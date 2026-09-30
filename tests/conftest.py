"""
Configuración común de pytest.
"""

import sys
from pathlib import Path

import pytest

# Permitir imports "from backend.x import ..."
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def _mock_dns_public(monkeypatch):
    """
    Por defecto, finge que todo host conocido resuelve a una IP pública.
    Los tests de SSRF (test_ssrf.py) sobreescriben este mock para casos maliciosos.
    """
    import backend.security.ssrf as ssrf_mod

    def fake_resolve(host, *args, **kwargs):
        return [(2, 1, 6, "", ("93.184.216.34", 0))]  # example.com IP pública

    monkeypatch.setattr(ssrf_mod.socket, "getaddrinfo", fake_resolve)
    yield
