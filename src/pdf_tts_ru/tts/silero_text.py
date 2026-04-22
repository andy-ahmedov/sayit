from __future__ import annotations

import re

from pdf_tts_ru.models import SileroLineBreakMode, SileroSynthesisSettings


_FORMAT_CHARS_RE = re.compile(r"[\u200b-\u200d\ufeff]")
_NUMBER_GROUP_RE = re.compile(r"(?<=\d)[\s\u00a0\u202f](?=\d{3}\b)")
_LETTER_DIGIT_BOUNDARY_RE = re.compile(r"(?<=[A-Za-zА-Яа-яЁё])(?=\d)|(?<=\d)(?=[A-Za-zА-Яа-яЁё])")
_LATIN_WORD_RE = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")
_NUMBER_TOKEN_RE = re.compile(r"(?<![\w])([+-]?\d+(?:[.,]\d+)?%?)(?![\w])")
_CYRILLIC_ACRONYM_RE = re.compile(r"(?<![А-ЯЁа-яё])([А-ЯЁ]{2,6})(?![А-ЯЁа-яё])")
_ENDS_WITH_PUNCTUATION_RE = re.compile(r"[.,;:!?…][\"')\]»]*$")
_LIST_MARKER_RE = re.compile(r"^(?:[-—•*]\s+|\d+[.)]\s+|[A-Za-zА-Яа-яЁё][.)]\s+)")

_SILERO_REPLACEMENTS = {
    "(": ", ",
    ")": ", ",
    "[": ", ",
    "]": ", ",
    "{": ", ",
    "}": ", ",
    "<": " меньше ",
    ">": " больше ",
    "~": " примерно ",
    "^": " в степени ",
    "*": " ",
    "/": " ",
    "\\": " ",
    "_": " ",
}

_LATIN_ACRONYM_NAMES = {
    "a": "эй",
    "b": "би",
    "c": "си",
    "d": "ди",
    "e": "и",
    "f": "эф",
    "g": "джи",
    "h": "эйч",
    "i": "ай",
    "j": "джей",
    "k": "кей",
    "l": "эл",
    "m": "эм",
    "n": "эн",
    "o": "оу",
    "p": "пи",
    "q": "кью",
    "r": "ар",
    "s": "эс",
    "t": "ти",
    "u": "ю",
    "v": "ви",
    "w": "дабл ю",
    "x": "икс",
    "y": "уай",
    "z": "зи",
}

_CYRILLIC_LETTER_NAMES = {
    "А": "а",
    "Б": "бэ",
    "В": "вэ",
    "Г": "гэ",
    "Д": "дэ",
    "Е": "е",
    "Ё": "ё",
    "Ж": "жэ",
    "З": "зэ",
    "И": "и",
    "Й": "й",
    "К": "ка",
    "Л": "эл",
    "М": "эм",
    "Н": "эн",
    "О": "о",
    "П": "пэ",
    "Р": "эр",
    "С": "эс",
    "Т": "тэ",
    "У": "у",
    "Ф": "эф",
    "Х": "ха",
    "Ц": "цэ",
    "Ч": "чэ",
    "Ш": "ша",
    "Щ": "ща",
    "Ъ": "твёрдый знак",
    "Ы": "ы",
    "Ь": "мягкий знак",
    "Э": "э",
    "Ю": "ю",
    "Я": "я",
}

_LATIN_MULTI_REPLACEMENTS = (
    ("tch", "ч"),
    ("sch", "щ"),
    ("sh", "ш"),
    ("ch", "ч"),
    ("zh", "ж"),
    ("kh", "х"),
    ("ts", "ц"),
    ("ph", "ф"),
    ("th", "т"),
    ("qu", "кв"),
    ("ck", "к"),
    ("ee", "и"),
    ("oo", "у"),
    ("ya", "я"),
    ("yo", "ё"),
    ("yu", "ю"),
    ("ye", "йе"),
    ("ai", "эй"),
    ("ay", "эй"),
    ("ei", "ей"),
    ("ey", "ей"),
    ("oi", "ой"),
    ("oy", "ой"),
    ("ow", "ау"),
    ("ou", "ау"),
    ("au", "ау"),
)

