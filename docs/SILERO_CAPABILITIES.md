# Silero В Проекте

Этот файл описывает, как именно `silero` используется в текущем проекте `pdf-tts-ru`, что в нем можно настраивать, что влияет на качество речи, а что влияет только на скорость работы.

Если нужен именно ответ на вопрос про железо, CPU/GPU и ожидания по времени выполнения, см. [docs/SYSTEM_REQUIREMENTS.md](SYSTEM_REQUIREMENTS.md).

## Главное Разделение: Silero И Torch

Нужно разделять две разные вещи:

- `Silero TTS` это сам движок синтеза речи.
- `torch` это runtime, на котором Silero работает.

То есть `torch` не является "более качественным движком". Он не делает голос лучше сам по себе. В контексте этого проекта `torch` влияет в первую очередь на совместимость и производительность:

- `torch` на `cpu` обычно медленнее;
- `torch` с `cuda` может быть заметно быстрее;
- качество речи при этом определяется не `torch`, а моделью Silero, выбранным голосом, sample rate и исходным текстом.

## Что Проект Поддерживает Для Silero Сейчас

В текущей реализации для `silero` доступны такие параметры:

- `engine = "silero"`
- `silero_model_id`
- `silero_speaker`
- `silero_sample_rate`
- `silero_rate`
- `silero_device`
- `silero_line_break_mode`
- `silero_transliterate_latin`
- `silero_verbalize_numbers`
- `silero_spell_cyrillic_abbreviations`
- `silero_expand_short_units`
- все общие параметры пайплайна:
  - `pages`
  - `split_mode`
  - `output_format`
  - `table_strategy`
  - `announce_page_numbers`
  - `pause_between_pages_ms`
  - `output_dir`

Также внутри проекта уже реализованы защитные механизмы для Silero:

- очистка проблемных символов перед синтезом;
- smart-обработка переносов строк без лишних пауз внутри фразы;
- транслитерация латиницы в русскоязычное произношение;
- побуквенное чтение кириллических аббревиатур;
- разворачивание коротких единиц измерения вроде `нм`, `мм`, `мг`;
- преобразование чисел в русские слова;
- автоматическое разбиение длинного текста на чанки;
- повторное более мелкое разбиение, если Silero считает chunk слишком длинным;
- сборка одного WAV из нескольких chunk'ов.

Это важно, потому что Silero чувствительнее Piper к отдельным символам и длине входного текста.

## Что Реально Влияет На Качество

### 1. `silero_model_id`

Это один из главных факторов качества.

Практически:

- более новые русские модели стоит пробовать раньше старых;
- в проекте по умолчанию используется `v5_5_ru`;
- если захочешь сравнивать, имеет смысл тестировать как минимум:
  - `v5_5_ru`
  - `v5_4_ru`

Что это дает:

- разные версии модели могут по-разному держать интонацию;
- отличаться по естественности;
- отличаться по стабильности на сложном тексте.

Базовый пример:

```toml
engine = "silero"
silero_model_id = "v5_5_ru"
silero_speaker = "xenia"
silero_sample_rate = 48000
# silero_rate = "normal"
silero_device = "cpu"
silero_line_break_mode = "smart"
silero_transliterate_latin = true
silero_verbalize_numbers = true
silero_spell_cyrillic_abbreviations = true
silero_expand_short_units = true
```

### 2. `silero_speaker`

Это влияет не столько на "качество" в абстрактном смысле, сколько на тембр, манеру речи и субъективную разборчивость.

На практике:

- один голос может звучать приятнее;
- другой может быть понятнее на учебных материалах;
- для длинных PDF иногда важнее не "красивый", а "ровный и разборчивый" голос.

В проекте уже проверен сценарий с:

```toml
silero_speaker = "xenia"
```

Если захочешь сравнивать голоса, делай это на одном и том же фрагменте PDF.

Пример запуска с другим голосом:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages 1-2 \
  --engine silero \
  --silero-model-id v5_5_ru \
  --silero-speaker kseniya \
  --silero-sample-rate 48000 \
  --silero-device cpu \
  --split merged \
  --format wav \
  --output-dir output_silero_kseniya
```

### 3. `silero_sample_rate`

В проекте для Silero поддерживаются:

- `8000`
- `24000`
- `48000`

Это уже сильнее влияет на качество итогового звука.

Практический смысл:

- `48000` это лучший вариант по качеству звука среди поддерживаемых;
- `24000` это компромисс между качеством и скоростью/размером;
- `8000` это только для совсем легкого, низкокачественного сценария.

Если цель именно "более качественная речь", то начинать надо с:

```toml
silero_sample_rate = 48000
output_format = "wav"
```

### 4. `silero_rate`

Этот параметр управляет именно скоростью речи Silero через SSML `prosody rate`.

Поддерживаются канонические значения:

- `x-slow`
- `slow`
- `medium`
- `fast`
- `x-fast`

Также проект принимает alias-значения:

- `normal` -> `medium`
- `slower` -> `slow`
- `faster` -> `fast`

Практический смысл:

- `silero_rate` меняет темп произнесения текста;
- `silero_sample_rate` не меняет темп речи и отвечает за частоту дискретизации аудио;
- если `silero_rate` не задан, проект оставляет текущий путь Silero без явной настройки темпа.

Пример конфига:

```toml
silero_rate = "slow"
```

Пример CLI:

```bash
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages 1 \
  --engine silero \
  --silero-rate normal
