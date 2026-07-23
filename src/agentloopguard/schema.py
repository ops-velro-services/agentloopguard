"""Versioned public models for recorded guard steps and detections."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Optional

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StepEvent:
    """A normalized step recorded by a :class:`~agentloopguard.GuardSession`.

    ``extra`` retains caller-defined dictionary fields so existing integrations
    can continue passing richer step dictionaries without losing data.
    """

    session_id: str
    timestamp: float
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    tool_name: Optional[str] = None
    tool_args: Any = None
    output: Any = None
    exception: Optional[Mapping[str, str]] = None
    extra: Mapping[str, Any] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Return the legacy dictionary shape, augmented with schema fields."""
        result = dict(self.extra)
        result.update(
            {
                "schema_version": self.schema_version,
                "session_id": self.session_id,
                "timestamp": self.timestamp,
                "model": self.model,
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "cost_usd": self.cost_usd,
            }
        )
        if self.tool_name is not None:
            result["tool_name"] = self.tool_name
        if self.tool_args is not None:
            result["tool_args"] = self.tool_args
        if self.output is not None:
            result["output"] = self.output
        if self.exception is not None:
            result["exception"] = dict(self.exception)
        return result


@dataclass(frozen=True)
class DetectionResult:
    """A versioned detector result with legacy fields and a dictionary adapter."""

    detector_name: str
    confidence: float
    description: str
    pattern_details: Mapping[str, Any]
    detector_id: str = "unknown"
    measured_values: Mapping[str, Any] = field(default_factory=dict)
    recommended_action: str = "stop"
    session_id: Optional[str] = None
    timestamp: Optional[float] = None
    schema_version: int = SCHEMA_VERSION

    def with_context(self, session_id: str, timestamp: float) -> "DetectionResult":
        """Return this result associated with the session and triggering step."""
        return DetectionResult(
            detector_name=self.detector_name,
            confidence=self.confidence,
            description=self.description,
            pattern_details=dict(self.pattern_details),
            detector_id=self.detector_id,
            measured_values=dict(self.measured_values),
            recommended_action=self.recommended_action,
            session_id=session_id,
            timestamp=timestamp,
            schema_version=self.schema_version,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the stable public event schema."""
        return {
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "detector_id": self.detector_id,
            "detector_name": self.detector_name,
            "confidence": self.confidence,
            "description": self.description,
            "measured_values": dict(self.measured_values),
            "recommended_action": self.recommended_action,
            "pattern_details": dict(self.pattern_details),
        }

    def to_legacy_dict(self) -> dict[str, Any]:
        """Return the pre-schema detector dictionary shape for integrations."""
        return {
            "detector_name": self.detector_name,
            "confidence": self.confidence,
            "description": self.description,
            "pattern_details": dict(self.pattern_details),
        }


@dataclass(frozen=True)
class TelemetryEvent:
    """A zero-dependency event ready for an OpenTelemetry adapter.

    ``attributes`` intentionally contains only scalar values. This makes the
    event safe to pass directly to common OpenTelemetry event and log APIs,
    while the richer :class:`StepEvent` and :class:`DetectionResult` remain
    available through their dictionary adapters.
    """

    name: str
    timestamp: float
    attributes: Mapping[str, Any]
