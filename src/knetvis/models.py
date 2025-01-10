import re
from dataclasses import dataclass
from typing import ClassVar, Pattern


@dataclass
class Target:
    namespace: str
    kind: str
    name: str
    TARGET_PATTERN: ClassVar[Pattern] = re.compile(r"^(?:([^/]+)/)?([^/]+)/([^/]+)$")

    @classmethod
    def from_str(cls, target_str: str) -> "Target":
        match = cls.TARGET_PATTERN.match(target_str)
        if not match:
            raise ValueError(
                f"Invalid target format: {target_str}. "
                "Expected format: [namespace/]kind/name"
            )
        namespace, kind, name = match.groups()
        return cls(namespace=namespace or "default", kind=kind, name=name)

    def __str__(self) -> str:
        """Return string representation in format namespace/kind/name"""
        return f"{self.namespace}/{self.kind}/{self.name}"
