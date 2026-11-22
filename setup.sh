#!/bin/sh
# Membuat .env dengan password dan API key acak. Tidak menimpa .env yang sudah ada.
set -e
if [ -f .env ]; then
  echo ".env sudah ada, tidak diubah."
  exit 0
fi
cat > .env <<ENV
POSTGRES_DB=jalurbelajar
POSTGRES_USER=jalurbelajar
POSTGRES_PASSWORD=$(openssl rand -hex 16)
API_KEY=$(openssl rand -hex 16)
JWT_SECRET=$(openssl rand -hex 32)
TUNNEL_TOKEN=
ENV
chmod 600 .env
echo ".env dibuat. API key kamu:"
grep '^API_KEY=' .env
