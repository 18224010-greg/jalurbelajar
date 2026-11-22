import os
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import APIKeyHeader
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, selectinload

from . import models, schemas
from .db import Base, SessionLocal, engine, get_db
from .seed import seed_if_empty

PASS_PERCENTAGE = 70


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Database mungkin belum siap tepat saat container core menyala: coba ulang.
    for attempt in range(30):
        try:
            Base.metadata.create_all(engine)
            break
        except OperationalError:
            if attempt == 29:
                raise
            time.sleep(2)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


# Pemeriksaan API key sebenarnya dilakukan gateway (Nginx).
# Skema ini hanya agar tombol "Authorize" muncul di dokumentasi /docs.
_api_key_doc = APIKeyHeader(name="X-API-Key", auto_error=False)

app = FastAPI(
    title="JalurBelajar API",
    version="1.0.0",
    description=(
        "Layanan inti JalurBelajar: modul belajar, kuis, rekomendasi, dan progres siswa. "
        "Semua endpoint (kecuali /health dan /docs) memerlukan header `X-API-Key`. "
        "Data di sini adalah data uji."
    ),
    root_path=os.getenv("ROOT_PATH", ""),
    lifespan=lifespan,
    dependencies=[Depends(_api_key_doc)],
)


def _percentage(score: int, total: int) -> int:
    return round(score * 100 / total) if total else 0


def _module_out(m: models.Module) -> schemas.ModuleOut:
    return schemas.ModuleOut(
        id=m.id, topic=m.topic, level=m.level, title=m.title, description=m.description
    )


@app.get("/health", tags=["Sistem"], dependencies=[])
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "service": "jalurbelajar-core"}


@app.get("/modules", response_model=list[schemas.ModuleOut], tags=["Modul"])
def list_modules(
    topic: str | None = Query(None, description="Contoh: python, matematika"),
    level: str | None = Query(None, description="pemula | menengah | lanjut"),
    db: Session = Depends(get_db),
):
    if level is not None and level not in models.LEVELS:
        raise HTTPException(422, f"level harus salah satu dari {models.LEVELS}")
    stmt = select(models.Module).order_by(models.Module.position)
    if topic:
        stmt = stmt.where(models.Module.topic == topic)
    if level:
        stmt = stmt.where(models.Module.level == level)
    return [_module_out(m) for m in db.scalars(stmt)]


@app.get("/modules/{module_id}/quiz", response_model=schemas.QuizOut, tags=["Kuis"])
def get_quiz(module_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(models.Quiz)
        .where(models.Quiz.module_id == module_id)
        .options(selectinload(models.Quiz.questions), selectinload(models.Quiz.module))
    )
    quiz = db.scalars(stmt).first()
    if quiz is None:
        raise HTTPException(404, "Kuis untuk modul ini tidak ditemukan")
    return schemas.QuizOut(
        id=quiz.id,
        module_id=quiz.module_id,
        title=quiz.module.title,
        questions=[
            schemas.QuestionOut(id=q.id, text=q.text, options=q.options)
            for q in quiz.questions
        ],
    )


@app.post("/quizzes/{quiz_id}/submit", response_model=schemas.SubmitOut, tags=["Kuis"])
def submit_quiz(quiz_id: int, body: schemas.SubmitIn, db: Session = Depends(get_db)):
    quiz = db.scalars(
        select(models.Quiz)
        .where(models.Quiz.id == quiz_id)
        .options(selectinload(models.Quiz.questions))
    ).first()
    if quiz is None:
        raise HTTPException(404, "Kuis tidak ditemukan")

    key = {q.id: q.answer_index for q in quiz.questions}
    given = {a.question_id: a.answer_index for a in body.answers}
    unknown = set(given) - set(key)
    if unknown:
        raise HTTPException(422, f"question_id bukan bagian kuis ini: {sorted(unknown)}")

    results = [
        schemas.QuestionResult(question_id=qid, correct=given.get(qid) == ans)
        for qid, ans in key.items()
    ]
    score = sum(r.correct for r in results)
    total = len(key)
    attempt = models.Attempt(
        student_id=body.student_id, quiz_id=quiz.id, score=score, total=total
    )
    db.add(attempt)
    db.commit()
    pct = _percentage(score, total)
    return schemas.SubmitOut(
        attempt_id=attempt.id,
        student_id=body.student_id,
        quiz_id=quiz.id,
        score=score,
        total=total,
        percentage=pct,
        passed=pct >= PASS_PERCENTAGE,
        results=results,
    )


def _attempts(db: Session, student_id: str):
    stmt = (
        select(models.Attempt, models.Module)
        .join(models.Quiz, models.Quiz.id == models.Attempt.quiz_id)
        .join(models.Module, models.Module.id == models.Quiz.module_id)
        .where(models.Attempt.student_id == student_id)
        .order_by(models.Attempt.created_at, models.Attempt.id)
    )
    return db.execute(stmt).all()


@app.get(
    "/students/{student_id}/progress",
    response_model=schemas.ProgressOut,
    tags=["Progres"],
)
def student_progress(student_id: str, db: Session = Depends(get_db)):
    rows = _attempts(db, student_id)
    attempts = [
        schemas.AttemptOut(
            attempt_id=a.id,
            module_id=m.id,
            module_title=m.title,
            score=a.score,
            total=a.total,
            percentage=_percentage(a.score, a.total),
            passed=_percentage(a.score, a.total) >= PASS_PERCENTAGE,
            created_at=a.created_at,
        )
        for a, m in rows
    ]
    completed = sorted({x.module_id for x in attempts if x.passed})
    avg = round(sum(x.percentage for x in attempts) / len(attempts)) if attempts else 0
    return schemas.ProgressOut(
        student_id=student_id,
        attempts=attempts,
        completed_modules=completed,
        average_percentage=avg,
    )


@app.get(
    "/recommendations",
    response_model=list[schemas.RecommendationOut],
    tags=["Rekomendasi"],
)
def recommendations(
    topic: str = Query(..., description="Topik yang ingin dipelajari"),
    student_id: str | None = Query(None, description="Jika kosong, mulai dari level pemula"),
    db: Session = Depends(get_db),
):
    modules = list(
        db.scalars(
            select(models.Module)
            .where(models.Module.topic == topic)
            .order_by(models.Module.position)
        )
    )
    if not modules:
        raise HTTPException(404, "Topik tidak ditemukan")

    best: dict[int, int] = {}
    if student_id:
        for a, m in _attempts(db, student_id):
            best[m.id] = max(best.get(m.id, 0), _percentage(a.score, a.total))

    # Rekomendasikan modul belum tuntas pada level terendah yang masih ada sisanya.
    for level in models.LEVELS:
        pending = [
            m for m in modules
            if m.level == level and best.get(m.id, -1) < PASS_PERCENTAGE
        ]
        if pending:
            return [
                schemas.RecommendationOut(
                    module=_module_out(m),
                    reason=(
                        f"Skor terbaikmu {best[m.id]}%, ulangi sampai {PASS_PERCENTAGE}%"
                        if m.id in best
                        else f"Belum dicoba, cocok untuk level {level}"
                    ),
                )
                for m in pending
            ]
    return []  # semua modul pada topik ini sudah tuntas
