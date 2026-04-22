# System Requirements

Этот документ отвечает на практический вопрос: потянет ли компьютер проект `pdf-tts-ru`, какой движок лучше выбрать под конкретное железо и когда стоит ожидать медленную обработку.

Ниже специально разделены два типа утверждений:

- `Official`: то, что прямо подтверждается первичными источниками движка или runtime;
- `Repo guidance`: практические рекомендации именно для этого репозитория. Это не vendor-spec и не обещание точного времени.

## Общий Baseline Проекта

### Minimum

- `Official`: Python `>=3.11` требуется самим проектом по [pyproject.toml](/home/andy/github.com/andy-ahmedov/speech/pyproject.toml).
- `Official`: нужен установленный `ffmpeg`, потому что проект конвертирует и склеивает аудио через `ffmpeg`.
- `Official`: проект рассчитан на born-digital документы `.pdf`, `.docx`, `.md`, `.txt`; OCR не является happy path.
- `Repo guidance`: GPU не нужен для самого проекта как обязательный компонент.

### Recommended

- `Repo guidance`: современный 64-bit CPU и SSD заметно повышают комфорт при длинных прогонах, потому что проект пишет временные WAV и итоговые `mp3`/`m4a`.
- `Repo guidance`: если планируются длинные документы, полезно иметь запас по CPU, а не только по диску.

### Comfortable

- `Repo guidance`: для частой озвучки длинных документов комфорт определяется в первую очередь скоростью CPU или наличием корректно настроенного GPU-пути у выбранного движка.

## Silero

### Что Требуется

- `Official`: Silero требует `PyTorch-compatible system`.
- `Official`: для платформы `x86_64` Silero указывает минимальное требование: современный процессор с набором инструкций `AVX2`.
- `Official`: модели скачиваются по требованию и кэшируются локально.
- `Official`: GPU не обязателен. Для ускорения PyTorch может использовать `CUDA` на NVIDIA GPU или `ROCm` на совместимых AMD GPU.

Источники:

- Silero README: <https://github.com/snakers4/silero-models>
- raw README с minimal requirements: <https://raw.githubusercontent.com/snakers4/silero-models/master/README.md>
- PyTorch local install guide: <https://pytorch.org/get-started/locally/>

### Minimum

- `Official`: CPU-only запуск возможен.
- `Official`: на `x86_64` нужен CPU с `AVX2`.
- `Repo guidance`: если у вас обычный современный ноутбук или ПК без дискретной видеокарты, дефолтный `Silero`-сценарий проекта обычно должен запускаться.

### Recommended

- `Repo guidance`: 4+ быстрых CPU cores дают заметно более комфортный CPU-only сценарий для коротких и средних документов.
- `Repo guidance`: для большинства пользователей это лучший baseline, если нет желания поднимать `CUDA`/`ROCm`.
- `Repo guidance`: sample rate `48000` и длинные документы увеличивают время синтеза сильнее, чем короткие smoke-runs на 1 странице.

### Comfortable

- `Repo guidance`: 6-8+ быстрых CPU cores уже подходят для регулярной озвучки длинных документов без ощущения, что пайплайн “еле ползет”.
- `Official`: совместимый GPU может заметно ускорять PyTorch path.
- `Repo guidance`: GPU особенно имеет смысл, если вы регулярно гоняете длинные документы или сравниваете разные конфиги/голоса.

### Что Известно О Скорости

- `Official`: у Silero есть benchmark wiki с метрикой `RTF/RTS`.
- `Official`: в их TTS benchmarks для 16 kHz модели на `Intel i7-6800K @ 3.40GHz` указано примерно:
  - CPU 1 thread: около `1.4x` realtime;
  - CPU 2 threads: около `2.3x` realtime;
  - CPU 4 threads: около `3.1x` realtime;
  - GPU `1080 Ti`: около `16.9x` realtime.
- `Official`: в тех же бенчмарках Silero отмечает, что прирост после 4 CPU threads уже ограничен.
- `Repo guidance`: эти цифры относятся к их стенду и не являются гарантией именно для `pdf-tts-ru`, тем более для `v5_5_ru`, другой длины текста, другого sample rate и ваших preprocessing-настроек.

Источник:

- <https://github.com/snakers4/silero-models/wiki/Performance-Benchmarks>

### Когда Silero Может Ощутимо Тормозить

- `Repo guidance`: первый запуск может быть медленнее из-за скачивания модели и прогрева кэша.
- `Repo guidance`: длинные PDF, `48000` Hz, объединенный `merged` output и CPU-only режим на слабом процессоре сильнее всего увеличивают время прогона.
- `Repo guidance`: на слабом железе Silero обычно остается рабочим, но может быть менее комфортным, чем Piper.

## Piper

### Что Требуется

- `Official`: для Python API нужен пакет `piper-tts`.
- `Official`: нужен локальный голос: `.onnx` модель и рядом `.onnx.json`.
- `Official`: voices экспортированы под `onnxruntime`.
- `Official`: CPU inference является стандартным путем.
- `Official`: для GPU-ускорения нужен `onnxruntime-gpu`.

Источники:

- Piper project: <https://github.com/OHF-Voice/piper1-gpl>
- Piper Python API: <https://raw.githubusercontent.com/OHF-Voice/piper1-gpl/main/docs/API_PYTHON.md>
- Piper voices: <https://raw.githubusercontent.com/OHF-Voice/piper1-gpl/main/docs/VOICES.md>

### Minimum

- `Official`: CPU-only запуск поддерживается из коробки.
- `Official`: `piper-tts` распространяется wheel-пакетами для типовых 64-bit платформ, включая `manylinux x86_64`, `manylinux aarch64`, `macOS x86_64`, `macOS arm64`, `win_amd64`.
- `Repo guidance`: для слабого железа Piper обычно рациональнее запускать с голосами `x_low`, `low` или `medium`, а не ожидать одинакового комфорта от всех voices.

