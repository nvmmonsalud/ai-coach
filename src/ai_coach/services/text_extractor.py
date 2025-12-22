from __future__ import annotations

import logging
from pathlib import Path

from docx import Document
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class TextExtractor:
    def extract(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self._extract_pdf(path)
        if suffix in {".doc", ".docx"}:
            return self._extract_docx(path)
        logger.info("Falling back to plain text read for %s", path)
        return path.read_text(encoding="utf-8", errors="ignore")

    def _extract_pdf(self, path: Path) -> str:
        reader = PdfReader(path)
        texts: list[str] = []
        for page in reader.pages:
            try:
                texts.append(page.extract_text() or "")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to extract PDF page text: %s", exc)
        return "\n".join(texts)

    def _extract_docx(self, path: Path) -> str:
        document = Document(path)
        return "\n".join(para.text for para in document.paragraphs)
