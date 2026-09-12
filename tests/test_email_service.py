import json
from unittest.mock import patch, MagicMock
import pytest
from backend.services.email_service import (
    BrevoEmailTransport,
    EmailService,
    FakeEmailTransport,
)
from backend.config import AppConfig
from backend.routers import auth


def test_brevo_transport_sends_correct_payload():
    transport = BrevoEmailTransport(
        api_key="test-brevo-key-12345",
        sender_email="alerts@jobhelper.guru",
        sender_name="JobHelperGuru Alerts",
    )

    mock_resp = MagicMock()
    mock_resp.status = 201
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        transport.send(
            recipient="candidate@example.com",
            subject="Welcome to JobHelperGuru",
            text_body="Hello candidate!",
        )

        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://api.brevo.com/v3/smtp/email"
        assert req.headers["Api-key"] == "test-brevo-key-12345"
        assert req.headers["Content-type"] == "application/json"

        body = json.loads(req.data.decode("utf-8"))
        assert body["sender"]["email"] == "alerts@jobhelper.guru"
        assert body["sender"]["name"] == "JobHelperGuru Alerts"
        assert body["to"] == [{"email": "candidate@example.com"}]
        assert body["subject"] == "Welcome to JobHelperGuru"
        assert body["textContent"] == "Hello candidate!"


def test_brevo_transport_handles_http_errors():
    import urllib.error
    transport = BrevoEmailTransport(api_key="invalid-key")

    mock_err = urllib.error.HTTPError(
        url="https://api.brevo.com/v3/smtp/email",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=MagicMock(read=lambda: b'{"message": "Key not valid"}'),
    )

    with patch("urllib.request.urlopen", side_effect=mock_err):
        with pytest.raises(RuntimeError, match="Brevo API error"):
            transport.send(
                recipient="user@example.com",
                subject="Test",
                text_body="Test",
            )


def test_create_email_service_selects_brevo_when_configured(monkeypatch):
    mock_cfg = AppConfig(
        brevo_api_key="brevo-api-key-xyz",
        brevo_sender_email="sender@jobhelper.guru",
        brevo_sender_name="My App",
    )
    monkeypatch.setattr("backend.routers.auth.load_config", lambda: mock_cfg)

    service = auth._create_email_service()
    assert isinstance(service.transport, BrevoEmailTransport)
    assert service.transport.api_key == "brevo-api-key-xyz"
    assert service.transport.sender_email == "sender@jobhelper.guru"
    assert service.transport.sender_name == "My App"
