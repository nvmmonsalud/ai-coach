import re
from dataclasses import dataclass
from typing import Dict, List, Pattern


@dataclass
class PIIMatch:
    value: str
    label: str
    start: int
    end: int


class PIIGuard:
    """Detects and redacts common PII to keep prompts and logs safe."""

    def __init__(self) -> None:
        self.patterns: Dict[str, Pattern[str]] = {
            "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
            "phone": re.compile(r"\b\+?\d{1,2}[\s.-]?(?:\d{3}|\(\d{3}\))[\s.-]?\d{3}[\s.-]?\d{4}\b"),
            "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
        }

    def detect(self, text: str) -> List[PIIMatch]:
        matches: List[PIIMatch] = []
        for label, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                matches.append(
                    PIIMatch(value=match.group(0), label=label, start=match.start(), end=match.end())
                )
        return matches

    def redact(self, text: str) -> str:
        redacted = text
        for label, pattern in self.patterns.items():
            redacted = pattern.sub(f"[{label.upper()} REDACTED]", redacted)
        return redacted

    def sanitize_for_embeddings(self, text: str) -> str:
        """
        Ensure embeddings do not leak raw PII by redacting and replacing with labels.
        """
        return self.redact(text)

    def annotate(self, text: str) -> str:
        """Append detected PII labels to the end of a log line for auditing."""
        matches = self.detect(text)
        if not matches:
            return text
        labels = sorted({m.label for m in matches})
        return f"{self.redact(text)} [PII:{','.join(labels)}]"