_LATIN_CHAR_MAP = {
    "a": "а",
    "b": "б",
    "c": "к",
    "d": "д",
    "e": "е",
    "f": "ф",
    "g": "г",
    "h": "х",
    "i": "и",
    "j": "дж",
    "k": "к",
    "l": "л",
    "m": "м",
    "n": "н",
    "o": "о",
    "p": "п",
    "q": "к",
    "r": "р",
    "s": "с",
    "t": "т",
    "u": "у",
    "v": "в",
    "w": "в",
    "x": "кс",
    "y": "й",
    "z": "з",
}

_SHORT_UNIT_FORMS = {
    "нм": ("нанометр", "нанометра", "нанометров"),
    "мкм": ("микрометр", "микрометра", "микрометров"),
    "мм": ("миллиметр", "миллиметра", "миллиметров"),
    "см": ("сантиметр", "сантиметра", "сантиметров"),
    "дм": ("дециметр", "дециметра", "дециметров"),
    "км": ("километр", "километра", "километров"),
    "мг": ("миллиграмм", "миллиграмма", "миллиграммов"),
    "г": ("грамм", "грамма", "граммов"),
    "кг": ("килограмм", "килограмма", "килограммов"),
    "мл": ("миллилитр", "миллилитра", "миллилитров"),
    "л": ("литр", "литра", "литров"),
}

_SHORT_UNIT_PATTERN = "|".join(sorted(_SHORT_UNIT_FORMS, key=len, reverse=True))
_NUMBER_WITH_SHORT_UNIT_RE = re.compile(
    rf"(?<![\w])([+-]?\d+(?:[.,]\d+)?)\s*({_SHORT_UNIT_PATTERN})(?![А-Яа-яЁёA-Za-z])",
    re.IGNORECASE,
)
_STANDALONE_SHORT_UNIT_RE = re.compile(
    rf"(?<![\w])({_SHORT_UNIT_PATTERN})(?![А-Яа-яЁёA-Za-z])",
    re.IGNORECASE,
)

_DIGIT_WORDS = {
    "0": "ноль",
    "1": "один",
    "2": "два",
    "3": "три",
    "4": "четыре",
    "5": "пять",
    "6": "шесть",
    "7": "семь",
    "8": "восемь",
    "9": "девять",
}

_UNITS_MASC = {
    1: "один",
    2: "два",
    3: "три",
    4: "четыре",
    5: "пять",
    6: "шесть",
    7: "семь",
    8: "восемь",
    9: "девять",
}

_UNITS_FEM = {
    1: "одна",
    2: "две",
    3: "три",
    4: "четыре",
    5: "пять",
    6: "шесть",
    7: "семь",
    8: "восемь",
    9: "девять",
}

_TEENS = {
    10: "десять",
    11: "одиннадцать",
    12: "двенадцать",
    13: "тринадцать",
    14: "четырнадцать",
    15: "пятнадцать",
    16: "шестнадцать",
    17: "семнадцать",
    18: "восемнадцать",
    19: "девятнадцать",
}

_TENS = {
    2: "двадцать",
    3: "тридцать",
    4: "сорок",
    5: "пятьдесят",
    6: "шестьдесят",
    7: "семьдесят",
    8: "восемьдесят",
    9: "девяносто",
}

_HUNDREDS = {
    1: "сто",
    2: "двести",
    3: "триста",
    4: "четыреста",
    5: "пятьсот",
    6: "шестьсот",
    7: "семьсот",
    8: "восемьсот",
    9: "девятьсот",
}

_SCALE_FORMS = [
    ("", "", "", "masc"),
    ("тысяча", "тысячи", "тысяч", "fem"),
    ("миллион", "миллиона", "миллионов", "masc"),
    ("миллиард", "миллиарда", "миллиардов", "masc"),
    ("триллион", "триллиона", "триллионов", "masc"),
]


