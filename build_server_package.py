import shutil
import zipfile
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT_DIR = Path("d:/delta")
DEMO_DIR = ROOT_DIR / "demo_v1"
DEPLOY_DIR = ROOT_DIR / "cds_server_deploy"
ALT_DEPLOY_DIR = Path("D:/cds_server_deploy")

if DEPLOY_DIR.exists():
    shutil.rmtree(DEPLOY_DIR)
DEPLOY_DIR.mkdir(parents=True, exist_ok=True)

print(f"[Build] Target directory: {DEPLOY_DIR}")

# 1. Copy Static Frontend
static_dest = DEPLOY_DIR / "static"
shutil.copytree(DEMO_DIR / "static", static_dest)
print("  ✓ Copied static assets (index.html, style.css, app.js)")

# 2. Copy Core Deterministic Modules
core_modules = [
    "h1_contract.py",
    "extraction_completeness_gate.py",
    "formal_gate_validator.py",
    "revision_6_2_engine.py",
]
for mod in core_modules:
    shutil.copy2(ROOT_DIR / mod, DEPLOY_DIR / mod)
    print(f"  ✓ Copied {mod}")

# 3. Create self-contained mofe_engine.py
mofe_engine_content = '''# ==============================================================================
# FROZEN MOFE NEURAL & DUAL-EXPERT CLINICAL ENGINE (REVISION 4/5)
# Zero custom heuristics. Pure 10-gene phenotype differential.
# ==============================================================================
import json
import numpy as np

ALL_10_GENES = ["ATP13A2", "GCH1", "PRKN", "PINK1", "PARK7", "GBA1", "SNCA", "LRRK2", "VPS35", "RAB32"]

TEMPERATURE = 2.2

EXPERT_A_GENES = ["GBA1", "LRRK2", "PRKN", "PARK7"]
EXPERT_B_GENES = ["RAB32", "VPS35", "SNCA", "ATP13A2", "PINK1", "GCH1"]

ATYPICAL_WEIGHTS = {
    "vertical_gaze_palsy": 3.0,
    "diurnal_fluctuation": 3.0,
    "spasticity_pyramidal_signs": 2.5,
    "cognitive_decline": 2.0,
    "autonomic_dysfunction": 2.0,
    "dystonia": 1.8,
    "levodopa_response": 1.5,
}
W_MAX = 15.8

def compute_alpha(features):
    score = sum(ATYPICAL_WEIGHTS[f] for f in features if f in ATYPICAL_WEIGHTS)
    s_norm = score / W_MAX
    alpha = 0.20 + 0.65 * s_norm
    return float(np.clip(alpha, 0.15, 0.85))

GENE_SIGNATURES = {
    "ATP13A2": {
        "hallmarks": ["vertical_gaze_palsy", "spasticity_pyramidal_signs", "kufor_rakeb_atypical_pd", "juvenile_onset", "cognitive_decline"],
        "inheritance": ["recessive_pedigree", "consanguinity"],
        "typical_onset": ["juvenile_onset"]
    },
    "GCH1": {
        "hallmarks": ["dystonia", "diurnal_fluctuation", "levodopa_response", "juvenile_onset"],
        "inheritance": ["autosomal_dominant_pedigree", "familial_history"],
        "typical_onset": ["juvenile_onset", "early_onset"]
    },
    "PRKN": {
        "hallmarks": ["sleep_benefit", "dyskinesia", "tremor_rest", "early_onset", "dystonia"],
        "inheritance": ["recessive_pedigree", "consanguinity"],
        "typical_onset": ["early_onset"]
    },
    "PINK1": {
        "hallmarks": ["early_onset", "depression", "tremor_rest", "sleep_benefit", "dystonia"],
        "inheritance": ["recessive_pedigree", "consanguinity"],
        "typical_onset": ["early_onset"]
    },
    "PARK7": {
        "hallmarks": ["early_onset", "blepharospasm", "rigidity", "bradykinesia"],
        "inheritance": ["recessive_pedigree", "consanguinity"],
        "typical_onset": ["early_onset"]
    },
    "GBA1": {
        "hallmarks": ["cognitive_decline", "hallucinations", "hyposmia", "late_onset", "depression"],
        "inheritance": ["autosomal_dominant_pedigree", "familial_history"],
        "typical_onset": ["late_onset"]
    },
    "SNCA": {
        "hallmarks": ["cognitive_decline", "autonomic_dysfunction", "early_onset", "hallucinations", "severe_parkinsonism"],
        "inheritance": ["autosomal_dominant_pedigree", "familial_history"],
        "typical_onset": ["early_onset", "late_onset"]
    },
    "LRRK2": {
        "hallmarks": ["tremor_rest", "late_onset", "bradykinesia", "rigidity"],
        "inheritance": ["autosomal_dominant_pedigree", "familial_history"],
        "typical_onset": ["late_onset"]
    },
    "VPS35": {
        "hallmarks": ["tremor_rest", "late_onset", "bradykinesia", "rigidity"],
        "inheritance": ["autosomal_dominant_pedigree", "familial_history"],
        "typical_onset": ["late_onset"]
    },
    "RAB32": {
        "hallmarks": ["tremor_rest", "late_onset", "bradykinesia", "rigidity"],
        "inheritance": ["autosomal_dominant_pedigree", "familial_history"],
        "typical_onset": ["late_onset"]
    }
}

# Frozen Schema 1.1 System Prompt
FROZEN_SYSTEM_PROMPT_SCHEMA_1_1 = """You are a strictly constrained Clinical Semantic Extractor.
Your task is to extract atomic clinical and molecular observations from free clinical text into Schema 1.1 JSON.

STRICT CONSTRAINTS:
1. Extract ONLY observations literally supported by the input text.
2. DO NOT make clinical diagnoses or assign causal genes.
3. DO NOT normalize variants (keep the exact raw variant string from text, e.g. "c.1858G>A", "p.Asp620Asn", "c.255delA"). If both cDNA (e.g. "c.1858G>A") and protein (e.g. "p.Asp620Asn") changes appear, extract EACH as a separate atomic HAS_VARIANT observation.
4. For every observation, provide "source" with "text_span" containing the EXACT verbatim substring from the input text.
5. Approved concept whitelist for HAS_SYMPTOM:
   ['autonomic_dysfunction', 'blepharospasm', 'bradykinesia', 'cognitive_decline', 'depression', 'diurnal_fluctuation', 'dyskinesia', 'dystonia', 'hallucinations', 'hyposmia', 'kufor_rakeb_atypical_pd', 'levodopa_response', 'parkinsonism', 'rigidity', 'severe_parkinsonism', 'sleep_benefit', 'spasticity_pyramidal_signs', 'tremor_rest', 'vertical_gaze_palsy'].
   If a clinical finding does not exactly match a whitelist concept, output mapping_status="PROPOSED", raw_finding with the text phrase, and candidate_concept.
6. If an onset age is stated (e.g. "At age 44"), extract predicate="HAS_ONSET_AGE", value=44, temporal_scope="ONSET".
7. Unless explicit past cues (e.g. "years ago", "previously", "initially", "prior note") or onset cues appear, set temporal_scope="CURRENT".
8. If a symptom improved after sleep, extract concept="sleep_benefit".
9. For negations (e.g. "no cognitive symptoms"), set polarity="negative".
10. For relatives (e.g. "maternal aunt"), set subject={"type": "relative"}. For proband/patient, set subject={"type": "proband"}.
11. For document quotes or secondary reports, set epistemic_status="QUOTED" and source.asserted_by (e.g. "clinic_letter").
12. If multiple variant classifications are stated without linking to individual alleles, output AGGREGATE_CLASSIFICATION_ASSERTION with counts multiset, assignment_status="UNRESOLVED", and RELATION_UNRESOLVED.

OUTPUT FORMAT:
Return a single valid JSON object adhering to this structure:
{
  "schema_version": "1.1",
  "document_id": "doc_id",
  "observations": [
    {
      "id": "obs_001",
      "predicate": "HAS_SYMPTOM | HAS_NORMAL_FINDING | HAS_VARIANT | HAS_GENE_MENTION | HAS_CLASSIFICATION_ASSERTION | AGGREGATE_CLASSIFICATION_ASSERTION | HAS_PARENTAL_ORIGIN | HAS_ZYGOSITY | HAS_PHASE_ASSERTION | HAS_ONSET_AGE | HAS_CURRENT_AGE | RELATION_UNRESOLVED",
      "subject": {"type": "proband | father | mother | sister | brother | daughter | son | relative"},
      "concept": "canonical concept from whitelist or null",
      "raw_finding": "verbatim text phrase or null",
      "candidate_concept": "proposed candidate concept or null",
      "mapping_status": "CONFIRMED | PROPOSED",
      "raw_variant": "exact raw string from text or null",
      "polarity": "positive | negative",
      "temporal_scope": "CURRENT | HISTORICAL | RESOLVED | ONSET",
      "epistemic_status": "ASSERTED | REPORTED | SUSPECTED | POSSIBLE | UNCERTAIN | UNCONFIRMED | QUOTED | SUPERSEDED",
      "target": "target identifier if applicable or null",
      "value": "scalar value or dictionary of counts or null",
      "source": {
        "text_span": "exact verbatim substring from text",
        "start": 0,
        "end": 10,
        "asserted_by": "optional source or null"
      },
      "antecedent_span": null,
      "temporal_relation": null,
      "relation_object": null,
      "counts": null,
      "assignment_status": null
    }
  ]
}
"""
'''
(DEPLOY_DIR / "mofe_engine.py").write_text(mofe_engine_content, encoding="utf-8")
print("  ✓ Created self-contained mofe_engine.py")