```

### 5. `silero_line_break_mode`

Этот параметр управляет тем, как проект готовит переносы строк перед подачей текста в Silero.

Поддерживаются режимы:

- `preserve`: оставить исходные переносы как есть;
- `smart`: сгладить только технические переносы без пунктуации;
- `flat`: максимально склеить строки внутри прозы.

Для born-digital PDF по умолчанию выбран `smart`, потому что он убирает искусственные паузы в середине фразы, но сохраняет абзацы и списки.

### 6. Формат вывода

Это уже не качество самого синтеза, а качество сохраненного результата.

Практически:

- `wav` сохраняет результат без потерь;
- `mp3` удобнее и меньше по размеру, но это уже компрессия;
- `m4a` тоже компрессия.

Если хочешь выжать максимум из Silero, лучший экспортный путь такой:

```toml
output_format = "wav"
```

Потом уже при необходимости конвертировать в `mp3`.

## Что Влияет На Скорость, Но Не Делает Голос Лучше Само По Себе

### 1. `silero_device`

Поддерживаются значения вида:

- `cpu`
- `cuda` при наличии подходящего окружения

Смысл:

- `cpu` проще и стабильнее;
- `cuda` может ускорить синтез;
- качество речи от этого само по себе не становится лучше.

Пример:

```toml
silero_device = "cuda"
```

Но использовать это стоит только если у тебя уже установлен подходящий CUDA-compatible PyTorch.

### 2. Установка PyTorch

Есть два практических сценария:

CPU-only:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch
python -m pip install -e .
```

Обычный путь, если подходит базовая установка проекта:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

Legacy-aliас `.[silero]` тоже остается рабочим, но он больше не обязателен: Silero теперь входит в базовую установку проекта.

## Практические Сценарии Использования Silero

Ниже не абстрактные возможности, а реально полезные режимы запуска именно в этом проекте.

### Сценарий 1. Максимальное качество звука

Когда использовать:

- если важнее качество, чем размер файла;
- если будешь потом слушать длинный документ;
- если хочешь сравнить Silero с Piper максимально честно.

Рекомендации:

- `silero_model_id = "v5_5_ru"`
- `silero_speaker = "xenia"`
- `silero_sample_rate = 48000`
- `output_format = "wav"`
- `split_mode = "merged"`

Пример конфига:

```toml
engine = "silero"
output_dir = "output"
ffmpeg_bin = "ffmpeg"
output_format = "wav"
split_mode = "merged"
table_strategy = "inline"
announce_page_numbers = true
pause_between_pages_ms = 700
silero_model_id = "v5_5_ru"
silero_speaker = "xenia"
silero_sample_rate = 48000
silero_device = "cpu"
```

Пример запуска:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages all \
  --engine silero \
  --silero-model-id v5_5_ru \
  --silero-speaker xenia \
  --silero-sample-rate 48000 \
  --silero-device cpu \
  --split merged \
  --format wav \
  --table-strategy inline \
  --announce-page-numbers \
  --pause-between-pages-ms 700
```

### Сценарий 2. Качество С Компромиссом По Размеру

Когда использовать:

- если качество еще важно, но не нужен огромный WAV;
- если результат надо хранить и пересылать.

Рекомендации:

- тот же `v5_5_ru`;
- `48000`;
- `mp3` вместо `wav`.

Пример запуска:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages all \
  --engine silero \
  --silero-model-id v5_5_ru \
  --silero-speaker xenia \
  --silero-sample-rate 48000 \
  --silero-device cpu \
  --split merged \
  --format mp3 \
  --table-strategy inline \
  --announce-page-numbers \
  --pause-between-pages-ms 700
```

### Сценарий 3. Более Быстрый Запуск На CPU

Когда использовать:

- если документ длинный;
- если важнее скорость и меньший размер, чем максимум качества.

Рекомендации:

- `silero_sample_rate = 24000`;
- `output_format = "mp3"`;
- `split_mode = "merged"` или `per-page`.

Пример конфига:

```toml
engine = "silero"
output_dir = "output_fast"
ffmpeg_bin = "ffmpeg"
output_format = "mp3"
split_mode = "merged"
table_strategy = "inline"
announce_page_numbers = false
pause_between_pages_ms = 300
silero_model_id = "v5_5_ru"
silero_speaker = "xenia"
silero_sample_rate = 24000
silero_device = "cpu"
```