def prepare_text_for_silero(text: str, settings: SileroSynthesisSettings) -> str:
    """Prepare text so Silero reads Russian, abbreviations, and numbers more reliably."""

    prepared = _FORMAT_CHARS_RE.sub("", text)
    prepared = _NUMBER_GROUP_RE.sub("", prepared)
    prepared = _LETTER_DIGIT_BOUNDARY_RE.sub(" ", prepared)
    prepared = _normalize_line_breaks(prepared, settings.line_break_mode)
    for source, replacement in _SILERO_REPLACEMENTS.items():
        prepared = prepared.replace(source, replacement)

    if settings.expand_short_units:
        prepared = _NUMBER_WITH_SHORT_UNIT_RE.sub(_replace_short_unit_with_number, prepared)
        prepared = _STANDALONE_SHORT_UNIT_RE.sub(_replace_standalone_short_unit, prepared)
    if settings.spell_cyrillic_abbreviations:
        prepared = _CYRILLIC_ACRONYM_RE.sub(_replace_cyrillic_abbreviation, prepared)
    if settings.transliterate_latin:
        prepared = _LATIN_WORD_RE.sub(_replace_latin_word, prepared)
    if settings.verbalize_numbers:
        prepared = _NUMBER_TOKEN_RE.sub(_replace_numeric_token, prepared)

    prepared = re.sub(r"[ \t]+", " ", prepared)
    prepared = re.sub(r" ?\n ?", "\n", prepared)
    prepared = re.sub(r"\n{3,}", "\n\n", prepared)
    return prepared.strip()


def _normalize_line_breaks(text: str, mode: SileroLineBreakMode) -> str:
    if mode == SileroLineBreakMode.PRESERVE:
        return text

    normalized_lines = [line.strip() for line in text.splitlines()]
    if not normalized_lines:
        return text.strip()

    result = ""
    previous_line = ""
    for line in normalized_lines:
        if not line:
            if result and not result.endswith("\n\n"):
                result = result.rstrip() + "\n\n"
            continue

        if not result:
            result = line
            previous_line = line
            continue

        if result.endswith("\n\n"):
            result += line
            previous_line = line
            continue

        separator = " "
        if mode == SileroLineBreakMode.SMART and _should_preserve_line_break(previous_line, line):
            separator = "\n"
        result += separator + line
        previous_line = line

    return result


def _should_preserve_line_break(previous_line: str, current_line: str) -> bool:
    return bool(
        _ENDS_WITH_PUNCTUATION_RE.search(previous_line)
        or _LIST_MARKER_RE.match(current_line)
    )


def _replace_latin_word(match: re.Match[str]) -> str:
    return latin_word_to_russian(match.group(0))


def _replace_cyrillic_abbreviation(match: re.Match[str]) -> str:
    return spell_cyrillic_abbreviation(match.group(1))


def _replace_short_unit_with_number(match: re.Match[str]) -> str:
    number = match.group(1)
    unit = match.group(2).lower()
    one, few, many = _SHORT_UNIT_FORMS[unit]
    spoken_number = number_token_to_russian(number)
    return f"{spoken_number} {_unit_form_for_number(number, one=one, few=few, many=many)}"


def _replace_standalone_short_unit(match: re.Match[str]) -> str:
    return spell_cyrillic_abbreviation(match.group(1).upper())


def latin_word_to_russian(word: str) -> str:
    """Approximate Latin-script words with a Russian-friendly pronunciation."""

    parts = [part for part in re.split(r"[-']+", word) if part]
    if len(parts) > 1:
        return " ".join(latin_word_to_russian(part) for part in parts)

    if word.isupper():
        return " ".join(_LATIN_ACRONYM_NAMES.get(char.lower(), char.lower()) for char in word)

    translated = word.lower()
    for source, replacement in _LATIN_MULTI_REPLACEMENTS:
        translated = translated.replace(source, replacement)

    pieces: list[str] = []
    for char in translated:
        pieces.append(_LATIN_CHAR_MAP.get(char, char))
    return "".join(pieces)


