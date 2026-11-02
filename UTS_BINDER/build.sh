#!/usr/bin/env bash
# Build the binder PDF. gen.py makes (and checks) all K-maps, tables, derivations and SVGs.
# Two print passes: pass 1 finds page numbers, pass 2 fills them in.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH=/projects/sandbox/.pylib
CHROME=$(find /root/.cache/puppeteer/chrome -name chrome -type f -path "*chrome-linux64*" | head -1)
mkdir -p dist gen svg /projects/sandbox/.build/home
python3 gen.py
rm -f dist/pages.json
for pass in 1 2; do
  node build.js
  HOME=/projects/sandbox/.build/home timeout 120 "$CHROME" --headless=new --no-sandbox --disable-gpu --no-zygote \
    --disable-crash-reporter --disable-dev-shm-usage --user-data-dir=/projects/sandbox/.build/profile \
    --no-pdf-header-footer --virtual-time-budget=5000 \
    --print-to-pdf=dist/raw.pdf "file://$PWD/dist/binder.html" 2>/dev/null
  python3 stamp.py dist/raw.pdf "DigSys_UTS_Binder.pdf"
done
rm -f dist/raw.pdf
