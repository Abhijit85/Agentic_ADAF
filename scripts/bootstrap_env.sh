#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "${ROOT_DIR}"

if [[ ! -d "${VENV_DIR}" ]]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

python - <<'PY'
from pathlib import Path
required = [
    "OPENROUTER_API_KEY",
    "PRIMARY_MODEL_NAME",
    "DEALOG_SUMMARIZER_MODEL",
]
env_path = Path(".env")
if not env_path.exists():
    raise SystemExit("Missing .env in repo root.")

values = {}
for line in env_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    values[key.strip()] = value.strip()

missing = [key for key in required if not values.get(key)]
if missing and values.get("DEALOG_LLM_BACKEND", "").strip().lower() != "local":
    print("Configured .env still needs values for hosted inference:", ", ".join(missing))
else:
    print(".env sanity check passed.")
PY

python - <<'PY'
import importlib
modules = ["dotenv", "pandas", "torch", "transformers", "yaml", "requests"]
missing = []
for name in modules:
    try:
        importlib.import_module(name)
    except Exception as exc:
        missing.append(f"{name}: {exc}")
if missing:
    raise SystemExit("Import smoke check failed:\n" + "\n".join(missing))
print("Dependency import smoke check passed.")
PY

printf '\nBootstrap complete.\n'
printf 'Activate with: source .venv/bin/activate\n'
printf 'Smoke test with: python main.py --dataset crtqa --split dev --limit 1 --llm ${PRIMARY_MODEL_NAME}\n'
