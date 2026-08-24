"""Webhook exporter for AgentLoopGuard alert and telemetry notifications."""

import hashlib
import hmac
import json
import logging
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Union

from agentloopguard.detectors import DetectionResult
from agentloopguard.schema import TelemetryEvent

logger = logging.getLogger(__name__)


class WebhookExporter:
    """Exports detection and telemetry events to external webhooks via HTTP POST.

    Supports HMAC-SHA256 request signing via the `X-AgentLoopGuard-Signature` header.
    Can be dispatched asynchronously in non-blocking background threads or synchronously.
    """

    def __init__(
        self,
        webhook_url: str,
        secret: Optional[str] = None,
        organization_id: Optional[str] = None,
        project_id: Optional[str] = None,
        timeout_sec: float = 5.0,
        async_send: bool = True,
    ) -> None:
        if not webhook_url or not isinstance(webhook_url, str):
            raise ValueError("webhook_url must be a non-empty string")
        if timeout_sec <= 0:
            raise ValueError("timeout_sec must be greater than zero")

        self.webhook_url = webhook_url
        self.secret = secret
        self.organization_id = organization_id or ""
        self.project_id = project_id or ""
        self.timeout_sec = timeout_sec
        self.async_send = async_send

    def _sign_payload(self, timestamp: int, payload_str: str) -> str:
        if not self.secret:
            return ""
        sign_string = f"{timestamp}.{payload_str}".encode()
        signature = hmac.new(
            self.secret.encode(),
            sign_string,
            hashlib.sha256,
        ).hexdigest()
        return f"t={timestamp},v1={signature}"

    def send_payload(self, payload: dict[str, Any]) -> None:
        """Send a JSON payload dictionary to the webhook URL."""
        if self.async_send:
            thread = threading.Thread(
                target=self._send_payload_sync,
                args=(payload,),
                daemon=True,
            )
            thread.start()
        else:
            self._send_payload_sync(payload)

    def _send_payload_sync(self, payload: dict[str, Any]) -> None:
        try:
            payload_str = json.dumps(payload, separators=(",", ":"))
            payload_bytes = payload_str.encode("utf-8")
            timestamp = int(time.time())

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "AgentLoopGuard-SDK/0.1.0",
            }
            if self.secret:
                sig_header = self._sign_payload(timestamp, payload_str)
                headers["X-AgentLoopGuard-Signature"] = sig_header

            req = urllib.request.Request(
                self.webhook_url,
                data=payload_bytes,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                if resp.status not in (200, 201, 202, 204):
                    logger.warning(
                        f"Webhook delivery to {self.webhook_url} "
                        f"returned unexpected status: {resp.status}"
                    )
        except Exception as err:
            logger.warning(f"Webhook delivery to {self.webhook_url} failed: {err}")

    def export_detection(
        self,
        result: DetectionResult,
        session_id: str = "",
        action_taken: str = "alert_raised",
    ) -> None:
        """Format and dispatch a detection event to the configured webhook URL."""
        event_timestamp = (
            datetime.fromtimestamp(result.timestamp, tz=timezone.utc).isoformat()
            if result.timestamp
            else datetime.now(timezone.utc).isoformat()
        )
        payload: dict[str, Any] = {
            "event_id": f"evt_{uuid.uuid4().hex[:10]}",
            "event_type": "detection.loop_trapped",
            "timestamp": event_timestamp,
            "organization_id": self.organization_id,
            "project_id": self.project_id,
            "session_id": session_id or result.session_id or "",
            "detection": result.to_dict(),
            "action_taken": action_taken,
        }
        self.send_payload(payload)

    def export_telemetry(self, event: TelemetryEvent) -> None:
        """Dispatch a telemetry event to the configured webhook URL."""
        payload: dict[str, Any] = {
            "event_id": f"evt_{uuid.uuid4().hex[:10]}",
            "event_type": event.name,
            "timestamp": datetime.fromtimestamp(event.timestamp, tz=timezone.utc).isoformat(),
            "organization_id": self.organization_id,
            "project_id": self.project_id,
            "attributes": event.attributes,
        }
        self.send_payload(payload)

    def __call__(self, event: Union[TelemetryEvent, DetectionResult]) -> None:
        """Allows WebhookExporter to be passed directly as event_exporter or alert_callback."""
        if isinstance(event, DetectionResult):
            self.export_detection(event)
        elif isinstance(event, TelemetryEvent):
            self.export_telemetry(event)
        else:
            logger.warning(f"WebhookExporter received unsupported event type: {type(event)}")