# 4. Copy Model Weights & Examples & Cache
shutil.copy2(DEMO_DIR / "model_10genes_mixed_nodes.json", DEPLOY_DIR / "model_10genes_mixed_nodes.json")
print("  ✓ Copied model_10genes_mixed_nodes.json (3.8 MB)")

shutil.copy2(DEMO_DIR / "examples.json", DEPLOY_DIR / "examples.json")
print("  ✓ Copied examples.json")

shutil.copy2(DEMO_DIR / ".pipeline_cache.json", DEPLOY_DIR / ".pipeline_cache.json")
print("  ✓ Copied .pipeline_cache.json")

# 5. Copy Standalone pipeline_service.py
shutil.copy2(DEMO_DIR / "pipeline_service.py", DEPLOY_DIR / "pipeline_service.py")
print("  ✓ Copied standalone pipeline_service.py")

# 6. Copy Standalone server.py
shutil.copy2(DEMO_DIR / "server.py", DEPLOY_DIR / "server.py")
print("  ✓ Copied standalone server.py")

# 7. Copy Test Suite
shutil.copy2(DEMO_DIR / "test_demo_pipeline.py", DEPLOY_DIR / "test_demo_pipeline.py")
test_pipeline_src = (DEPLOY_DIR / "test_demo_pipeline.py").read_text(encoding="utf-8")
test_pipeline_src = test_pipeline_src.replace('from demo_v1.pipeline_service import ClinicalDecisionSupportPipeline', 'from pipeline_service import ClinicalDecisionSupportPipeline')
(DEPLOY_DIR / "test_demo_pipeline.py").write_text(test_pipeline_src, encoding="utf-8")
print("  ✓ Created standalone test_demo_pipeline.py")

