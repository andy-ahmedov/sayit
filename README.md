# pdf-tts-ru

Локальный пайплайн для озвучки русскоязычных документов в аудиофайлы `wav`, `mp3`, `m4a`.

Лучше всего проект поддерживает "чистые" born-digital PDF, где текст уже есть внутри документа. Также поддерживаются входные файлы `.docx`, `.md`, `.txt`. Основной путь извлечения PDF идет через PyMuPDF, основной TTS-движок по умолчанию это Silero, дополнительный локальный вариант это Piper.

## Что уже умеет

- извлекать текст из PDF без OCR;
- принимать на вход `.pdf`, `.docx`, `.md`, `.txt`;
- инспектировать документ и показывать количество страниц и таблиц;
- выбирать страницы в формате `all`, `1`, `1-5`, `1,3-5,8`;
- собирать аудио в режимах `per-page`, `per-range`, `merged`;
- экспортировать в `wav`, `mp3`, `m4a`;
- обрабатывать таблицы в режимах `skip`, `inline`, `separate`;
- озвучивать через `piper` или `silero`;
- настраивать запуск через CLI или `config.toml`.

## CLI

Минимальные команды:

```bash
python -m pdf_tts_ru.cli inspect --input file.pdf
python -m pdf_tts_ru.cli synth --input file.pdf --pages 1-5 --config config.toml
```

Приоритет параметров такой:

```text
CLI > config.toml > встроенные defaults
```

## Поддерживаемые Входы

- `.pdf`: основной и лучше всего поддерживаемый формат;
- `.docx`: поддерживается как логический документ; страницы считаются только по явным manual page breaks;
- `.md`: озвучивается как обычный текст, markdown-разметка перед синтезом очищается;
- `.txt`: озвучивается как обычный текст; поддерживаются `utf-8`, `utf-8-sig`, `cp1251`;
- `.doc`: прямой вход не поддерживается, сначала нужно конвертировать в `.docx`.

Для `.md` и `.txt` документ считается одностраничным:

- используйте `--pages all` или `--pages 1`;
- любые другие страницы дадут ошибку out-of-bounds.
- стартовое `Страница 1` не озвучивается, даже если включен `--announce-page-numbers`.

Для `.doc` можно использовать, например:

```bash
pandoc file.doc -o file.docx
libreoffice --headless --convert-to docx --outdir . file.doc
```

## Установка

Базовая установка проекта:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[dev]'
```

`ffmpeg` должен быть установлен в системе и доступен как `ffmpeg`, либо его путь нужно указать через `ffmpeg_bin` в конфиге.

## Системные Требования

Короткий ответ:

- если у вас обычный современный 64-bit ноутбук или ПК без дискретной видеокарты, проект обычно запустится и на `Silero`, и на `Piper`;
- `Silero` является дефолтным движком и нормально работает в CPU-only режиме, но на слабом железе длинные документы будут обрабатываться заметно дольше;
- `Piper` обычно проще использовать на слабых CPU, особенно с голосами уровня `x_low`, `low` или `medium`;
- GPU не обязателен ни для проекта в целом, ни для стандартного сценария запуска, но может ускорять `Silero`, а для `Piper` GPU-путь является отдельным и необязательным сценарием через `onnxruntime-gpu`.

Практический ориентир:

- `минимум`: современный 64-bit CPU, Python `3.11+`, `ffmpeg`, CPU-only запуск;
- `рекомендуется`: 4+ CPU cores для регулярной озвучки коротких и средних документов;
- `комфортно`: 6-8+ быстрых CPU cores или совместимый GPU для длинных документов и частых прогонов.

Подробная разбивка по `Silero` и `Piper`, официальные источники, ограничения и команды для self-check лежат в [docs/SYSTEM_REQUIREMENTS.md](docs/SYSTEM_REQUIREMENTS.md).

Быстрый self-check на своем железе:

```bash
cd /path/to/sayit
. .venv/bin/activate
/usr/bin/time -f 'elapsed=%E cpu=%P maxrss=%MKB' \
  python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages 1 \
  --config examples/silero.config.toml
```

```bash
cd /path/to/sayit
. .venv/bin/activate
/usr/bin/time -f 'elapsed=%E cpu=%P maxrss=%MKB' \
  python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages 1 \
  --config examples/piper.config.toml
```

Первый прогон может быть медленнее из-за загрузки модели или прогрева кэшей, поэтому скорость имеет смысл сравнивать как минимум со второго запуска.

## Запуск Через Silero

Silero теперь является дефолтным движком проекта. Для него не нужен `voice_model`, а базовая установка проекта уже включает его runtime-зависимости.

В `smart`-режиме Silero сглаживает технические переносы строк без пунктуации, но сохраняет абзацы, списки и паузы после знаков препинания. Также он может читать кириллические аббревиатуры по буквам и разворачивать короткие единицы измерения вроде `нм`, `мм`, `мг`.

Подробное описание возможностей, ограничений и сценариев запуска Silero находится в [docs/SILERO_CAPABILITIES.md](docs/SILERO_CAPABILITIES.md).

### 1. Установить зависимости

Базовый путь:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

Если нужен отдельный CPU-only PyTorch:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch
python -m pip install -e .
```

При первом реальном запуске Silero может скачать модель в локальный cache.

### 2. Пример конфига

Готовый пример лежит в [examples/silero.config.toml](examples/silero.config.toml).

