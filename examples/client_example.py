"""Example demonstrating RemotePolicyProvider and WebhookExporter usage."""

import json
from unittest.mock import patch

from agentloopguard.client import RemotePolicyProvider, WebhookExporter


class MockHttpResponse:
    def __init__(self, status: int, body: bytes):
        self.status = status
        self._body = body
        self.headers = {"ETag": '"v1_etag"'}

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "MockHttpResponse":
        return self

    def __exit__(self, *args: str) -> None:
        pass


def main() -> None:
    policy_payload = {
        "schema_version": 1,
        "policy_id": "pol_prod_enterprise",
        "organization_id": "org_velro",
        "rules": {
            "budget": {
                "max_iterations": 10,
                "max_cost_usd": 5.0,
            },
            "detectors": {
                "exact_repeat": {"enabled": True, "max_repeats": 3},
            },
            "alert_mode": "log",
        },
    }

    mock_resp = MockHttpResponse(200, json.dumps(policy_payload).encode("utf-8"))

    with patch("urllib.request.urlopen", return_value=mock_resp):
        print("1. Initializing RemotePolicyProvider...")
        provider = RemotePolicyProvider(
            policy_id="pol_prod_enterprise",
            endpoint_url="http://localhost:8000/v1/policies",
        )

        print("2. Constructing LoopGuard from remote policy...")
        guard = provider.create_guard()
        print(f"   Max iterations limit: {guard._budget_config.max_iterations}")

        print("3. Configuring WebhookExporter...")
        webhook_exporter = WebhookExporter(
            webhook_url="http://localhost:8000/v1/webhooks",
            secret="my_hmac_secret_key",
            organization_id="org_velro",
            async_send=False,
        )

        guard.event_exporter = webhook_exporter

        session = guard.session()
        print("4. Recording step event...")
        session.record(
            {
                "model": "gpt-4o",
                "input_tokens": 100,
                "output_tokens": 50,
                "tool_name": "search_db",
                "tool_args": {"query": "SELECT * FROM users"},
                "output": "10 rows returned",
            }
        )
        print("   Step recorded successfully and webhook dispatched!")


if __name__ == "__main__":
    main()