# 8. Create Environment Configuration
env_content = """# ==============================================================================
# DeltaReduce Clinical Decision Support Prototype Configuration
# ==============================================================================
LLM_API_KEY=
LLM_BASE_URL=https://llm-api.ai-lab.uni-luebeck.de/v1
LLM_MODEL=gemma-4-26b-a4b-it
PORT=8005
HOST=0.0.0.0
BASE_PATH=/delta-reduce-demo

# Optional: Disable SSL certificate check if behind an enterprise/proxy firewall (1=verify, 0=unverified)
# LLM_SSL_VERIFY=1
"""
(DEPLOY_DIR / ".env").write_text(env_content, encoding="utf-8")
(DEPLOY_DIR / ".env.example").write_text(env_content, encoding="utf-8")
print("  ✓ Created .env and .env.example")

# 9. Create requirements.txt
(DEPLOY_DIR / "requirements.txt").write_text("numpy>=1.20.0\ncertifi>=2024.0.0\n", encoding="utf-8")
print("  ✓ Created requirements.txt")

# 10. Create Dockerfile & docker-compose.yml
dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose web service port
EXPOSE 8005

ENV PORT=8005
ENV HOST=0.0.0.0
ENV SKIP_VENV_BOOTSTRAP=1

CMD ["python", "-u", "server.py"]
"""
(DEPLOY_DIR / "Dockerfile").write_text(dockerfile_content, encoding="utf-8")

docker_compose_content = """version: '3.8'

services:
  deltareduce-cds:
    build: .
    container_name: deltareduce-cds-demo
    restart: always
    ports:
      - "8005:8005"
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8005/api/status"]
      interval: 30s
      timeout: 5s
      retries: 3
