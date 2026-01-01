import json
import logging
import threading
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DatetimeEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


class JsonStore:
    """ACID-compliant JSON file store for simple persistence."""

    def __init__(self, filepath: Path, data_class: Type[T]):
        self.filepath = filepath
        self.data_class = data_class
        self.lock = threading.Lock()
        self.items: List[T] = self._load()

    def _load(self) -> List[T]:
        if not self.filepath.exists():
            return []
        with self.lock:
            if self.filepath.stat().st_size == 0:
                return []
            with self.filepath.open() as f:
                try:
                    raw_data = json.load(f)
                    for item in raw_data:
                        if "created_at" in item and isinstance(item["created_at"], str):
                            item["created_at"] = datetime.fromisoformat(item["created_at"])
                    return [self.data_class(**item) for item in raw_data]
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    logger.error("Failed to decode JSON from %s: %s", self.filepath, e)
                    return []

    def _save(self) -> None:
        with self.lock:
            temp_filepath = self.filepath.with_suffix(f".tmp.{threading.get_ident()}")
            with temp_filepath.open("w") as f:
                json.dump(
                    [asdict(item) if is_dataclass(item) else item for item in self.items],
                    f,
                    indent=2,
                    cls=DatetimeEncoder,
                )
            temp_filepath.rename(self.filepath)

    def add(self, item: T) -> None:
        with self.lock:
            self.items.append(item)
            self._save()

    def get_all(self) -> List[T]:
        with self.lock:
            return list(self.items)

    def replace_all(self, items: List[T]) -> None:
        with self.lock:
            self.items = items
            self._save()
