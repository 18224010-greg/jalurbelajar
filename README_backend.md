# JalurBelajar

Microservice backend JalurBelajar (Tugas Besar TST × PWAM, tema Education & Learning Tools).
Siswa memilih topik, mengerjakan kuis per modul, dan menerima rekomendasi modul berikutnya berdasarkan hasil kuis.

- Kelompok: PAWM TST Jaya (K02)
- URL publik: https://pawm-tst-jaya.stei.site/api
- Dokumentasi interaktif (Swagger): https://pawm-tst-jaya.stei.site/api/docs
- Repositori aplikasi mobile (klien layanan ini): https://github.com/18224010-greg/jalurbelajar-app

## Arsitektur

```
Internet -> Cloudflare Tunnel -> gateway (Nginx) -> core (FastAPI: API key / JWT) -> db (PostgreSQL)
```

| Container | Fungsi | Batas sumber daya |
|---|---|---|
| gateway | Pintu masuk tunggal, menandai `X-API-Key` yang valid | 64 MB, 0.25 CPU |
| core | Logika JalurBelajar dan autentikasi (FastAPI) | 256 MB, 0.5 CPU |
| db | PostgreSQL, tidak dibuka ke luar | 256 MB, 0.5 CPU |
| tunnel | Cloudflare Tunnel (profil `tunnel`) | 128 MB, 0.25 CPU |

Semua container memakai `restart: unless-stopped`. Data di database adalah data uji.

## Menjalankan (di STB atau komputer apa pun yang punya Docker)

```
sh setup.sh                 # membuat .env berisi password dan API key acak
docker compose up -d --build
curl http://localhost/api/health
```

Tunnel ke internet (setelah `TUNNEL_TOKEN` diisi di `.env`):

```
docker compose --profile tunnel up -d
```

## Cara mendapat akses

1. Cari entri `pawm-tst-jaya` di API Registry kelas (spreadsheet bersama) untuk URL dan dokumentasinya.
2. Minta **API key** ke kelompok PAWM TST Jaya (K02) lewat kontak anggota yang tercantum di API Registry atau grup kelas. API key tidak dicantumkan di dokumen ini.
3. Sertakan header `X-API-Key: <API key>` pada setiap permintaan (kecuali `/api/health`, `/api/docs`, `/api/auth/register`, dan `/api/auth/login`).
4. Tanpa key atau dengan key yang salah, layanan menjawab `401 Unauthorized`.

Pengguna aplikasi tidak memakai API key. Mereka mendaftar lewat `POST /api/auth/register`, masuk lewat `POST /api/auth/login`, lalu mengirim `Authorization: Bearer <token>` (JWT, berlaku 7 hari). Pengguna login hanya dapat mengakses data miliknya sendiri; `student_id` diisi otomatis dari token (atau gunakan `me`).

Untuk menguji di Postman atau REST Client: impor kontrak OpenAPI dari `https://pawm-tst-jaya.stei.site/api/openapi.json`, atau buka Swagger di `/api/docs`.

## Endpoint

Base URL: `https://pawm-tst-jaya.stei.site/api`

| Method | Path | Fungsi |
|---|---|---|
| GET | `/health` | Cek layanan hidup (tanpa key) |
| POST | `/auth/register` | Daftar akun pengguna (tanpa key) |
| POST | `/auth/login` | Masuk, menerima token JWT (tanpa key) |
| GET | `/auth/me` | Profil pengguna yang sedang login (Bearer) |
| GET | `/modules?topic=&level=` | Daftar modul. `level`: pemula, menengah, lanjut |
| GET | `/modules/{id}/quiz` | Kuis sebuah modul (tanpa kunci jawaban) |
| POST | `/quizzes/{id}/submit` | Kirim jawaban, terima skor |
| GET | `/recommendations?topic=&student_id=` | Modul yang disarankan berikutnya |
| GET | `/students/{id}/progress` | Riwayat kuis dan modul tuntas (lulus = skor 70% ke atas) |

Contoh:

```
curl -H "X-API-Key: KUNCI" "https://pawm-tst-jaya.stei.site/api/modules?topic=python"

curl -X POST -H "X-API-Key: KUNCI" -H "Content-Type: application/json" \
  -d '{"student_id":"siswa-1","answers":[{"question_id":1,"answer_index":1},{"question_id":2,"answer_index":0},{"question_id":3,"answer_index":2}]}' \
  https://pawm-tst-jaya.stei.site/api/quizzes/1/submit
```

Contoh jawaban `GET /api/modules?topic=python`:

```
[{"id":1,"topic":"python","level":"pemula","title":"Variabel dan Tipe Data",
  "description":"Menyimpan nilai dalam variabel dan mengenal int, float, str, bool."}, ...]
```

Contoh jawaban `POST /api/quizzes/1/submit`:

```
{"attempt_id":1,"student_id":"siswa-1","quiz_id":1,"score":3,"total":3,
 "percentage":100,"passed":true,
 "results":[{"question_id":1,"correct":true}, ...]}
```

Kode status: `200` berhasil, `201` akun dibuat, `401` API key atau token salah atau tidak ada,
`403` pengguna login mengakses data milik orang lain, `404` data tidak ditemukan,
`409` email sudah terdaftar, `422` parameter atau isi permintaan tidak valid.

Kontrak lengkap (OpenAPI) tersedia di `/api/openapi.json`.

## Aturan penilaian kuis

Satu kuis memiliki beberapa pertanyaan pilihan ganda. Skor adalah jumlah jawaban benar.
Siswa dinyatakan lulus modul bila persentase 70% ke atas. Rekomendasi menampilkan modul belum tuntas
pada level terendah yang masih tersisa dalam topik yang diminta (pemula, menengah, lanjut).

## Catatan keamanan

- `.env` berisi rahasia dan tidak ikut GitHub (`.gitignore`).
- Port database tidak dipublikasikan.
- Layanan integrasi, frontend, dan aplikasi mobile tidak dijalankan di STB.
