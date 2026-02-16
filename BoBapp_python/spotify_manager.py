"""
Spotify Manager

Dit bestand detecteert welk nummer er speelt via Windows Media Session API
en stuurt deze info naar de Pico voor weergave op de OLED.

Dependencies:
    - winsdk (pip install winsdk)
"""

import threading
import time
from typing import Optional, Dict, Callable
import sys


class SpotifyManager:
    """
    Beheert media track detectie en notificaties.
    
    Deze class:
    - Detecteert wanneer er een nieuw nummer speelt (via Windows Media API)
    - Haalt artiest en titel op
    - Notificeert de serial manager voor display op OLED
    - Werkt met Spotify, YouTube Music, Apple Music, Chrome, etc.
    
    Attributes:
        running (bool): Of de monitor thread actief is
        monitor_thread (Thread): Background thread voor detectie
        current_track (str): Huidige track info
        on_track_change (Callable): Callback bij track wijziging
        check_interval (float): Hoe vaak te checken (seconden)
    """
    
    def __init__(self):
        """Initialiseer de Spotify Manager."""
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.current_track: Optional[str] = None
        self.on_track_change: Optional[Callable[[str, str], None]] = None
        self.check_interval = 1.0  # Check elke seconde
        
        # Platform check
        self.platform = sys.platform
        
        if self.platform == 'win32':
            try:
                # Try importing Windows Media Session
                from winsdk.windows.media.control import \
                    GlobalSystemMediaTransportControlsSessionManager as MediaManager
                self.media_available = True
                print("✅ Windows Media Session available")
            except ImportError:
                self.media_available = False
                print("⚠️ winsdk not installed - Media detection disabled")
                print("   Install with: pip install winsdk")
        else:
            self.media_available = False
            print("⚠️ Media detection only available on Windows")
    
    def set_callback(self, callback: Callable[[str, str], None]):
        """
        Stel callback in voor track wijzigingen.
        
        Args:
            callback: Functie (artist, title) die aangeroepen wordt bij nieuwe track
        """
        self.on_track_change = callback
        print("✅ Media callback registered")
    
    def start(self):
        """Start de media monitor thread."""
        if not self.media_available:
            print("⚠️ Cannot start media monitor - platform not supported")
            return
        
        if self.running:
            print("⚠️ Media monitor already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("🎵 Media monitor started")
    
    def stop(self):
        """Stop de media monitor thread."""
        if not self.running:
            return
        
        self.running = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        
        print("🛑 Media monitor stopped")
    
    def _get_media_info(self) -> Optional[Dict[str, str]]:
        """
        Haal media track info op via Windows Media Session API.
        
        Returns:
            Dict met 'artist' en 'title', of None als niets speelt
        """
        if not self.media_available:
            return None
        
        try:
            import asyncio
            from winsdk.windows.media.control import \
                GlobalSystemMediaTransportControlsSessionManager as MediaManager
            
            # Get current session
            async def get_media_info():
                sessions = await MediaManager.request_async()
                
                # Get current session (the one that's playing)
                current_session = sessions.get_current_session()
                if current_session:
                    info = await current_session.try_get_media_properties_async()
                    
                    # Get playback info to check if actually playing
                    playback_info = current_session.get_playback_info()
                    playback_status = playback_info.playback_status
                    
                    # Only return info if actually playing (not paused)
                    # PlaybackStatus: 0=Closed, 1=Opened, 2=Changing, 3=Stopped, 4=Playing, 5=Paused
                    if playback_status == 4 and info:  # 4 = Playing
                        artist = info.artist or "Unknown Artist"
                        title = info.title or "Unknown Title"
                        
                        return {
                            'artist': artist,
                            'title': title
                        }
                
                return None
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(get_media_info())
            loop.close()
            
            return result
            
        except Exception as e:
            # Silent fail - geen media actief
            return None
    
    def _monitor_loop(self):
        """
        Background thread die media monitort.
        
        Deze thread:
        1. Checkt periodiek de Windows Media Session
        2. Detecteert track wijzigingen
        3. Notificeert callback bij nieuwe tracks
        """
        print("🎧 Media monitor loop started")
        
        last_track = None
        
        while self.running:
            try:
                # Haal huidige track op
                track_info = self._get_media_info()
                
                if track_info:
                    # Maak unieke track identifier
                    current_track = f"{track_info['artist']} - {track_info['title']}"
                    
                    # Check of track veranderd is
                    if current_track != last_track:
                        print(f"🎵 New track: {current_track}")
                        
                        # Update state
                        self.current_track = current_track
                        last_track = current_track
                        
                        # Notificeer callback
                        if self.on_track_change:
                            self.on_track_change(
                                track_info['artist'],
                                track_info['title']
                            )
                else:
                    # Geen track actief
                    if last_track is not None:
                        print("🎵 Media stopped/paused")
                        last_track = None
                        self.current_track = None
                
            except Exception as e:
                print(f"❌ Media monitor error: {e}")
            
            # Wacht voor volgende check
            time.sleep(self.check_interval)
        
        print("🛑 Media monitor loop stopped")
    
    def get_current_track(self) -> Optional[Dict[str, str]]:
        """
        Haal de huidige track info op.
        
        Returns:
            Dict met 'artist' en 'title', of None als geen track speelt
        """
        if not self.current_track:
            return None
        
        # Parse het opgeslagen track formaat
        if " - " in self.current_track:
            parts = self.current_track.split(" - ", 1)
            return {
                'artist': parts[0],
                'title': parts[1]
            }
        
        return None


# Test code
if __name__ == "__main__":
    print("🧪 Media Manager Test")
    print("=" * 50)
    
    def on_track_change(artist: str, title: str):
        print(f"🎵 Track Changed!")
        print(f"   Artist: {artist}")
        print(f"   Title: {title}")
    
    manager = SpotifyManager()
    manager.set_callback(on_track_change)
    manager.start()
    
    print("\n▶️  Speel media af (Spotify, YouTube, etc.)")
    print("⏸️  Druk op Ctrl+C om te stoppen\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")
        manager.stop()
        print("✅ Done!")
