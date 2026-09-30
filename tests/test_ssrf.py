"""
Tests para backend.security.ssrf
"""
import pytest

from backend.security.ssrf import SSRFError, assert_safe_url


def test_https_youtube_allowed():
    # No debe lanzar — host en allowlist, IP pública esperada.
    assert_safe_url("https://www.youtube.com/watch?v=abc")


def test_rejects_ftp_scheme():
    with pytest.raises(SSRFError, match="Scheme not allowed"):
        assert_safe_url("ftp://youtube.com/file")


def test_rejects_file_scheme():
    with pytest.raises(SSRFError, match="Scheme not allowed"):
        assert_safe_url("file:///etc/passwd")


def test_rejects_host_not_in_allowlist():
    with pytest.raises(SSRFError, match="not in allowlist"):
        assert_safe_url("https://evil.example.com/")


def test_rejects_loopback_via_ip(monkeypatch):
    # Simulamos que el host "public.youtube.com" resuelve a 127.0.0.1 (DNS rebinding).
    import backend.security.ssrf as ssrf_mod

    monkeypatch.setattr(ssrf_mod.socket, "getaddrinfo", lambda *a, **kw: [(2, 1, 6, "", ("127.0.0.1", 0))])
    # Quitamos la allowlist para forzar que la verificación pase el filtro de host
    monkeypatch.setenv("ALLOWED_HOSTS", "public.youtube.com")
    with pytest.raises(SSRFError, match="private IP"):
        assert_safe_url("https://public.youtube.com/watch?v=x")


def test_rejects_private_ip(monkeypatch):
    import backend.security.ssrf as ssrf_mod

    monkeypatch.setattr(ssrf_mod.socket, "getaddrinfo", lambda *a, **kw: [(2, 1, 6, "", ("192.168.1.1", 0))])
    monkeypatch.setenv("ALLOWED_HOSTS", "leak.test")
    with pytest.raises(SSRFError, match="private IP"):
        assert_safe_url("https://leak.test/")


def test_rejects_link_local(monkeypatch):
    import backend.security.ssrf as ssrf_mod

    monkeypatch.setattr(ssrf_mod.socket, "getaddrinfo", lambda *a, **kw: [(2, 1, 6, "", ("169.254.169.254", 0))])
    monkeypatch.setenv("ALLOWED_HOSTS", "aws.test")
    with pytest.raises(SSRFError, match="private IP"):
        assert_safe_url("https://aws.test/latest/meta-data/")


def test_rejects_missing_host():
    with pytest.raises(SSRFError):
        assert_safe_url("https:///path")