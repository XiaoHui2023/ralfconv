#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

rm -rf .venv build dist .ci-smoke

export DEBIAN_FRONTEND=noninteractive
sed -i \
  -e 's|http://archive.ubuntu.com/ubuntu|http://old-releases.ubuntu.com/ubuntu|g' \
  -e 's|http://security.ubuntu.com/ubuntu|http://old-releases.ubuntu.com/ubuntu|g' \
  /etc/apt/sources.list

apt-get update
apt-get install -y --no-install-recommends \
  bzip2 \
  ca-certificates \
  binutils \
  wget
update-ca-certificates

miniconda=/tmp/miniconda.sh
for attempt in 1 2 3; do
  if wget -q -O "$miniconda" \
    https://repo.anaconda.com/miniconda/Miniconda3-py310_23.5.2-0-Linux-x86_64.sh; then
    break
  fi
  if [[ "$attempt" == "3" ]]; then
    echo "failed to download Miniconda" >&2
    exit 1
  fi
  sleep 5
done

bash "$miniconda" -b -p /opt/conda
/opt/conda/bin/python -m venv .venv

export PACK_LINUX_SKIP_STATICX=1
bash tools/pack.sh src

mkdir -p .ci-smoke
chmod +x dist/ralfconv
dist/ralfconv -i example/demo_soc.ralf -o .ci-smoke/demo_soc_flat.json
dist/ralfconv --format hierarchical -i example/demo_soc.ralf -o .ci-smoke/demo_soc_hierarchical.json

.venv/bin/python - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

flat = json.loads(Path(".ci-smoke/demo_soc_flat.json").read_text(encoding="utf-8"))
if not any(item.get("path") == "demo_soc.CTRL" for item in flat):
    raise SystemExit("flat smoke output is missing demo_soc.CTRL")

hier = json.loads(Path(".ci-smoke/demo_soc_hierarchical.json").read_text(encoding="utf-8"))
if not hier or hier[0].get("name") != "demo_soc":
    raise SystemExit("hierarchical smoke output is missing demo_soc root")

archives = list(Path("dist").glob("ralfconv-*-linux.tar.gz"))
if not Path("dist/ralfconv").is_file() or not archives:
    raise SystemExit("release assets are incomplete")
PY
