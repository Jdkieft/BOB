"""
Autostart Manager

Beheert of de Stream Deck Manager automatisch opstart met Windows.
Gebruikt de Windows Startup folder - geen admin rechten vereist.

Methode:
    Een snelkoppeling (.lnk) in de Windows Startup folder zorgt ervoor
    dat de app automatisch opstart bij inloggen.
    
    Startup folder locatie:
    %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
"""

import os
import sys
from pathlib import Path


class AutostartManager:
    """
    Beheert autostart via de Windows Startup folder.
    
    Werkt alleen als de app als .exe draait (PyInstaller).
    Bij draaien als .py script wordt een melding getoond.
    """
    
    APP_NAME = "StreamDeckManager"
    SHORTCUT_NAME = "Stream Deck Manager.lnk"
    
    @staticmethod
    def _get_startup_folder() -> Path:
        """
        Geef het pad naar de Windows Startup folder.
        
        Returns:
            Path naar de Startup folder
        """
        appdata = os.getenv('APPDATA', '')
        return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    
    @staticmethod
    def _get_shortcut_path() -> Path:
        """
        Geef het pad naar de snelkoppeling in de Startup folder.
        
        Returns:
            Path naar de .lnk snelkoppeling
        """
        return AutostartManager._get_startup_folder() / AutostartManager.SHORTCUT_NAME
    
    @staticmethod
    def _get_exe_path() -> str:
        """
        Geef het pad naar de draaiende .exe.
        
        Returns:
            Absoluut pad naar de .exe of het .py script
        """
        if getattr(sys, 'frozen', False):
            # Draait als .exe (PyInstaller)
            return sys.executable
        else:
            # Draait als Python script - gebruik het hoofdscript
            return str(Path(__file__).parent / "main.py")
    
    @staticmethod
    def is_exe() -> bool:
        """
        Controleer of de app als .exe draait.
        
        Returns:
            True als .exe, False als Python script
        """
        return getattr(sys, 'frozen', False)
    
    @staticmethod
    def is_enabled() -> bool:
        """
        Controleer of autostart actief is.
        
        Returns:
            True als snelkoppeling bestaat in Startup folder
        """
        return AutostartManager._get_shortcut_path().exists()
    
    @staticmethod
    def enable() -> bool:
        """
        Zet autostart aan door een snelkoppeling te maken.
        
        Maakt een .lnk bestand in de Windows Startup folder
        dat verwijst naar de .exe, gestart geminimaliseerd
        zodat het op de achtergrond start.
        
        Returns:
            True als succesvol, False bij fout
        """
        try:
            exe_path = AutostartManager._get_exe_path()
            shortcut_path = AutostartManager._get_shortcut_path()
            
            # Zorg dat de startup folder bestaat
            shortcut_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Maak snelkoppeling via Windows Shell COM object
            import winreg  # Controleer of we op Windows zitten
            
            try:
                import win32com.client
                
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(str(shortcut_path))
                shortcut.TargetPath = exe_path
                shortcut.WorkingDirectory = str(Path(exe_path).parent)
                shortcut.Description = "Stream Deck Manager - Autostart"
                # WindowStyle 7 = geminimaliseerd starten
                shortcut.WindowStyle = 7
                shortcut.save()
                
                print(f"✅ Autostart ingeschakeld: {shortcut_path}")
                return True
                
            except ImportError:
                # win32com niet beschikbaar - gebruik alternatieve methode
                return AutostartManager._enable_via_script(exe_path, shortcut_path)
                
        except Exception as e:
            print(f"❌ Autostart enable fout: {e}")
            return False
    
    @staticmethod
    def _enable_via_script(exe_path: str, shortcut_path: Path) -> bool:
        """
        Maak snelkoppeling via PowerShell als win32com niet beschikbaar is.
        
        Args:
            exe_path: Pad naar de .exe
            shortcut_path: Waar de .lnk moet komen
            
        Returns:
            True als succesvol
        """
        try:
            import subprocess
            
            # PowerShell commando om een .lnk te maken
            ps_script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
$Shortcut.TargetPath = '{exe_path}'
$Shortcut.WorkingDirectory = '{Path(exe_path).parent}'
$Shortcut.Description = 'Stream Deck Manager - Autostart'
$Shortcut.WindowStyle = 7
$Shortcut.Save()
"""
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and shortcut_path.exists():
                print(f"✅ Autostart ingeschakeld via PowerShell: {shortcut_path}")
                return True
            else:
                print(f"❌ PowerShell fout: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Autostart via script fout: {e}")
            return False
    
    @staticmethod
    def disable() -> bool:
        """
        Zet autostart uit door de snelkoppeling te verwijderen.
        
        Returns:
            True als succesvol of al uitgeschakeld, False bij fout
        """
        try:
            shortcut_path = AutostartManager._get_shortcut_path()
            
            if shortcut_path.exists():
                shortcut_path.unlink()
                print(f"✅ Autostart uitgeschakeld: {shortcut_path}")
            else:
                print("ℹ️ Autostart was al uitgeschakeld")
            
            return True
            
        except Exception as e:
            print(f"❌ Autostart disable fout: {e}")
            return False
    
    @staticmethod
    def toggle() -> bool:
        """
        Zet autostart aan of uit (wissel).
        
        Returns:
            Nieuwe staat: True = ingeschakeld, False = uitgeschakeld
        """
        if AutostartManager.is_enabled():
            AutostartManager.disable()
            return False
        else:
            AutostartManager.enable()
            return True
