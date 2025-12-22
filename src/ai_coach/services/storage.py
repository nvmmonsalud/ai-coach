from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from ai_coach.config.settings import settings


class StorageClient:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root or settings.storage_root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_obj: BinaryIO, filename: str) -> Path:
        destination = self.root / filename
        with open(destination, "wb") as target:
            while chunk := file_obj.read(8192):
                target.write(chunk)
        return destination

    def read_text(self, path: Path) -> str:
        return Path(path).read_text(encoding="utf-8")
