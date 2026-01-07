"""
Fnord Data Models

The fnord is a mysterious thing - here we define its sacred shape.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Any, Tuple
import json


@dataclass
class FnordSighting:
    """
    A fnord sighting record.

    The fnord appears when you least expect it. This is how we capture it.
    All fields are sacred, but only when and summary are required by law of fnords.

    Attributes:
        id: The sacred ID (database-assigned, 23 is lucky)
        when: When the fnord appeared (ISO8601 format string)
        where_place_name: Optional human-readable location description
        source: Where the fnord was found (News, Walk, Code, Dream, etc.)
        summary: Brief description of the fnord sighting
        notes: Optional JSON-serializable dict for additional metadata
        logical_fallacies: Optional list of logical fallacy names (e.g., ["ad hominem"])
    """

    # Database fields
    id: Optional[int] = None

    # When the fnord revealed itself
    when: str = ""

    # Where the fnord appeared (text description - whatever the caller considers location)
    where_place_name: Optional[str] = None

    # Source of the fnord sighting
    source: str = ""

    # Summary of the fnord (what was it doing there?)
    summary: str = ""

    # Additional notes (JSON blob)
    notes: Optional[dict[str, Any]] = None

    # List of logical fallacies (JSON array)
    logical_fallacies: Optional[list[str]] = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert fnord to dictionary.

        Returns:
            dict: The fnord, as a dict (for JSON serialization)
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FnordSighting":
        """
        Create fnord from dictionary.

        Args:
            data: Dictionary representation of a fnord

        Returns:
            FnordSighting: A new fnord instance
        """
        return cls(**data)

    def validate(self) -> list[str]:
        """
        Validate the fnord sighting.

        Returns:
            list: List of error messages (empty if fnord is valid)
        """
        errors = []

        # when is required and must be ISO8601
        if not self.when:
            errors.append("when: This field is required (fnords must have a time!)")
        else:
            try:
                datetime.fromisoformat(self.when.replace("Z", "+00:00"))
            except ValueError:
                errors.append("when: Must be in ISO8601 format (e.g., 2026-01-07T14:23:00Z)")

        # source is required
        if not self.source:
            errors.append("source: This field is required (where did the fnord come from?)")

        # summary is required
        if not self.summary:
            errors.append("summary: This field is required (describe the fnord! what did it do?)")

        # Validate notes is JSON-serializable if present
        if self.notes is not None:
            try:
                json.dumps(self.notes)
            except (TypeError, ValueError):
                errors.append("notes: Must be JSON-serializable (fnords love JSON)")

        return errors

    def __str__(self) -> str:
        """
        String representation of fnord.

        Returns:
            str: Human-readable fnord description
        """
        where = self.where_place_name or "Unknown location"

        return f"[{self.when}] {self.source}: {self.summary} @ {where}"

    def __repr__(self) -> str:
        """
        Developer representation of fnord.

        Returns:
            str: Unambiguous fnord representation
        """
        return f"FnordSighting(id={self.id}, when='{self.when}', source='{self.source}', summary='{self.summary[:30]}...')"
