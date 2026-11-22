"""Data uji (bukan data nyata). Dimuat sekali saat tabel masih kosong."""
from sqlalchemy.orm import Session

from .models import Module, Question, Quiz

# (topic, level, judul, deskripsi, [(pertanyaan, [opsi], index_jawaban), ...])
DATA = [
    ("python", "pemula", "Variabel dan Tipe Data",
     "Menyimpan nilai dalam variabel dan mengenal int, float, str, bool.",
     [("Tipe data dari nilai 3.14 adalah?", ["int", "float", "str", "bool"], 1),
      ("Perintah untuk menampilkan teks ke layar?", ["print()", "show()", "echo()", "out()"], 0),
      ("Hasil dari type(True) adalah?", ["int", "str", "bool", "float"], 2)]),
    ("python", "pemula", "Percabangan dan Perulangan",
     "Mengatur alur program dengan if/else, for, dan while.",
     [("Kata kunci untuk perulangan dengan jumlah tertentu?", ["for", "if", "def", "try"], 0),
      ("Blok yang dijalankan jika kondisi if salah?", ["elif", "else", "then", "case"], 1),
      ("range(3) menghasilkan?", ["1,2,3", "0,1,2", "0,1,2,3", "3"], 1)]),
    ("python", "menengah", "Fungsi dan Modul",
     "Membuat fungsi dengan def dan mengimpor modul.",
     [("Kata kunci untuk membuat fungsi?", ["func", "def", "fn", "lambda"], 1),
      ("Kata kunci untuk mengembalikan nilai fungsi?", ["give", "yield", "return", "out"], 2),
      ("Cara mengimpor modul math?", ["use math", "import math", "include math", "load math"], 1)]),
    ("matematika", "pemula", "Bilangan dan Operasi Hitung",
     "Operasi dasar pada bilangan bulat dan pecahan.",
     [("Hasil 7 + 8 x 2 adalah?", ["30", "23", "22", "16"], 1),
      ("Hasil 1/2 + 1/4 adalah?", ["2/6", "3/4", "1/6", "2/4"], 1),
      ("Bilangan prima terkecil adalah?", ["0", "1", "2", "3"], 2)]),
    ("matematika", "menengah", "Aljabar Dasar",
     "Menyelesaikan persamaan linear satu variabel.",
     [("Jika 2x + 3 = 11, maka x = ?", ["3", "4", "5", "7"], 1),
      ("Bentuk sederhana 3a + 2a adalah?", ["5a", "6a", "5a2", "a5"], 0),
      ("Jika x - 4 = 10, maka x = ?", ["6", "14", "40", "-6"], 1)]),
    ("bahasa-inggris", "pemula", "Simple Present Tense",
     "Kalimat untuk kebiasaan dan fakta umum.",
     [("She ___ to school every day.", ["go", "goes", "going", "gone"], 1),
      ("They ___ football on Sundays.", ["plays", "play", "playing", "played"], 1),
      ("Bentuk negatif: He ___ like coffee.", ["don't", "doesn't", "isn't", "not"], 1)]),
]


def seed_if_empty(db: Session) -> None:
    if db.query(Module).first():
        return
    for pos, (topic, level, title, desc, questions) in enumerate(DATA, start=1):
        module = Module(topic=topic, level=level, title=title, description=desc, position=pos)
        quiz = Quiz(module=module)
        for text, options, answer in questions:
            quiz.questions.append(Question(text=text, options=options, answer_index=answer))
        db.add_all([module, quiz])
    db.commit()
