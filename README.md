# JalurBelajar

Microservice backend JalurBelajar (Tugas Besar TST × PWAM, tema Education & Learning Tools).
Siswa mengikuti tes awal singkat, mendapat jalur belajar, mengerjakan kuis, dan menerima rekomendasi modul.

- Kelompok: PAWM TST Jaya (K02)
- URL publik: https://pawm-tst-jaya.stei.site/api
- Dokumentasi interaktif (Swagger): https://pawm-tst-jaya.stei.site/api/docs

## Arsitektur

```
Internet -> Cloudflare Tunnel -> gateway (Nginx, cek X-API-Key) -> core (FastAPI) -> db (PostgreSQL)
```

| Container | Fungsi | Batas sumber daya |
|---|---|---|
| gateway | Pintu masuk tunggal, memeriksa `X-API-Key` | 64 MB, 0.25 CPU |
| core | Logika JalurBelajar (FastAPI) | 256 MB, 0.5 CPU |
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

## Autentikasi

Semua endpoint kecuali `/api/health` dan `/api/docs` wajib header:

```
X-API-Key: <API key dari pemilik layanan>
```

Tanpa key yang benar, jawabannya `401`.

## Endpoint

Base URL: `https://pawm-tst-jaya.stei.site/api`

| Method | Path | Fungsi |
|---|---|---|
| GET | `/health` | Cek layanan hidup (tanpa key) |
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

Kontrak lengkap (OpenAPI) tersedia di `/api/openapi.json`.

## Catatan keamanan

- `.env` berisi rahasia dan tidak ikut GitHub (`.gitignore`).
- Port database tidak dipublikasikan.
- Layanan integrasi, frontend, dan aplikasi mobile tidak dijalankan di STB.
