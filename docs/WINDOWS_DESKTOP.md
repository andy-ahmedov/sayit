# Windows Desktop App

GUI построен как thin desktop shell над существующим `pdf_tts_ru` pipeline. Это значит:

- логика извлечения текста, резолва конфига и синтеза остаётся общей с CLI;
- GUI не дублирует пайплайн, а собирает `SynthesisRequest` и запускает `PdfTtsPipeline`;
- ошибки от back-end слоя показываются пользователю как явные сообщения, а не silent failure.

## Что входит в первую версию

- выбор входного документа;
- inspect summary по страницам и таблицам;
- ввод `pages`;
- выбор `Silero` или `Piper`;
- engine-specific параметры в форме;
- загрузка и сохранение `TOML`-конфига;
- выбор output folder;
- запуск синтеза в фоне;
- лог статусов;
- кнопка открытия папки результата.

В первую версию не входят очередь задач, история запусков и встроенный аудиоплеер.

## Локальный запуск GUI

Установить desktop-зависимости:

```bash
python -m pip install -e '.[desktop]'
```

Запустить:

```bash
python -m pdf_tts_ru.gui.main
```

или:

```bash
pdf-tts-ru-gui
```

Если `PySide6` не установлен, GUI entrypoint завершится с подсказкой установить `.[desktop]`.

## Как GUI работает с конфигом

- `Load TOML` читает существующий `config.toml` и заполняет форму.
- `Save TOML as...` сохраняет текущее состояние формы обратно в `TOML`.
- Текущий выбранный input file и `pages` остаются частью состояния окна, а не обязательной частью `config.toml`.

## Как GUI работает с результатом

Под "скачать результат" в локальном desktop-сценарии понимается:

- пользователь заранее выбирает `output_dir`;
- pipeline пишет готовые `wav` / `mp3` / `m4a` в эту папку;
- после завершения GUI показывает список файлов и умеет открыть папку результата.

## Windows Build

Для сборки portable one-folder bundle нужен `PyInstaller`:

```bash
python -m pip install -e '.[desktop]'
python tools/build_windows_gui.py --ffmpeg-bin C:\path\to\ffmpeg.exe
```

Что делает build helper:

- собирает GUI в `PyInstaller --onedir`;
- добавляет `src` в import path;
- при переданном `--ffmpeg-bin` кладёт `ffmpeg.exe` в корень bundle.

После этого приложение при запуске пытается найти bundled `ffmpeg.exe` рядом с `.exe`. Если его нет, используется обычный `ffmpeg` из `PATH` или явное значение из формы/конфига.

## Piper и голоса

В bundled app `Silero` должен работать из коробки при наличии его runtime-зависимостей в сборке. Для `Piper` в первой версии не бандлится готовый голос:

- пользователь выбирает свой `.onnx` voice model через file picker;
- если `Piper` выбран без voice model, приложение блокирует запуск и показывает ошибку.