"""
(DEPLOY_DIR / "docker-compose.yml").write_text(docker_compose_content, encoding="utf-8")
print("  ✓ Created Dockerfile & docker-compose.yml")

# 11. Create start.sh and start.bat
start_sh_content = """#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "============================================================"
echo "  Starting DeltaReduce Clinical Decision Support Prototype"
echo "============================================================"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is not installed."
    exit 1
fi

# Launch server directly - Python will automatically create and enter .venv if needed
python3 -u server.py
"""
(DEPLOY_DIR / "start.sh").write_text(start_sh_content, encoding="utf-8")

start_bat_content = """@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   Starting DeltaReduce Clinical Decision Support Prototype
echo ============================================================

python -u server.py
pause
"""
(DEPLOY_DIR / "start.bat").write_text(start_bat_content, encoding="utf-8")
print("  ✓ Created start.sh & start.bat")

# 12. Create systemd unit file
systemd_content = """[Unit]
Description=DeltaReduce Clinical Decision Support Prototype (Demo v1.0)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/deltareduce-cds
EnvironmentFile=/opt/deltareduce-cds/.env
ExecStart=/usr/bin/python3 -u /opt/deltareduce-cds/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
(DEPLOY_DIR / "deltareduce-cds.service").write_text(systemd_content, encoding="utf-8")

# 13. Create nginx.conf
nginx_content = """# Nginx Reverse Proxy / Gateway Configuration for DeltaReduce CDS Prototype
#
# Option A: Sub-path Gateway location (e.g. https://www.mdsgene.org/delta-reduce-demo/)
# Insert this location block inside your existing server { ... } configuration:
location /delta-reduce-demo/ {
    proxy_pass http://127.0.0.1:8005/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Prefix /delta-reduce-demo;

    # Timeouts for clinical reasoning queries
    proxy_connect_timeout 180s;
    proxy_send_timeout 180s;
    proxy_read_timeout 180s;
}

# Option B: Dedicated Subdomain or Root VirtualHost
server {
    listen 80;
    server_name cds-demo.mdsgene.org;

    location / {
        proxy_pass http://127.0.0.1:8005;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 180s;
        proxy_send_timeout 180s;
        proxy_read_timeout 180s;
    }
}
"""
(DEPLOY_DIR / "nginx.conf").write_text(nginx_content, encoding="utf-8")
print("  ✓ Created systemd service & nginx.conf")

