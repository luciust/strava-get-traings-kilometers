"""Credentials storage and management for Strava authentication."""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


CONFIG_DIR = Path.home() / ".config" / "strava_tui"
CONFIG_FILE = CONFIG_DIR / "credentials.json"
CACHE_DIR = CONFIG_DIR / "cache"


class CredentialsManager:
    """Manages secure storage of Strava tokens and session cookies."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """Load stored credentials from file."""
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self, data: Dict[str, Any]) -> None:
        """Save credentials to file with restricted permissions (0600)."""
        self._ensure_config_dir()
        existing = self.load()
        existing.update(data)
        
        # Write to temporary file then atomically replace
        temp_file = self.config_path.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        os.chmod(temp_file, 0o600)
        temp_file.replace(self.config_path)

    def clear(self) -> None:
        """Clear stored credentials."""
        if self.config_path.exists():
            try:
                self.config_path.unlink()
            except OSError:
                pass

    def get_api_credentials(self) -> Dict[str, Any]:
        """Get API credentials if available."""
        data = self.load()
        return {
            "client_id": data.get("client_id", ""),
            "client_secret": data.get("client_secret", ""),
            "access_token": data.get("access_token", ""),
            "refresh_token": data.get("refresh_token", ""),
            "expires_at": data.get("expires_at", 0),
            "athlete": data.get("athlete", {}),
        }

    def get_session_cookies(self) -> Dict[str, str]:
        """Get web session cookies if available."""
        data = self.load()
        return data.get("session_cookies", {})

    def get_auth_mode(self) -> str:
        """Get current auth mode: 'api', 'session', 'demo', or 'none'."""
        data = self.load()
        return data.get("auth_mode", "none")

    def set_auth_mode(self, mode: str) -> None:
        self.save({"auth_mode": mode})
