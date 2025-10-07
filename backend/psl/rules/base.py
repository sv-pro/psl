from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel

class LintError(BaseModel):
    """Represents a linting error"""
    rule: str
    severity: str  # "error" | "warning" | "info"
    message: str
    suggestion: str

class Rule(ABC):
    """Base class for linting rules"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Rule identifier"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description"""
        pass

    @abstractmethod
    def check(self, ir) -> List[LintError]:
        """Check IR and return errors"""
        pass
