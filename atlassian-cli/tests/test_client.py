"""Tests for client module (mocked HTTP)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import httpx
import pytest

from atlassian_cli.client import _request, _handle_error


class TestRequest:
    def _mock_client(self, status_code=200, json_body=None, content=b"{}"):
        """Create a mock httpx client that returns a canned response."""
        response = httpx.Response(
            status_code=status_code,
            content=json.dumps(json_body).encode() if json_body is not None else content,
            headers={"content-type": "application/json"},
            request=httpx.Request("GET", "https://test.atlassian.net/test"),
        )
        client = MagicMock(spec=httpx.Client)
        client.request.return_value = response
        return client

    def test_successful_get(self):
        client = self._mock_client(json_body={"key": "PROJ-1"})
        result = _request(client, "GET", "/rest/api/3/issue/PROJ-1")
        assert result == {"key": "PROJ-1"}
        client.request.assert_called_once()

    def test_strips_none_params(self):
        client = self._mock_client(json_body={})
        _request(client, "GET", "/test", params={"a": "1", "b": None, "c": "3"})
        call_kwargs = client.request.call_args
        assert call_kwargs.kwargs["params"] == {"a": "1", "c": "3"}

    def test_204_returns_none(self):
        response = httpx.Response(
            status_code=204,
            content=b"",
            request=httpx.Request("DELETE", "https://test.atlassian.net/test"),
        )
        client = MagicMock(spec=httpx.Client)
        client.request.return_value = response
        assert _request(client, "DELETE", "/test") is None

    def test_empty_content_returns_none(self):
        response = httpx.Response(
            status_code=200,
            content=b"",
            request=httpx.Request("PUT", "https://test.atlassian.net/test"),
        )
        client = MagicMock(spec=httpx.Client)
        client.request.return_value = response
        assert _request(client, "PUT", "/test") is None

    def test_error_raises_system_exit(self):
        client = self._mock_client(
            status_code=404,
            json_body={"errorMessages": ["Issue does not exist"]},
        )
        with pytest.raises(SystemExit):
            _request(client, "GET", "/rest/api/3/issue/NOPE-1")

    def test_401_raises_system_exit(self):
        client = self._mock_client(
            status_code=401,
            json_body={"errorMessages": ["Unauthorized"]},
        )
        with pytest.raises(SystemExit):
            _request(client, "GET", "/test")

    def test_passes_json_body(self):
        client = self._mock_client(json_body={"id": "123"})
        payload = {"fields": {"summary": "test"}}
        _request(client, "POST", "/test", json=payload)
        call_kwargs = client.request.call_args
        assert call_kwargs.kwargs["json"] == payload


class TestHandleError:
    def test_error_with_messages(self, capsys):
        resp = httpx.Response(
            status_code=400,
            content=json.dumps({"errorMessages": ["Bad JQL", "Invalid field"]}).encode(),
            headers={"content-type": "application/json"},
            request=httpx.Request("POST", "https://test.atlassian.net/test"),
        )
        with pytest.raises(SystemExit):
            _handle_error(resp)
        err = capsys.readouterr().err
        assert "Bad JQL; Invalid field" in err

    def test_error_with_errors_dict(self, capsys):
        resp = httpx.Response(
            status_code=400,
            content=json.dumps({"errorMessages": [], "errors": {"summary": "required"}}).encode(),
            headers={"content-type": "application/json"},
            request=httpx.Request("POST", "https://test.atlassian.net/test"),
        )
        with pytest.raises(SystemExit):
            _handle_error(resp)
        err = capsys.readouterr().err
        assert "summary" in err

    def test_error_with_hint(self, capsys):
        resp = httpx.Response(
            status_code=401,
            content=json.dumps({"errorMessages": ["Unauthorized"]}).encode(),
            headers={"content-type": "application/json"},
            request=httpx.Request("GET", "https://test.atlassian.net/test"),
        )
        with pytest.raises(SystemExit):
            _handle_error(resp)
        err = capsys.readouterr().err
        assert "atlassian-cli auth login" in err

    def test_error_non_json_body(self, capsys):
        resp = httpx.Response(
            status_code=500,
            content=b"Internal Server Error",
            headers={"content-type": "text/plain"},
            request=httpx.Request("GET", "https://test.atlassian.net/test"),
        )
        with pytest.raises(SystemExit):
            _handle_error(resp)
        err = capsys.readouterr().err
        assert "500" in err
