"""Desktop application layer for the Windows GUI."""

from pdf_tts_ru.gui.models import DesktopFormState, DesktopInspectionSummary
from pdf_tts_ru.gui.service import DesktopAppService

__all__ = [
    "DesktopAppService",
    "DesktopFormState",
    "DesktopInspectionSummary",
]
