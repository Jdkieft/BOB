"""
Audio Manager

Dit bestand beheert de detectie van audio applicaties op Windows.
Het gebruikt de pycaw library om te communiceren met de Windows Audio API.

Dependencies:
    - pycaw (pip install pycaw)
    - comtypes (automatisch geïnstalleerd met pycaw)
"""

from typing import List


class AudioManager:
    """
    Beheert de detectie van audio applicaties.
    
    Deze class gebruikt de Windows Core Audio API om te detecteren
    welke applicaties momenteel audio afspelen of kunnen afspelen.
    """
    
    @staticmethod
    def get_audio_applications() -> List[str]:
        """
        Detecteer alle lopende applicaties met audio sessies.
        
        Deze methode:
        1. Haalt alle audio sessies op van Windows
        2. Filtert unieke applicatie namen
        3. Returnt een gesorteerde lijst
        
        Returns:
            List van applicatie namen (bijv. ["Discord.exe", "Spotify.exe"])
            Of dummy data als pycaw niet beschikbaar is
        
        Note:
            Als pycaw niet geïnstalleerd is, wordt dummy data geretourneerd
            voor development doeleinden.
        """
        try:
            # Probeer pycaw te importeren
            from pycaw.pycaw import AudioUtilities
            
            # Haal alle audio sessies op
            sessions = AudioUtilities.GetAllSessions()
            apps = []
            
            # Loop door alle sessies
            for session in sessions:
                # Check of de sessie een proces heeft
                if session.Process and session.Process.name():
                    app_name = session.Process.name()
                    
                    # Voeg alleen toe als nog niet in de lijst
                    if app_name not in apps:
                        apps.append(app_name)
            
            # Sorteer alfabetisch voor betere UX
            apps.sort()
            return apps
            
        except ImportError:
            # pycaw niet geïnstalleerd - return dummy data
            print("⚠️ pycaw not installed, using dummy data")
            return AudioManager._get_dummy_apps()
        
        except Exception as e:
            # Andere fout - log en return dummy data
            print(f"❌ Audio detection error: {e}")
            return AudioManager._get_dummy_apps()
    
    @staticmethod
    def _get_dummy_apps() -> List[str]:
        """
        Return dummy applicatie lijst voor development.
        
        Returns:
            List van veelvoorkomende applicaties
        """
        return [
            "Discord.exe",
            "Spotify.exe",
            "chrome.exe",
            "firefox.exe",
            "obs64.exe",
            "steam.exe",
            "vlc.exe"
        ]
    
    @staticmethod
    def get_volume_for_app(app_name: str) -> float:
        """
        Haal het huidige volume op voor een applicatie.
        
        Args:
            app_name: Naam van de applicatie (bijv. "Discord.exe")
        
        Returns:
            Volume level tussen 0.0 en 1.0, of -1 bij fout
        
        Note:
            Deze functie is een placeholder voor toekomstige implementatie.
            Voor echte volume control moet dit verder uitgewerkt worden.
        """
        try:
            from pycaw.pycaw import AudioUtilities
            
            sessions = AudioUtilities.GetAllSessions()
            
            for session in sessions:
                if session.Process and session.Process.name() == app_name:
                    volume = session.SimpleAudioVolume
                    if volume:
                        return volume.GetMasterVolume()
            
            return -1
            
        except Exception as e:
            print(f"❌ Volume detection error: {e}")
            return -1
    
    @staticmethod
    def set_volume_for_app(app_name: str, volume: float) -> bool:
        """
        Stel het volume in voor een applicatie.
        
        Args:
            app_name: Naam van de applicatie (bijv. "Discord.exe")
            volume: Volume level tussen 0.0 en 1.0
        
        Returns:
            True als succesvol, False bij fout
        
        Note:
            Deze functie is een placeholder voor toekomstige implementatie.
            Voor echte volume control moet dit verder uitgewerkt worden.
        """
        try:
            from pycaw.pycaw import AudioUtilities
            
            # Clamp volume tussen 0 en 1
            volume = max(0.0, min(1.0, volume))
            
            sessions = AudioUtilities.GetAllSessions()
            
            for session in sessions:
                if session.Process and session.Process.name() == app_name:
                    volume_interface = session.SimpleAudioVolume
                    if volume_interface:
                        volume_interface.SetMasterVolume(volume, None)
                        return True
            
            return False
            
        except Exception as e:
            print(f"❌ Volume set error: {e}")
            return False

    @staticmethod
    def get_master_volume() -> float:
        """
        Haal het huidige master (systeem) volume op.
        
        Returns:
            Volume level tussen 0.0 en 1.0, of -1 bij fout
        """
        try:
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            
            # GetMasterVolumeLevelScalar returns 0.0 to 1.0
            current_volume = volume.GetMasterVolumeLevelScalar()
            return current_volume
            
        except Exception as e:
            print(f"❌ Master volume get error: {e}")
            return -1
    
    @staticmethod
    def set_master_volume(volume: float) -> bool:
        """
        Stel het master (systeem) volume in.
        
        Args:
            volume: Volume level tussen 0.0 en 1.0
        
        Returns:
            True als succesvol, False bij fout
        """
        try:
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            
            # Clamp volume tussen 0 en 1
            volume = max(0.0, min(1.0, volume))
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume_interface = interface.QueryInterface(IAudioEndpointVolume)
            
            # SetMasterVolumeLevelScalar accepts 0.0 to 1.0
            volume_interface.SetMasterVolumeLevelScalar(volume, None)
            return True
            
        except Exception as e:
            print(f"❌ Master volume set error: {e}")
            return False