Источник:

- PyPI package metadata: <https://pypi.org/project/piper-tts/>

### Recommended

- `Repo guidance`: современный 4-core desktop/laptop CPU уже подходит для регулярной локальной озвучки.
- `Repo guidance`: `medium` голоса обычно дают хороший баланс качества и скорости для этого проекта.
- `Official`: уровни качества голосов у Piper различаются по размеру модели:
  - `x_low`: `16 kHz`, `5-7M` params;
  - `low`: `16 kHz`, `15-20M` params;
  - `medium`: `22.05 kHz`, `15-20M` params;
  - `high`: `22.05 kHz`, `28-32M` params.
- `Repo guidance`: чем тяжелее voice level, тем выше ожидания к CPU и тем дольше синтез.

Источник:

- <https://rhasspy.github.io/piper-samples/>

### Comfortable

- `Repo guidance`: 6-8+ быстрых CPU cores дают заметно более спокойный режим для длинных документов и повторных прогонов.
- `Official`: GPU-путь возможен, но это уже отдельная настройка через `onnxruntime-gpu`, а не стандартный happy path.
- `Repo guidance`: в рамках этого проекта Piper стоит считать прежде всего CPU-friendly движком, а не GPU-first решением.

### Что Известно О Скорости

- `Official`: Piper CLI предупреждает, что разовый CLI запуск может быть медленным, потому что голос загружается каждый раз.
- `Official`: upstream не публикует такой же подробной универсальной таблицы throughput, как Silero.
- `Repo guidance`: из-за этого корректнее не обещать конкретные секунды “на любом железе”, а оценивать скорость локальным smoke-run на вашем документе и вашем голосе.

Источник:

- Piper CLI docs: <https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md>

### Когда Piper Может Ощутимо Тормозить

- `Repo guidance`: тяжелые `high` voices, длинные merged-выгрузки и слабый CPU делают Piper заметно менее отзывчивым.
- `Repo guidance`: для “слабого, но рабочего” компьютера Piper часто удобнее Silero, но это зависит от конкретного голоса.
- `Repo guidance`: GPU-путь для Piper не стоит считать обязательным или автоматически более быстрым без локальной проверки.

## GPU: Когда Он Вообще Нужен

### Silero

- `Official`: GPU нужен только если вы хотите ускорить `torch` inference.
- `Official`: для NVIDIA path нужен CUDA-capable GPU; для AMD path нужен ROCm-capable GPU.
- `Repo guidance`: для большинства пользователей проекта CPU-only запуск остается самым простым и предсказуемым вариантом.

### Piper

- `Official`: GPU нужен только для optional path через `onnxruntime-gpu`.
- `Official`: для ONNX Runtime GPU package требуются совместимые `CUDA` и `cuDNN`.
- `Repo guidance`: если вы не уверены в своей GPU-конфигурации, рациональнее считать Piper CPU-only движком.

Источники:

- ONNX Runtime install: <https://onnxruntime.ai/docs/install/>
- ONNX Runtime CUDA EP requirements: <https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html>

## Как Быстро Проверить Свое Железо

Ниже не “официальный benchmark”, а practical self-check для этого репозитория.

### 1. Silero CPU-only

```bash
cd /home/andy/github.com/andy-ahmedov/speech
. .venv/bin/activate
/usr/bin/time -f 'elapsed=%E cpu=%P maxrss=%MKB' \
  python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages 1 \
  --config examples/silero.config.toml
```

### 2. Silero CUDA

```bash
cd /home/andy/github.com/andy-ahmedov/speech
. .venv/bin/activate
/usr/bin/time -f 'elapsed=%E cpu=%P maxrss=%MKB' \
  python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages 1 \
  --engine silero \
  --silero-model-id v5_5_ru \
  --silero-speaker xenia \
  --silero-sample-rate 48000 \
  --silero-device cuda \
  --silero-line-break-mode smart \
  --silero-transliterate-latin \
  --silero-verbalize-numbers \
  --silero-spell-cyrillic-abbreviations \
  --silero-expand-short-units \
  --split per-page \
  --format wav \
  --output-dir output_bench_silero_cuda
```

### 3. Piper

```bash
cd /home/andy/github.com/andy-ahmedov/speech
. .venv/bin/activate
/usr/bin/time -f 'elapsed=%E cpu=%P maxrss=%MKB' \
  python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages 1 \
  --config examples/piper.config.toml
```

### Как Читать Результат

- `Repo guidance`: сравнивайте не первый запуск, а второй или третий, потому что на первом могут загружаться модели и прогреваться кэши.
- `Repo guidance`: если одна страница озвучивается примерно в realtime или быстрее, компьютер уже подходит для повседневного использования.
- `Repo guidance`: если даже одна страница идет заметно медленнее realtime, длинные документы будут требовать терпения; в этом случае обычно стоит:
  - для `Silero` остаться на CPU-only baseline или попробовать GPU, если он уже настроен;
  - для `Piper` перейти на более легкий voice level;
  - тестировать сначала `per-page`, а не длинный `merged`.

## Вывод По Выбору Движка

- Если нужен самый простой дефолтный путь и у вас обычный современный ПК: начинайте с `Silero`.
- Если железо слабее или нужен более “легкий” CPU-only сценарий: часто выгоднее начать с `Piper`.
- Если у вас есть совместимый и уже настроенный GPU: сначала имеет смысл пробовать ускорение для `Silero`, а не строить весь расчет на GPU-пути `Piper`.
