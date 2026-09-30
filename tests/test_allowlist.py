"""
Tests para backend.security.allowlist
"""
import os
from unittest import mock

from backend.security.allowlist import DEFAULT_HOSTS, get_allowed_hosts, is_host_allowed


def test_default_hosts_when_env_empty():
    with mock.patch.dict(os.environ, {}, clear=True):
        hosts = get_allowed_hosts()
    assert "youtube.com" in hosts
    assert hosts == DEFAULT_HOSTS


def test_hosts_from_env(monkeypatch):
    monkeypatch.setenv("ALLOWED_HOSTS", "example.com, sub.example.org")
    hosts = get_allowed_hosts()
    assert "example.com" in hosts
    assert "sub.example.org" in hosts
    # minúsculas
    assert "EXAMPLE.COM" not in hosts


def test_is_host_allowed_exact():
    assert is_host_allowed("https://www.youtube.com/watch?v=abc") is True


def test_is_host_allowed_subdomain():
    assert is_host_allowed("https://m.youtube.com/watch?v=abc") is True


def test_is_host_allowed_rejects_unknown():
    assert is_host_allowed("https://evil.example.com/x") is False


def test_is_host_allowed_rejects_malformed():
    assert is_host_allowed("not a url") is False
    assert is_host_allowed("") is False


def test_is_host_allowed_rejects_non_http():
    assert is_host_allowed("file:///etc/passwd") is False
    assert is_host_allowed("ftp://youtube.com/") is False