# DeltaReduce Clinical Decision Support Prototype (Demo v1.0)
## Автономный пакет для развертывания на сервере (Standalone Server Deployment Package)

Этот каталог содержит **полностью автономную версию** клинического прототипа поддержки принятия врачебных решений (Demo v1.0), готовую к установке на любом сервере (Linux / Ubuntu / Debian, Docker или Windows Server).

---

### Архитектура и компоненты:
1. **Live NLP Модель (`deepseek-v4-flash`)**:
   - Работает через API Uni Lübeck (`https://llm-api.ai-lab.uni-luebeck.de/v1`).
   - Ключ и эндпоинт настраиваются в файле `.env`.
   - Включает отказоустойчивый парсер, лимит токенов (6144) против зацикливания и восстановление черновиков из `reasoning_content`.
2. **Нейросетевая модель фенотипического ранжирования (10-Gene Phenotype Classifier)**:
   - Замороженный artifact `model_10genes_phenotype_classifier.json`.
   - Чистый phenotype-to-gene ranking без генотипических бонусов.
3. **Детерминированное ядро Revision 6.2**:
   - Каталог транскриптов `CANONICAL_CATALOG`, нормализация HGVS, проверка зиготности/фазирования и выявление дискордантности.
4. **Формальный верификатор и шлюз полноты**:
   - `FormalGateValidator` и `ExtractionCompletenessGate`.
5. **Интерактивный веб-интерфейс врача**:
   - Динамическое подтверждение/отклонение симптомов врачом и моментальный перерасчет (`POST /api/recalculate`) без повторного вызова LLM.
6. **Safety v2 для фенотипического классификатора**:
   - Цепочка `classifier -> probability abstention -> support/OOD guard -> API response -> Web UI`.
   - Ranking классификатора не изменяется; safety-слой может только понизить `DEFINITIVE_GENE` до `AMBIGUOUS_GENE_CLUSTER`.
   - API возвращает `status` и `reason_codes`; UI показывает status, top candidate и classifier score.

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
Тест проверит все 5 сценариев, корректность загрузки замороженного phenotype classifier,
работу детерминированного ядра и API перерасчета.

Offline smoke без LLM/API-ключа:

```bash
python3 test_safety_v2_pipeline.py
```

Этот тест mock-ит Schema 1.1 extraction, прогоняет 5 packaged demo cases, проверяет `status`,
`reason_codes`, неизменность ranking после safety-слоя и fail-closed поведение support guard.

---

## ⚙️ Настройки в `.env`

Файл `.env` содержит:
```env
LLM_API_KEY=<SET_LOCALLY_DO_NOT_COMMIT>
LLM_BASE_URL=https://llm-api.ai-lab.uni-luebeck.de/v1
PORT=8005
HOST=0.0.0.0
```
Вы можете изменить порт (например, на `80` или `8080`) или указать другой ключ/эндпоинт при необходимости.

---

## Замороженные deployment artifacts

Рядом с моделью должны оставаться:

```text
model_10genes_phenotype_classifier.json
clinical_ontology_v1.json
input_schema_v1.json
safety_thresholds_v2.json
support_index_v2.json
compatibility_manifest_v2.json
```

`compatibility_manifest_v2.json` содержит SHA-256 для модели, ontology, input schema,
thresholds, support index, backend и UI-компонентов. При изменении deploy-кода или артефактов
запустите:

```bash
python3 freeze_safety_artifacts.py
```