Пример запуска:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages all \
  --engine silero \
  --silero-model-id v5_5_ru \
  --silero-speaker xenia \
  --silero-sample-rate 24000 \
  --silero-device cpu \
  --split merged \
  --format mp3 \
  --table-strategy inline \
  --no-announce-page-numbers \
  --pause-between-pages-ms 300 \
  --output-dir output_fast
```

### Сценарий 4. Более Быстрый Запуск На GPU

Когда использовать:

- если у тебя уже настроен CUDA-compatible PyTorch;
- если нужно прогонять длинные документы быстрее.

Главное:

- это в первую очередь про скорость;
- не про "более качественный движок".

Пример запуска:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages all \
  --engine silero \
  --silero-model-id v5_5_ru \
  --silero-speaker xenia \
  --silero-sample-rate 48000 \
  --silero-device cuda \
  --split merged \
  --format mp3 \
  --table-strategy inline
```

### Сценарий 5. Сравнение Разных Голосов На Одном Фрагменте

Когда использовать:

- если хочешь подобрать голос под учебные PDF;
- если важнее понятность, чем просто "красивое звучание".

Правильный способ сравнения:

1. взять один и тот же фрагмент, например `--pages 1-2`;
2. сохранить в `wav`;
3. менять только `silero_speaker`.

Пример:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages 1-2 \
  --engine silero \
  --silero-model-id v5_5_ru \
  --silero-speaker xenia \
  --silero-sample-rate 48000 \
  --format wav \
  --split merged \
  --output-dir output_xenia
```

Потом тем же способом:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages 1-2 \
  --engine silero \
  --silero-model-id v5_5_ru \
  --silero-speaker baya \
  --silero-sample-rate 48000 \
  --format wav \
  --split merged \
  --output-dir output_baya
```

### Сценарий 6. Работа С Таблицами

Silero использует тот же extraction pipeline, что и Piper, поэтому здесь возможности определяются не самим TTS, а общим пайплайном проекта.

Доступны три режима:

- `skip`
- `inline`
- `separate`

Если документ содержит много таблиц:

- `inline` полезен, если таблицы надо читать в потоке текста;
- `separate` полезен, если таблицы нужно вынести в отдельные аудиофайлы;
- `skip` полезен, если таблицы мешают.

Пример:

```bash
cd /path/to/sayit
. .venv/bin/activate
python -m pdf_tts_ru.cli synth \
  --input VPG_5.pdf \
  --pages all \
  --engine silero \
  --silero-model-id v5_5_ru \
  --silero-speaker xenia \
  --silero-sample-rate 48000 \
  --split per-page \
  --format mp3 \
  --table-strategy separate \
  --output-dir output_silero_tables
```

### Сценарий 7. Проверка И Подбор На Одной Странице

Это лучший режим для быстрых экспериментов.

Пример:

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
  --split per-page \
  --format wav \
  --output-dir output_probe
```

Этот режим удобен, чтобы быстро сравнивать:

- `xenia` vs другой speaker;
- `48000` vs `24000`;
- `inline` vs `skip`;
- `announce-page-numbers` vs `no-announce-page-numbers`.

## Чего В Silero Пока Нет В Этом Проекте

По сравнению с Piper в текущем проекте для Silero пока нет отдельных пользовательских ручек вроде:

- регулировки скорости речи;
- прямой настройки шума;
- прямой настройки вариативности голоса;
- тонкой ручной настройки интонации.

То есть сейчас Silero в проекте настраивается через:

- выбор модели;
- выбор speaker;
- выбор sample rate;
- выбор output format;
- выбор device;
- общие параметры пайплайна.

Если тебе нужен именно отдельный режим "Silero, но медленнее", это уже отдельная задача на доработку проекта.

## Рекомендуемые Стартовые Профили

Если нужен лучший общий старт:

```toml
engine = "silero"
output_format = "wav"
split_mode = "merged"
table_strategy = "inline"
announce_page_numbers = true
pause_between_pages_ms = 700
silero_model_id = "v5_5_ru"
silero_speaker = "xenia"
silero_sample_rate = 48000
silero_device = "cpu"
```

Если нужен практичный компромисс:

```toml
engine = "silero"
output_format = "mp3"
split_mode = "merged"
table_strategy = "inline"
announce_page_numbers = true
pause_between_pages_ms = 700
silero_model_id = "v5_5_ru"
silero_speaker = "xenia"
silero_sample_rate = 48000
silero_device = "cpu"
```

Если нужен более быстрый запуск:

```toml
engine = "silero"
output_format = "mp3"
split_mode = "merged"
table_strategy = "inline"
announce_page_numbers = false
pause_between_pages_ms = 300
silero_model_id = "v5_5_ru"
silero_speaker = "xenia"
silero_sample_rate = 24000
silero_device = "cpu"
```

## Где Это Использовать

Для практического запуска в проекте смотри также:

- [README.md](../README.md)
- [examples/silero.config.toml](../examples/silero.config.toml)
