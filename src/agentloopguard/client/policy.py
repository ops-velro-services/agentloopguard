"""Remote policy provider for AgentLoopGuard."""

import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional, Union

from agentloopguard.detectors import (
    BaseDetector,
    CostVelocityDetector,
    ExactRepeatDetector,
    LexicalSimilarityDetector,
    OscillationDetector,
)
from agentloopguard.exceptions import AgentLoopGuardError
from agentloopguard.guard import LoopGuard

logger = logging.getLogger(__name__)

DEFAULT_POLICY_ENDPOINT = "http://localhost:8000/v1/policies"


class RemotePolicyProvider:
    """Fetches and caches remote policy configurations from the Control Plane."""

    def __init__(
        self,
        policy_id: str,
        endpoint_url: str = DEFAULT_POLICY_ENDPOINT,
        api_key: Optional[str] = None,
        sync_interval_sec: float = 60.0,
        cache_file_path: Optional[Union[str, Path]] = None,
        timeout_sec: float = 5.0,
    ) -> None:
        if not policy_id or not isinstance(policy_id, str):
            raise ValueError("policy_id must be a non-empty string")
        if not endpoint_url or not isinstance(endpoint_url, str):
            raise ValueError("endpoint_url must be a non-empty string")
        if sync_interval_sec < 0:
            raise ValueError("sync_interval_sec must be non-negative")
        if timeout_sec <= 0:
            raise ValueError("timeout_sec must be greater than zero")

        self.policy_id = policy_id
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        self.sync_interval_sec = sync_interval_sec
        self.cache_file_path = Path(cache_file_path) if cache_file_path else None
        self.timeout_sec = timeout_sec

        self._last_sync_time: float = 0.0
        self._cached_etag: Optional[str] = None
        self._cached_policy: Optional[dict[str, Any]] = None
        self._lock = threading.Lock()

    def fetch_policy(self, force: bool = False) -> dict[str, Any]:
        """Fetch remote policy configuration via HTTP REST API.

        Uses ETag validation when available. Falls back to local disk or
        in-memory cache when offline or on server error.
        """
        with self._lock:
            now = time.time()
            if (
                not force
                and self._cached_policy
                and (now - self._last_sync_time) < self.sync_interval_sec
            ):
                return self._cached_policy

            # Build URL: append policy_id if not already present in endpoint_url path
            url = self.endpoint_url.rstrip("/")
            if not url.endswith(f"/{self.policy_id}"):
                url = f"{url}/{self.policy_id}"

            headers = {
                "User-Agent": "AgentLoopGuard-SDK/0.1.0",
                "Accept": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            if self._cached_etag:
                headers["If-None-Match"] = self._cached_etag

            req = urllib.request.Request(url, headers=headers, method="GET")

            try:
                with urllib.request.urlopen(req, timeout=self.timeout_sec) as response:
                    status = response.status
                    if status == 200:
                        raw_body = response.read().decode("utf-8")
                        parsed = json.loads(raw_body)
                        if not isinstance(parsed, dict):
                            raise AgentLoopGuardError(
                                f"Remote policy response for '{self.policy_id}' "
                                "must be a JSON object"
                            )
                        policy_data: dict[str, Any] = parsed
                        etag = response.headers.get("ETag") or response.headers.get("etag")
                        if etag:
                            self._cached_etag = etag

                        self._cached_policy = policy_data
                        self._last_sync_time = time.time()

                        if self.cache_file_path:
                            try:
                                self.cache_file_path.parent.mkdir(parents=True, exist_ok=True)
                                tmp_path = self.cache_file_path.with_suffix(".tmp")
                                with open(tmp_path, "w", encoding="utf-8") as f:
                                    json.dump(policy_data, f, indent=2)
                                os.replace(tmp_path, self.cache_file_path)
                            except Exception as cache_err:
                                logger.warning(f"Failed to write policy cache file: {cache_err}")

                        return policy_data
            except urllib.error.HTTPError as http_err:
                if http_err.code == 304:
                    self._last_sync_time = time.time()
                    if self._cached_policy:
                        return self._cached_policy
                    cached = self._read_cache_file()
                    if cached:
                        self._cached_policy = cached
                        return cached
                logger.warning(f"HTTP error fetching remote policy '{self.policy_id}': {http_err}")
            except Exception as net_err:
                logger.warning(
                    f"Network error fetching remote policy '{self.policy_id}': {net_err}"
                )

            # Fallback strategy when remote request fails
            if self._cached_policy:
                logger.info(f"Using in-memory cached policy for '{self.policy_id}'")
                return self._cached_policy

            cached_disk = self._read_cache_file()
            if cached_disk:
                logger.info(f"Using disk-cached policy for '{self.policy_id}'")
                self._cached_policy = cached_disk
                return cached_disk

            raise AgentLoopGuardError(
                f"Failed to fetch remote policy '{self.policy_id}' and no local cache is available."
            )

    def get_policy(self, force: bool = False) -> dict[str, Any]:
        """Get cached policy or fetch fresh copy if sync interval expired."""
        return self.fetch_policy(force=force)

    def get_cached_policy(self) -> Optional[dict[str, Any]]:
        """Retrieve currently cached policy without initiating network calls."""
        with self._lock:
            if self._cached_policy:
                return self._cached_policy
            return self._read_cache_file()

    def _read_cache_file(self) -> Optional[dict[str, Any]]:
        if self.cache_file_path and self.cache_file_path.exists():
            try:
                with open(self.cache_file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception as err:
                logger.warning(f"Failed to read policy cache file '{self.cache_file_path}': {err}")
        return None

    def create_guard(self, **override_kwargs: Any) -> LoopGuard:
        """Construct a LoopGuard instance pre-configured from remote policy rules."""
        policy = self.get_policy()
        rules = policy.get("rules", {})
        budget_cfg = rules.get("budget", {})
        detector_cfg = rules.get("detectors", {})
        alert_mode = rules.get("alert_mode", "raise")

        guard_kwargs: dict[str, Any] = {
            "max_iterations": budget_cfg.get("max_iterations"),
            "max_cost_usd": budget_cfg.get("max_cost_usd"),
            "max_tokens": budget_cfg.get("max_tokens"),
            "max_duration_seconds": budget_cfg.get("max_duration_seconds"),
            "unknown_model_policy": budget_cfg.get("unknown_model_policy"),
            "on_alert": alert_mode,
        }

        # Build detectors tuple
        detectors: list[BaseDetector] = []
        if isinstance(detector_cfg, dict):
            if detector_cfg.get("exact_repeat", {}).get("enabled", True):
                n = detector_cfg.get("exact_repeat", {}).get("max_repeats", 3)
                detectors.append(ExactRepeatDetector(n=n))

            lex_cfg = detector_cfg.get("lexical_similarity", {})
            if lex_cfg.get("enabled", True):
                thresh = lex_cfg.get("similarity_threshold", 0.92)
                window = lex_cfg.get("history_window", 3)
                detectors.append(LexicalSimilarityDetector(threshold=thresh, n=window))

            cost_vel_cfg = detector_cfg.get("cost_velocity", {})
            if cost_vel_cfg.get("enabled", True):
                max_vel = cost_vel_cfg.get("max_cost_velocity_usd_per_min", 2.0)
                detectors.append(CostVelocityDetector(max_usd_per_min=max_vel))

            if detector_cfg.get("oscillation", {}).get("enabled", True):
                min_cycles = detector_cfg.get("oscillation", {}).get("min_repeats", 3)
                detectors.append(OscillationDetector(min_cycles=min_cycles))

        if detectors:
            guard_kwargs["detectors"] = detectors

        # Caller override arguments
        guard_kwargs.update(override_kwargs)

        return LoopGuard(**guard_kwargs)
