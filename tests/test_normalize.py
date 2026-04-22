from pdf_tts_ru.normalize import normalize_text_for_speech, strip_markdown_for_speech


def test_normalize_basic_whitespace() -> None:
    text = "Привет,   мир\n\n\nЭто   тест"
    assert normalize_text_for_speech(text) == "Привет, мир\nЭто тест"


def test_strip_markdown_for_speech_removes_common_markup() -> None:
    text = (
        "# Заголовок\n"
        "- пункт списка\n"
        "[ссылка](https://example.com)\n"
        "![схема](https://example.com/image.png)\n"
        "```python\nprint('skip')\n```\n"
        "**важный** `код`"
    )

    assert strip_markdown_for_speech(text) == (
        "Заголовок\n"
        "пункт списка\n"
        "ссылка\n"
        "схема\n"
        "\n"
        "важный код"
    )