```toml
engine = "silero"
output_dir = "output"
ffmpeg_bin = "ffmpeg"
output_format = "mp3"
split_mode = "merged"
table_strategy = "inline"
announce_page_numbers = true
pause_between_pages_ms = 700
silero_model_id = "v5_5_ru"
silero_speaker = "xenia"
silero_sample_rate = 48000
silero_device = "cpu"
silero_line_break_mode = "smart"
silero_transliterate_latin = true
silero_verbalize_numbers = true
silero_spell_cyrillic_abbreviations = true
silero_expand_short_units = true
```

### 3. Примеры запуска

Инспекция документа:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli inspect --input VPG_5.pdf
```

Озвучка через конфиг:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages all \
  --config examples/silero.config.toml
```

Озвучка через CLI без конфига:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages 1-3 \
  --engine silero \
  --silero-model-id v5_5_ru \
  --silero-speaker xenia \
  --silero-sample-rate 48000 \
  --silero-device cpu \
  --silero-line-break-mode smart \
  --silero-transliterate-latin \
  --silero-verbalize-numbers \
  --silero-spell-cyrillic-abbreviations \
  --silero-expand-short-units \
  --split merged \
  --format mp3 \
  --table-strategy inline \
  --announce-page-numbers \
  --pause-between-pages-ms 700
```

Режим "по файлу на страницу":

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages 1 \
  --engine silero \
  --silero-model-id v5_5_ru \
  --silero-speaker xenia \
  --silero-sample-rate 48000 \
  --silero-line-break-mode smart \
  --silero-transliterate-latin \
  --silero-verbalize-numbers \
  --silero-spell-cyrillic-abbreviations \
  --silero-expand-short-units \
  --split per-page \
  --format wav \
  --output-dir output_silero
```

Озвучка `.docx`:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input notes.docx \
  --pages all \
  --config examples/silero.config.toml
```

Озвучка `.md` или `.txt`:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input lechenie.md \
  --pages 1 \
  --engine silero \
  --silero-model-id v5_5_ru \
  --silero-speaker xenia \
  --silero-sample-rate 48000 \
  --silero-line-break-mode smart \
  --silero-transliterate-latin \
  --silero-verbalize-numbers \
  --silero-spell-cyrillic-abbreviations \
  --silero-expand-short-units \
  --split per-page \
  --format mp3
```

## Запуск Через Piper

Piper остается полностью поддержанным альтернативным движком. Для него нужен ONNX-файл голоса и sidecar-конфиг `*.onnx.json` рядом с ним.

### 1. Установить зависимости и скачать голос

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m piper.download_voices ru_RU-dmitri-medium
```

После загрузки обычно появляется файл вида:

```text
voices/ru_RU-dmitri-medium.onnx
voices/ru_RU-dmitri-medium.onnx.json
```

### 2. Пример конфига

Готовый пример лежит в [examples/piper.config.toml](examples/piper.config.toml).

```toml
engine = "piper"
voice_model = "voices/ru_RU-dmitri-medium.onnx"
output_dir = "output"
ffmpeg_bin = "ffmpeg"
output_format = "mp3"
split_mode = "merged"
table_strategy = "inline"
announce_page_numbers = true
pause_between_pages_ms = 700
length_scale = 1.3
noise_scale = 0.667
noise_w_scale = 0.8
```

### 3. Примеры запуска

Озвучка через конфиг:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages all \
  --config examples/piper.config.toml
```

Озвучка через CLI без конфига:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages 1-3 \
  --engine piper \
  --voice voices/ru_RU-dmitri-medium.onnx \
  --split merged \
  --format mp3 \
  --table-strategy inline \
  --announce-page-numbers \
  --pause-between-pages-ms 700 \
  --length-scale 1.3
```

Режим "по файлу на страницу":

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages 1,2,3 \
  --engine piper \
  --voice voices/ru_RU-dmitri-medium.onnx \
  --split per-page \
  --format wav \
  --output-dir output_piper_pages
```

Озвучка `.docx`:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input notes.docx \
  --pages all \
  --config examples/piper.config.toml
```

Озвучка `.md` или `.txt`:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input klinika.md \
  --pages 1 \
  --engine piper \
  --voice voices/ru_RU-dmitri-medium.onnx \
  --split per-page \
  --format mp3
```

## Примеры Конфигов

В каталоге `examples/` есть готовые шаблоны:

- [piper.config.toml](examples/piper.config.toml)
- [silero.config.toml](examples/silero.config.toml)
- [config.example.toml](examples/config.example.toml)

`config.example.toml` теперь отражает дефолтный Silero-сценарий, а для практического запуска под конкретный движок удобнее использовать отдельные конфиги.

## Полезные Параметры

- `--pages`: `all`, `1`, `1-5`, `1,3-5,8`
- `--split`: `per-page`, `per-range`, `merged`
- `--format`: `wav`, `mp3`, `m4a`
- `--table-strategy`: `skip`, `inline`, `separate`
- `--announce-page-numbers` и `--no-announce-page-numbers`
- `--pause-between-pages-ms`

Piper-specific:

- `--voice`
- `--length-scale`
- `--noise-scale`
- `--noise-w-scale`

Silero-specific:

- `--silero-model-id`
- `--silero-speaker`
- `--silero-sample-rate`
- `--silero-device`
- `--silero-line-break-mode`: `preserve`, `smart`, `flat`
- `--silero-transliterate-latin` и `--no-silero-transliterate-latin`
- `--silero-verbalize-numbers` и `--no-silero-verbalize-numbers`
- `--silero-spell-cyrillic-abbreviations` и `--no-silero-spell-cyrillic-abbreviations`
- `--silero-expand-short-units` и `--no-silero-expand-short-units`

## Проверка

```bash
. .venv/bin/activate
python -m pytest -q
python -m compileall src
python -m pdf_tts_ru.cli --help
bash tools/verify.sh
```
