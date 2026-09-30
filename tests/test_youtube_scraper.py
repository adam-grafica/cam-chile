"""
Tests para backend.scraper.youtube_live

Mockea httpx para no depender de YouTube real.
"""

from unittest import mock

import httpx
import pytest

from backend.scraper import youtube_live


def test_video_public_returns_metadata():
    fake_resp = mock.Mock(status_code=200)
    fake_resp.json.return_value = {
        "title": "ALMA Live",
        "author_name": "ALMA Observatory",
        "thumbnail_url": "https://example.com/thumb.jpg",
    }
    with mock.patch.object(httpx, "Client") as MockClient:
        mock_ctx = mock.MagicMock()
        mock_ctx.__enter__.return_value.get.return_value = fake_resp
        MockClient.return_value = mock_ctx
        meta = youtube_live._is_video_public("https://www.youtube.com/watch?v=abc")
    assert meta["title"] == "ALMA Live"


def test_private_video_raises():
    fake_resp = mock.Mock(status_code=401)
    with mock.patch.object(httpx, "Client") as MockClient:
        mock_ctx = mock.MagicMock()
        mock_ctx.__enter__.return_value.get.return_value = fake_resp
        MockClient.return_value = mock_ctx
        with pytest.raises(youtube_live.YouTubePublicError, match="private"):
            youtube_live._is_video_public("https://www.youtube.com/watch?v=abc")


def test_not_found_raises():
    fake_resp = mock.Mock(status_code=404)
    with mock.patch.object(httpx, "Client") as MockClient:
        mock_ctx = mock.MagicMock()
        mock_ctx.__enter__.return_value.get.return_value = fake_resp
        MockClient.return_value = mock_ctx
        with pytest.raises(youtube_live.YouTubePublicError, match="not found"):
            youtube_live._is_video_public("https://www.youtube.com/watch?v=missing")


def test_verify_catalog_entry_skips_non_youtube():
    cam = {"stream_url": "https://example.com/stream", "stream_type": "hls"}
    out = youtube_live.verify_catalog_entry(cam)
    assert out is cam
    assert "verified_title" not in out


def test_verify_catalog_entry_updates_status():
    fake_resp = mock.Mock(status_code=200)
    fake_resp.json.return_value = {"title": "x", "author_name": "y"}
    with mock.patch.object(httpx, "Client") as MockClient:
        mock_ctx = mock.MagicMock()
        mock_ctx.__enter__.return_value.get.return_value = fake_resp
        MockClient.return_value = mock_ctx
        out = youtube_live.verify_catalog_entry(
            {
                "stream_url": "https://www.youtube.com/watch?v=a",
                "stream_type": "youtube",
            }
        )
    assert out["public_status"] == "declared_public"
    assert out["verified_title"] == "x"


def test_main_cli_success(monkeypatch, capsys):
    """CLI: video público → exit 0 + JSON en stdout."""
    fake_resp = mock.Mock(status_code=200)
    fake_resp.json.return_value = {"title": "ALMA Live", "author_name": "ALMA"}
    with mock.patch.object(httpx, "Client") as MockClient:
        mock_ctx = mock.MagicMock()
        mock_ctx.__enter__.return_value.get.return_value = fake_resp
        MockClient.return_value = mock_ctx
        monkeypatch.setattr(
            "sys.argv", ["youtube_live", "https://www.youtube.com/watch?v=x"]
        )
        rc = youtube_live.main()
    assert rc == 0
    captured = capsys.readouterr()
    assert "ALMA Live" in captured.out


def test_main_cli_private_video(monkeypatch):
    """CLI: video privado → exit 1."""
    fake_resp = mock.Mock(status_code=401)
    with mock.patch.object(httpx, "Client") as MockClient:
        mock_ctx = mock.MagicMock()
        mock_ctx.__enter__.return_value.get.return_value = fake_resp
        MockClient.return_value = mock_ctx
        monkeypatch.setattr(
            "sys.argv", ["youtube_live", "https://www.youtube.com/watch?v=priv"]
        )
        rc = youtube_live.main()
    assert rc == 1


def test_main_cli_not_found(monkeypatch):
    """CLI: video no encontrado → exit 1."""
    fake_resp = mock.Mock(status_code=404)
    with mock.patch.object(httpx, "Client") as MockClient:
        mock_ctx = mock.MagicMock()
        mock_ctx.__enter__.return_value.get.return_value = fake_resp
        MockClient.return_value = mock_ctx
        monkeypatch.setattr(
            "sys.argv", ["youtube_live", "https://www.youtube.com/watch?v=missing"]
        )
        rc = youtube_live.main()
    assert rc == 1


def test_main_cli_network_error(monkeypatch):
    """CLI: error de red → exit 1."""
    with mock.patch.object(httpx, "Client") as MockClient:
        mock_ctx = mock.MagicMock()
        mock_ctx.__enter__.return_value.get.side_effect = httpx.ConnectError("no net")
        MockClient.return_value = mock_ctx
        monkeypatch.setattr(
            "sys.argv", ["youtube_live", "https://www.youtube.com/watch?v=x"]
        )
        rc = youtube_live.main()
    assert rc == 1
