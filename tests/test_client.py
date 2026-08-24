"""Unit tests for RemotePolicyProvider and WebhookExporter using mock HTTP responses."""

import json
import tempfile
import urllib.error
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from agentloopguard.client import RemotePolicyProvider, WebhookExporter
from agentloopguard.detectors import DetectionResult
from agentloopguard.exceptions import AgentLoopGuardError
from agentloopguard.guard import LoopGuard
from agentloopguard.schema import TelemetryEvent


class DummyResponse:
    def __init__(self, status: int, body: bytes, headers: dict[str, str] | None = None):
        self.status = status
        self._body = body
        self.headers = headers or {}

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "DummyResponse":
        return self

    def __exit__(self, *args: Any) -> None:
        pass


SAMPLE_POLICY_DATA = {
    "schema_version": 1,
    "policy_id": "pol_test_123",
    "organization_id": "org_test",
    "rules": {
        "budget": {
            "max_iterations": 15,
            "max_cost_usd": 10.0,
            "max_tokens": 100000,
            "max_duration_seconds": 120,
            "unknown_model_policy": "fail_closed",
        },
        "detectors": {
            "exact_repeat": {"enabled": True, "max_repeats": 4},
            "lexical_similarity": {
                "enabled": True,
                "similarity_threshold": 0.85,
                "history_window": 3,
            },
            "cost_velocity": {"enabled": True, "max_cost_velocity_usd_per_min": 3.0},
            "oscillation": {"enabled": True, "min_repeats": 2},
        },
        "alert_mode": "raise",
    },
}


def test_remote_policy_provider_fetch_and_cache() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = Path(tmpdir) / "policy_cache.json"
        provider = RemotePolicyProvider(
            policy_id="pol_test_123",
            endpoint_url="http://localhost:8000/v1/policies",
            sync_interval_sec=0.1,
            cache_file_path=cache_file,
        )

        body_bytes = json.dumps(SAMPLE_POLICY_DATA).encode("utf-8")
        resp_200 = DummyResponse(200, body_bytes, {"ETag": '"v1_etag"'})

        with patch("urllib.request.urlopen", return_value=resp_200) as mock_urlopen:
            policy = provider.fetch_policy()
            assert policy["policy_id"] == "pol_test_123"
            assert policy["rules"]["budget"]["max_iterations"] == 15
            assert cache_file.exists()
            mock_urlopen.assert_called_once()

        # Test 304 Not Modified
        http_304 = urllib.error.HTTPError("http://localhost", 304, "Not Modified", {}, None)  # type: ignore[arg-type]
        with patch("urllib.request.urlopen", side_effect=http_304):
            policy_cached = provider.fetch_policy(force=True)
            assert policy_cached["rules"]["budget"]["max_iterations"] == 15


def test_remote_policy_provider_offline_fallback() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = Path(tmpdir) / "policy_cache.json"
        cache_data = {"policy_id": "pol_offline", "rules": {"budget": {"max_iterations": 99}}}
        cache_file.write_text(json.dumps(cache_data))

        provider = RemotePolicyProvider(
            policy_id="pol_offline",
            endpoint_url="http://localhost:8000/v1/policies",
            cache_file_path=cache_file,
        )

        conn_err = urllib.error.URLError("Connection refused")
        with patch("urllib.request.urlopen", side_effect=conn_err):
            policy = provider.fetch_policy()
            assert policy["policy_id"] == "pol_offline"
            assert policy["rules"]["budget"]["max_iterations"] == 99


def test_remote_policy_provider_offline_no_cache_error() -> None:
    provider = RemotePolicyProvider(
        policy_id="pol_missing",
        endpoint_url="http://localhost:8000/v1/policies",
        cache_file_path=Path("/nonexistent/file/path.json"),
    )
    conn_err = urllib.error.URLError("Connection refused")
    with (
        patch("urllib.request.urlopen", side_effect=conn_err),
        pytest.raises(AgentLoopGuardError, match="Failed to fetch remote policy"),
    ):
        provider.fetch_policy()


def test_remote_policy_provider_create_guard() -> None:
    provider = RemotePolicyProvider(
        policy_id="pol_test_123",
        endpoint_url="http://localhost:8000/v1/policies",
    )
    body_bytes = json.dumps(SAMPLE_POLICY_DATA).encode("utf-8")
    resp_200 = DummyResponse(200, body_bytes)

    with patch("urllib.request.urlopen", return_value=resp_200):
        guard = provider.create_guard()
        assert guard._budget_config.max_iterations == 15
        assert guard._budget_config.max_cost_usd == 10.0
        assert len(guard.detectors) == 4


def test_webhook_exporter_detection() -> None:
    exporter = WebhookExporter(
        webhook_url="http://localhost:8000/v1/webhooks",
        secret="super_secret_key",
        organization_id="org_test",
        project_id="proj_test",
        async_send=False,
    )

    result = DetectionResult(
        detector_name="ExactRepeatDetector",
        confidence=1.0,
        description="Repeated tool call 3 times.",
        pattern_details={"tool_name": "db_query"},
        detector_id="exact_repeat",
        session_id="sess_123",
    )

    resp_202 = DummyResponse(202, b'{"status": "accepted"}')
    with patch("urllib.request.urlopen", return_value=resp_202) as mock_urlopen:
        exporter.export_detection(result, action_taken="session_terminated")

        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "http://localhost:8000/v1/webhooks"
        sig = req.get_header("X-agentloopguard-signature") or req.get_header(
            "X-AgentLoopGuard-Signature"
        )
        assert sig and sig.startswith("t=") and ",v1=" in sig

        payload = json.loads(req.data.decode("utf-8"))
        assert payload["event_type"] == "detection.loop_trapped"
        assert payload["organization_id"] == "org_test"
        assert payload["project_id"] == "proj_test"
        assert payload["session_id"] == "sess_123"
        assert payload["detection"]["detector_id"] == "exact_repeat"


def test_webhook_exporter_telemetry_event() -> None:
    exporter = WebhookExporter(
        webhook_url="http://localhost:8000/v1/webhooks",
        organization_id="org_test",
        async_send=False,
    )

    event = TelemetryEvent(
        name="agentloopguard.step",
        timestamp=1700000000.0,
        attributes={"agentloopguard.model": "gpt-4o"},
    )

    resp_202 = DummyResponse(202, b'{"status": "accepted"}')
    with patch("urllib.request.urlopen", return_value=resp_202) as mock_urlopen:
        exporter(event)

        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["event_type"] == "agentloopguard.step"
        assert payload["attributes"]["agentloopguard.model"] == "gpt-4o"


def test_webhook_exporter_integration_with_guard() -> None:
    exporter = WebhookExporter(
        webhook_url="http://localhost:8000/v1/webhooks",
        async_send=False,
    )

    guard = LoopGuard(
        max_iterations=2,
        on_alert="log",
        event_exporter=exporter,
    )

    resp_202 = DummyResponse(202, b'{"status": "accepted"}')
    with patch("urllib.request.urlopen", return_value=resp_202) as mock_urlopen:
        session = guard.session()
        session.record({"model": "gpt-4o", "input_tokens": 10, "output_tokens": 10})
        assert mock_urlopen.called
