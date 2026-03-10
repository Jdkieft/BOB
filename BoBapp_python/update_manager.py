"""
Update Manager

Checks for new versions via GitHub Releases and handles updates.

Dependencies:
    - requests (for GitHub API calls)
"""

import sys
import json
import time
import re
import threading
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Callable
from datetime import datetime, timedelta


class UpdateManager:
    """
    Manages software updates via GitHub Releases.
    
    Automatically detects version from release title/tag and downloads
    the first .exe file found in the release assets.
    """
    
    def __init__(
        self,
        current_version: str,
        github_repo: str,
        check_interval_hours: int = 24
    ):
        """
        Initialize the UpdateManager.
        
        Args:
            current_version: Current version (e.g., "0.14" or "1.2.3")
            github_repo: GitHub repo in format "owner/repo"
            check_interval_hours: How often to check automatically (default 24 hours)
        """
        self.current_version = current_version
        self.github_repo = github_repo
        self.check_interval_hours = check_interval_hours
        
        # State
        self.update_available = False
        self.latest_version_info: Optional[Dict] = None
        self.last_check_time: Optional[datetime] = None
        
        # Callbacks
        self.on_update_available: Optional[Callable[[Dict], None]] = None
        
        # Background checking
        self._check_thread: Optional[threading.Thread] = None
        self._check_running = False
        
        # Config file for update settings
        self._config_file = self._get_config_file()
        self._load_config()
        
        print(f"🔄 UpdateManager initialized (v{current_version})")
    
    def _get_config_file(self) -> Path:
        """Get location of update config file."""
        import os
        
        if getattr(sys, 'frozen', False):
            # Running as .exe
            appdata = Path(os.getenv('APPDATA', ''))
            config_dir = appdata / 'StreamDeckManager'
        else:
            # Running as script
            config_dir = Path(__file__).parent
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'update_config.json'
    
    def _load_config(self):
        """Load update configuration from disk."""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r') as f:
                    config = json.load(f)
                    
                # Parse last check time
                if 'last_check' in config:
                    self.last_check_time = datetime.fromisoformat(config['last_check'])
                
                # Load saved update info
                if 'latest_version_info' in config:
                    self.latest_version_info = config['latest_version_info']
                    
                    # Check if this update is still newer
                    if self._is_version_newer(
                        self.latest_version_info.get('version', '0.0.0'),
                        self.current_version
                    ):
                        self.update_available = True
                
                print(f"✅ Update config loaded")
            except Exception as e:
                print(f"⚠️ Could not load update config: {e}")
    
    def _save_config(self):
        """Save update configuration to disk."""
        try:
            config = {
                'last_check': self.last_check_time.isoformat() if self.last_check_time else None,
                'latest_version_info': self.latest_version_info
            }
            
            with open(self._config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Could not save update config: {e}")
    
    def set_callback(self, callback: Callable[[Dict], None]):
        """
        Set callback that's called when update is available.
        
        Args:
            callback: Function that receives update_info dict
        """
        self.on_update_available = callback
        print("✅ Update callback registered")
    
    def _extract_version_from_text(self, text: str) -> Optional[str]:
        """
        Extract version number from text (title or tag).
        
        Looks for patterns like:
        - "v0.14" or "0.14"
        - "version 1.2.3"
        - "BOB 2.0"
        
        Args:
            text: Text to search for version
        
        Returns:
            Version string (e.g., "0.14") or None
        """
        if not text:
            return None
        
        # Try patterns in order of specificity
        patterns = [
            r'v?(\d+\.\d+\.\d+)',           # 1.2.3 or v1.2.3
            r'v?(\d+\.\d+)',                # 1.2 or v1.2
            r'version\s+v?(\d+\.\d+\.\d+)', # version 1.2.3
            r'version\s+v?(\d+\.\d+)',      # version 1.2
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _is_version_newer(self, version_a: str, version_b: str) -> bool:
        """
        Compare two versions.
        
        Args:
            version_a: Version to test (e.g., "0.15")
            version_b: Version to compare against (e.g., "0.14")
        
        Returns:
            True if version_a is newer than version_b
        """
        try:
            # Remove 'v' prefix if present
            v1 = version_a.lstrip('v')
            v2 = version_b.lstrip('v')
            
            # Split on dots and convert to integers
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]
            
            # Pad with zeros if needed
            while len(parts1) < len(parts2):
                parts1.append(0)
            while len(parts2) < len(parts1):
                parts2.append(0)
            
            # Compare
            return parts1 > parts2
            
        except Exception as e:
            print(f"⚠️ Version compare error: {e}")
            return False
    
    def check_for_updates(self, force: bool = False) -> bool:
        """
        Check for updates via GitHub API.
        
        Args:
            force: Force check, even if recently checked
        
        Returns:
            True if update is available
        """
        # Check if we recently checked
        if not force and self.last_check_time:
            time_since_check = datetime.now() - self.last_check_time
            if time_since_check < timedelta(hours=self.check_interval_hours):
                print(f"ℹ️ Last check was {time_since_check.seconds // 3600}h ago")
                return self.update_available
        
        try:
            import requests
            
            # GitHub API endpoint for latest release
            api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            
            print(f"🔍 Checking for updates at {api_url}")
            
            # Request with timeout
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            
            # Extract version from tag_name first, then name as fallback
            tag_name = release_data.get('tag_name', '')
            release_name = release_data.get('name', '')
            
            # Try to extract version
            latest_version = self._extract_version_from_text(tag_name)
            if not latest_version:
                latest_version = self._extract_version_from_text(release_name)
            
            if not latest_version:
                print(f"⚠️ Could not extract version from tag '{tag_name}' or name '{release_name}'")
                return False
            
            release_notes = release_data.get('body', '')
            release_url = release_data.get('html_url', '')
            published_at = release_data.get('published_at', '')
            
            # Find .exe file in assets (use first one found)
            assets = release_data.get('assets', [])
            download_url = None
            installer_size = 0
            installer_name = None
            
            for asset in assets:
                asset_name = asset.get('name', '')
                if asset_name.endswith('.exe'):
                    download_url = asset.get('browser_download_url')
                    installer_size = asset.get('size', 0)
                    installer_name = asset_name
                    print(f"📦 Found installer: {asset_name}")
                    break
            
            # Update info object
            self.latest_version_info = {
                'version': latest_version,
                'name': release_name,
                'notes': release_notes,
                'url': release_url,
                'download_url': download_url,
                'installer_size': installer_size,
                'installer_name': installer_name,
                'published_at': published_at
            }
            
            # Check if this is newer
            self.update_available = self._is_version_newer(latest_version, self.current_version)
            
            # Update check time
            self.last_check_time = datetime.now()
            self._save_config()
            
            if self.update_available:
                print(f"✨ Update available: v{latest_version}")
                
                # Trigger callback
                if self.on_update_available:
                    self.on_update_available(self.latest_version_info)
            else:
                print(f"✅ You have the latest version (v{self.current_version})")
            
            return self.update_available
            
        except ImportError:
            print("❌ 'requests' library not found")
            print("   Install with: pip install requests")
            return False
            
        except Exception as e:
            print(f"❌ Update check failed: {e}")
            return False
    
    def get_latest_version_info(self) -> Optional[Dict]:
        """
        Get info about the latest version.
        
        Returns:
            Dict with version info, or None if not available
        """
        return self.latest_version_info
    
    def download_update(self, save_path: Optional[Path] = None) -> Optional[Path]:
        """
        Download the latest version.
        
        Args:
            save_path: Where to save installer (optional)
        
        Returns:
            Path to downloaded file, or None on error
        """
        if not self.update_available or not self.latest_version_info:
            print("❌ No update available to download")
            return None
        
        download_url = self.latest_version_info.get('download_url')
        if not download_url:
            print("❌ No download URL found in release")
            return None
        
        try:
            import requests
            
            # Determine save location
            if not save_path:
                downloads = Path.home() / 'Downloads'
                filename = self.latest_version_info.get('installer_name', 
                          f"BOB_Setup_v{self.latest_version_info['version']}.exe")
                save_path = downloads / filename
            
            print(f"📥 Downloading update to {save_path}")
            
            # Download with progress
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress feedback
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"📥 {progress:.1f}% downloaded", end='\r')
            
            print(f"\n✅ Update downloaded: {save_path}")
            return save_path
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def install_update(self, installer_path: Path) -> bool:
        """
        Start the installer and close the current application.
        
        Args:
            installer_path: Path to the downloaded installer
        
        Returns:
            True if installer started
        """
        try:
            import subprocess
            
            print(f"🚀 Starting installer: {installer_path}")
            
            # Start installer
            subprocess.Popen([str(installer_path)])
            
            # The application should now shut down so installer can work
            print("👋 Shutting down for update installation...")
            
            return True
            
        except Exception as e:
            print(f"❌ Could not start installer: {e}")
            return False
    
    def open_release_page(self):
        """Open the GitHub release page in browser."""
        if self.latest_version_info:
            url = self.latest_version_info.get('url')
            if url:
                webbrowser.open(url)
                print(f"🌐 Opened release page: {url}")
    
    def start_auto_check(self):
        """Start automatic update checking in background."""
        if self._check_running:
            print("⚠️ Auto-check already running")
            return
        
        self._check_running = True
        self._check_thread = threading.Thread(target=self._auto_check_loop, daemon=True)
        self._check_thread.start()
        print(f"🔄 Auto-check started (interval: {self.check_interval_hours}h)")
    
    def stop_auto_check(self):
        """Stop automatic update checking."""
        self._check_running = False
        print("🛑 Auto-check stopped")
    
    def _auto_check_loop(self):
        """Background loop for automatic updates."""
        # Check immediately on start
        self.check_for_updates()
        
        while self._check_running:
            # Wait for check interval
            time.sleep(self.check_interval_hours * 3600)
            
            # Check for updates
            if self._check_running:
                self.check_for_updates()
    
    def dismiss_update(self):
        """Dismiss the current update (until next version)."""
        self.update_available = False
        self._save_config()
        print(f"✓ Update v{self.latest_version_info['version']} dismissed")