def spell_cyrillic_abbreviation(token: str) -> str:
    """Spell a Cyrillic abbreviation letter by letter."""

    return " ".join(_CYRILLIC_LETTER_NAMES.get(char, char.lower()) for char in token)


def _replace_numeric_token(match: re.Match[str]) -> str:
    return number_token_to_russian(match.group(1))


def number_token_to_russian(token: str) -> str:
    """Convert a numeric token into a simple spoken Russian representation."""

    is_percent = token.endswith("%")
    raw_number = token[:-1] if is_percent else token
    spoken = _number_to_russian(raw_number)

    if not is_percent:
        return spoken

    if "." in raw_number or "," in raw_number:
        return f"{spoken} процента"
    return f"{spoken} {_percent_form(raw_number)}"


def _number_to_russian(token: str) -> str:
    sign = ""
    number = token
    if number.startswith(("+", "-")):
        sign = "плюс" if number[0] == "+" else "минус"
        number = number[1:]

    if not number:
        return sign

    if "." in number or "," in number:
        integer_part, fraction_part = re.split(r"[.,]", number, maxsplit=1)
        integer_words = _integer_to_russian(integer_part or "0")
        fraction_words = " ".join(_DIGIT_WORDS[digit] for digit in fraction_part if digit.isdigit())
        parts = [part for part in (sign, integer_words, "запятая", fraction_words) if part]
        return " ".join(parts)

    integer_words = _integer_to_russian(number)
    return " ".join(part for part in (sign, integer_words) if part)


def _integer_to_russian(number: str) -> str:
    digits = number.lstrip("0")
    if not digits:
        return "ноль"

    if len(number) > 1 and number.startswith("0"):
        return _digits_to_russian(number)

    groups: list[int] = []
    remaining = digits
    while remaining:
        groups.append(int(remaining[-3:]))
        remaining = remaining[:-3]

    if len(groups) > len(_SCALE_FORMS):
        return _digits_to_russian(digits)

    words: list[str] = []
    for index in range(len(groups) - 1, -1, -1):
        group_value = groups[index]
        if group_value == 0:
            continue

        one, few, many, gender = _SCALE_FORMS[index]
        words.extend(_triplet_to_words(group_value, gender=gender))
        if index > 0:
            words.append(_plural_form(group_value, one=one, few=few, many=many))

    return " ".join(words)


def _digits_to_russian(number: str) -> str:
    return " ".join(_DIGIT_WORDS[digit] for digit in number if digit.isdigit())


def _triplet_to_words(value: int, *, gender: str) -> list[str]:
    words: list[str] = []
    hundreds = value // 100
    tens_units = value % 100

    if hundreds:
        words.append(_HUNDREDS[hundreds])

    if 10 <= tens_units <= 19:
        words.append(_TEENS[tens_units])
        return words

    tens = tens_units // 10
    units = tens_units % 10
    if tens:
        words.append(_TENS[tens])
    if units:
        units_map = _UNITS_FEM if gender == "fem" else _UNITS_MASC
        words.append(units_map[units])
    return words


def _plural_form(value: int, *, one: str, few: str, many: str) -> str:
    remainder_100 = value % 100
    remainder_10 = value % 10
    if 11 <= remainder_100 <= 14:
        return many
    if remainder_10 == 1:
        return one
    if 2 <= remainder_10 <= 4:
        return few
    return many


def _unit_form_for_number(number: str, *, one: str, few: str, many: str) -> str:
    if "." in number or "," in number:
        return few

    digits = re.sub(r"\D", "", number)
    if not digits:
        return many
    value = int(digits)
    return _plural_form(value, one=one, few=few, many=many)


def _percent_form(number: str) -> str:
    digits = re.sub(r"\D", "", number)
    if not digits:
        return "процентов"

    value = int(digits)
    return _plural_form(
        value,
        one="процент",
        few="процента",
        many="процентов",
    )