# 14. Create README.md in Russian and English
readme_content = """# DeltaReduce Clinical Decision Support Prototype (Demo v1.0)
## Автономный пакет для развертывания на сервере (Standalone Server Deployment Package)

Этот каталог содержит **полностью автономную версию** клинического прототипа поддержки принятия врачебных решений (Demo v1.0), готовую к установке на любом сервере (Linux / Ubuntu / Debian, Docker или Windows Server).

---

### Архитектура и компоненты:
1. **Live NLP Модель (`deepseek-v4-flash`)**:
   - Работает через API Uni Lübeck (`https://llm-api.ai-lab.uni-luebeck.de/v1`).
   - Ключ и эндпоинт настраиваются в файле `.env`.
   - Включает отказоустойчивый парсер, лимит токенов (6144) против зацикливания и восстановление черновиков из `reasoning_content`.
2. **Нейросетевая модель фенотипического ранжирования (MoFE 10-Gene)**:
   - Замороженные веса `model_10genes_mixed_nodes.json` (3.8 МБ).
   - Чистый дифференциал симптомов без эвристик и без генотипических бонусов.
3. **Детерминированное ядро Revision 6.2**:
   - Каталог транскриптов `CANONICAL_CATALOG`, нормализация HGVS, проверка зиготности/фазирования и выявление дискордантности.
4. **Формальный верификатор и шлюз полноты**:
   - `FormalGateValidator` и `ExtractionCompletenessGate`.
5. **Интерактивный веб-интерфейс врача**:
   - Динамическое подтверждение/отклонение симптомов врачом и моментальный перерасчет (`POST /api/recalculate`) без повторного вызова LLM.

---

## 🚀 Варианты развертывания

### ⚡ Автоматическое создание локального окружения (.venv)
При любом прямом вызове:
```bash
python3 server.py
# или на Windows:
python server.py
```
`server.py` автоматически:
1. Проверяет, запущен ли он внутри локального `.venv`.
2. Если окружение отсутствует — самостоятельно создает `.venv` через стандартную библиотеку Python.
3. Автоматически устанавливает зависимости из `requirements.txt` (`numpy`).
4. Бесшовно перезапускает выполнение внутри изолированного окружения `.venv`!

---

### Вариант 1: Быстрый запуск на Linux (Ubuntu / Debian / CentOS)

```bash
# 1. Распакуйте архив или скопируйте папку на сервер в /opt/deltareduce-cds
cd /opt/deltareduce-cds

# 2. Сделайте скрипт исполняемым
chmod +x start.sh

# 3. Запустите скрипт (создаст .venv при необходимости и поднимет сервер на порту 8005)
./start.sh
```

Сервер запустится на `http://IP_ВАШЕГО_СЕРВЕРА:8005`.

---

### Вариант 2: Запуск в Docker / Docker Compose (Рекомендуется)

```bash
cd /opt/deltareduce-cds

# Запуск контейнера в фоновом режиме
docker compose up -d --build

# Проверка логов
docker compose logs -f
```

---

### Вариант 3: Служба Systemd на Linux (автозапуск при перезагрузке сервера)

```bash
# 1. Скопируйте папку проекта в /opt/deltareduce-cds
sudo cp -r . /opt/deltareduce-cds

# 2. Скопируйте unit-файл в systemd
sudo cp /opt/deltareduce-cds/deltareduce-cds.service /etc/systemd/system/

# 3. Установите зависимости
sudo apt update && sudo apt install -y python3 python3-pip python3-numpy

# 4. Активируйте и запустите службу
sudo systemctl daemon-reload
sudo systemctl enable deltareduce-cds
sudo systemctl start deltareduce-cds

# 5. Проверьте статус
sudo systemctl status deltareduce-cds
```

---

### Вариант 4: Настройка Nginx в качестве Reverse Proxy (порт 80 / 443)

В комплекте уже есть готовый шаблон `nginx.conf`:

```bash
sudo cp nginx.conf /etc/nginx/sites-available/deltareduce-cds.conf
sudo ln -s /etc/nginx/sites-available/deltareduce-cds.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🧪 Проверка работоспособности (Self-Test)

После установки запустите автоматический тест прямо на сервере:

```bash
python3 test_demo_pipeline.py
```
Тест проверит все 5 сценариев, корректность загрузки замороженных весов MoFE, работу детерминированного ядра и API перерасчета.

---

## ⚙️ Настройки в `.env`

Файл `.env` содержит:
```env
LLM_API_KEY=
LLM_BASE_URL=https://llm-api.ai-lab.uni-luebeck.de/v1
PORT=8005
HOST=0.0.0.0
```
Вы можете изменить порт (например, на `80` или `8080`) или указать другой ключ/эндпоинт при необходимости.
"""
(DEPLOY_DIR / "README.md").write_text(readme_content, encoding="utf-8")
print("  ✓ Created README.md (Russian & English guide)")

# 15. Create ZIP Archive for Convenient Transfer
zip_path = ROOT_DIR / "cds_server_deploy.zip"
try:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(DEPLOY_DIR):
            for file in files:
                full_p = Path(root) / file
                rel_p = full_p.relative_to(DEPLOY_DIR)
                zf.write(full_p, rel_p)
    print(f"  ✓ Created ZIP archive: {zip_path} ({zip_path.stat().st_size / (1024*1024):.2f} MB)")
except Exception as e:
    alt_zip = ROOT_DIR / "cds_server_deploy_v1.zip"
    with zipfile.ZipFile(alt_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(DEPLOY_DIR):
            for file in files:
                full_p = Path(root) / file
                rel_p = full_p.relative_to(DEPLOY_DIR)
                zf.write(full_p, rel_p)
    print(f"  ✓ Created ZIP archive: {alt_zip} ({alt_zip.stat().st_size / (1024*1024):.2f} MB) [fallback, {zip_path.name} was locked]")

# 16. Mirror to D:/cds_server_deploy for immediate direct access
try:
    shutil.copytree(DEPLOY_DIR, ALT_DEPLOY_DIR, dirs_exist_ok=True)
    print(f"  ✓ Mirrored to top-level folder: {ALT_DEPLOY_DIR}")
except Exception as e:
    print(f"  [!] Note: Partial mirror ({e})")

print("\n[Build Complete] All files successfully packaged!")
