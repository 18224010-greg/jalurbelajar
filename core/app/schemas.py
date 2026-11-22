from datetime import datetime

from pydantic import BaseModel, Field


class ModuleOut(BaseModel):
    id: int
    topic: str
    level: str
    title: str
    description: str


class QuestionOut(BaseModel):
    id: int
    text: str
    options: list[str]


class QuizOut(BaseModel):
    id: int
    module_id: int
    title: str
    questions: list[QuestionOut]


class AnswerIn(BaseModel):
    question_id: int
    answer_index: int = Field(ge=0)


class SubmitIn(BaseModel):
    student_id: str | None = Field(
        None, min_length=1, max_length=64,
        description="Wajib untuk X-API-Key. Untuk pengguna login diisi otomatis dari token.",
    )
    answers: list[AnswerIn] = Field(min_length=1)


class QuestionResult(BaseModel):
    question_id: int
    correct: bool


class SubmitOut(BaseModel):
    attempt_id: int
    student_id: str
    quiz_id: int
    score: int
    total: int
    percentage: int
    passed: bool
    results: list[QuestionResult]


class AttemptOut(BaseModel):
    attempt_id: int
    module_id: int
    module_title: str
    score: int
    total: int
    percentage: int
    passed: bool
    created_at: datetime


class ProgressOut(BaseModel):
    student_id: str
    attempts: list[AttemptOut]
    completed_modules: list[int]
    average_percentage: int


class RecommendationOut(BaseModel):
    module: ModuleOut
    reason: str


_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    email: str = Field(max_length=120, pattern=_EMAIL)
    password: str = Field(min_length=6, max_length=72)


class LoginIn(BaseModel):
    email: str = Field(max_length=120)
    password: str = Field(max_length=72)


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    student_id: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
