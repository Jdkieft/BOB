"""
Configuration Manager

Dit bestand beheert het opslaan en laden van configuraties.
Het houdt alle button mappings en slider instellingen bij in een JSON bestand.

Configuratie structuur:
    {
        "mode_0_btn_0": {
            "icon": "🎮",
            "label": "Discord Mute",
            "hotkey": "ctrl+shift+m"
        },
        "slider_0": "Discord.exe",
        ...
    }
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def get_config_directory():
    """
    Bepaal de juiste directory voor config opslag.
    
    Deze functie zorgt ervoor dat config bestanden op de juiste plek komen:
    - Bij .exe: In %APPDATA%/StreamDeckManager/
    - Bij script: In de script directory
    
    Returns:
        Path object naar de config directory
    """
    if getattr(sys, 'frozen', False):
        # Running als .exe (PyInstaller)
        # Gebruik AppData voor persistent storage
        appdata = os.getenv('APPDATA')
        config_dir = Path(appdata) / 'StreamDeckManager'
    else:
        # Running als Python script
        # Gebruik script directory
        config_dir = Path(__file__).parent
    
    # Maak directory als die niet bestaat
    config_dir.mkdir(parents=True, exist_ok=True)
    
    return config_dir


class ConfigManager:
    """
    Beheert het laden, opslaan en manipuleren van configuraties.
    
    Attributes:
        config_file (Path): Pad naar het JSON configuratiebestand
        config (Dict): De huidige configuratie in het geheugen
    """
    
    def __init__(self, config_file: str = "streamdeck_config.json"):
        """
        Initialiseer de ConfigManager.
        
        Args:
            config_file: Naam van het configuratiebestand (standaard: streamdeck_config.json)
        """
        # Bepaal de juiste locatie voor config
        config_dir = get_config_directory()
        self.config_file = config_dir / config_file
        
        print(f"📁 Config file location: {self.config_file}")
        
        self.config: Dict[str, Any] = self.load()
        self.config: Dict[str, Any] = self.load()
        
        # Zorg ervoor dat num_modes bestaat in config
        if 'num_modes' not in self.config:
            from constants import DEFAULT_MODES
            self.config['num_modes'] = DEFAULT_MODES
            self.save()
    
    def get_num_modes(self) -> int:
        """
        Haal het aantal actieve modes op.
        
        Returns:
            Aantal modes (standaard 4)
        """
        return self.config.get('num_modes', 4)
    
    def set_num_modes(self, num_modes: int) -> None:
        """
        Stel het aantal modes in.
        
        Args:
            num_modes: Aantal modes (1-10)
        """
        from constants import MIN_MODES, MAX_MODES_LIMIT
        
        # Clamp tussen min en max
        num_modes = max(MIN_MODES, min(MAX_MODES_LIMIT, num_modes))
        
        self.config['num_modes'] = num_modes
        self.save()
        print(f"✓ Number of modes set to {num_modes}")
    
    def get_mode_name(self, mode: int) -> str:
        """
        Haal de naam van een mode op.
        
        Args:
            mode: Mode nummer (0-9)
        
        Returns:
            Custom naam of standaard "Mode X"
        """
        key = f"mode_{mode}_name"
        return self.config.get(key, f"Mode {mode + 1}")
    
    def set_mode_name(self, mode: int, name: str) -> None:
        """
        Stel een custom naam in voor een mode.
        
        Args:
            mode: Mode nummer (0-9)
            name: Nieuwe naam voor de mode
        """
        key = f"mode_{mode}_name"
        self.config[key] = name
        self.save()
        print(f"✓ Mode {mode} renamed to '{name}'")
    
    def load(self) -> Dict[str, Any]:
        """
        Laad configuratie van disk.
        
        Returns:
            Dict met configuratie, of lege dict als bestand niet bestaat
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Error loading config: {e}")
                return {}
        return {}
    
    def save(self) -> None:
        """
        Sla huidige configuratie op naar disk.
        
        Schrijft de config dict naar JSON bestand met mooie formatting.
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print("💾 Config saved")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    
    def get_button_config(self, mode: int, button: int) -> Optional[Dict[str, str]]:
        """
        Haal button configuratie op voor een specifieke mode en button.
        
        Args:
            mode: Mode nummer (0-3)
            button: Button nummer (0-8)
        
        Returns:
            Dict met icon, label en hotkey, of None als niet geconfigureerd
        """
        key = f"mode_{mode}_btn_{button}"
        return self.config.get(key)
    
    def set_button_config(self, mode: int, button: int, config: Dict[str, str]) -> None:
        """
        Sla button configuratie op.
        
        Args:
            mode: Mode nummer (0-3)
            button: Button nummer (0-8)
            config: Dict met 'icon', 'label' en 'hotkey' keys
        """
        key = f"mode_{mode}_btn_{button}"
        self.config[key] = config
        self.save()
    
    def clear_button_config(self, mode: int, button: int) -> None:
        """
        Verwijder button configuratie.
        
        Args:
            mode: Mode nummer (0-3)
            button: Button nummer (0-8)
        """
        key = f"mode_{mode}_btn_{button}"
        if key in self.config:
            del self.config[key]
            self.save()
    
    def get_slider_config(self, slider: int):
        """
        Haal slider configuratie op.
        
        Args:
            slider: Slider nummer (0-2)
        
        Returns:
            List van app namen of lege list
        """
        config = self.config.get(f"slider_{slider}", [])
        # Backward compatibility: convert string to list
        if isinstance(config, str):
            return [config] if config and config != "Master Volume" else []
        return config if isinstance(config, list) else []
    
    def set_slider_config(self, slider: int, app_names) -> None:
        """
        Sla slider configuratie op.
        
        Args:
            slider: Slider nummer (0-2)
            app_names: List van app namen of enkele app naam (backward compat)
        """
        # Accept both list and string for backward compatibility
        if isinstance(app_names, str):
            app_names = [app_names] if app_names else []
        
        self.config[f"slider_{slider}"] = app_names
        self.save()
        print(f"✓ Slider {slider} configured with {len(app_names)} apps")
    
    def export_to_file(self, filename: str) -> None:
        """
        Export configuratie naar een specifiek bestand.
        
        Args:
            filename: Pad naar het exportbestand
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"📤 Exported to {filename}")
        except Exception as e:
            print(f"❌ Error exporting: {e}")
    
    def import_from_file(self, filename: str) -> bool:
        """
        Importeer configuratie van een bestand.
        
        Args:
            filename: Pad naar het importbestand
        
        Returns:
            True als succesvol, False bij fout
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.save()
            print(f"📥 Imported from {filename}")
            return True
        except Exception as e:
            print(f"❌ Error importing: {e}")
            return False
    
    def get_preferred_port(self) -> str:
        """
        Haal de voorkeurs COM poort op.
        
        Returns:
            COM poort naam (bijv. "COM3") of lege string als niet ingesteld
        """
        return self.config.get('preferred_port', '')
    
    def set_preferred_port(self, port: str) -> None:
        """
        Sla de voorkeurs COM poort op.
        
        Args:
            port: COM poort naam (bijv. "COM3")
        """
        self.config['preferred_port'] = port
        self.save()
        print(f"✅ Preferred port set to {port}")
    
    def get_slider_name(self, slider: int) -> str:
        """
        Haal de naam van een slider op.
        
        Args:
            slider: Slider nummer (0-3)
        
        Returns:
            Custom naam of standaard naam
        """
        key = f"slider_{slider}_name"
        default_name = "Master Volume" if slider == 3 else f"Slider {slider + 1}"
        return self.config.get(key, default_name)
    
    def set_slider_name(self, slider: int, name: str) -> None:
        """
        Stel een custom naam in voor een slider.
        
        Args:
            slider: Slider nummer (0-3)
            name: Nieuwe naam voor de slider
        """
        key = f"slider_{slider}_name"
        self.config[key] = name
        self.save()
        print(f"✅ Slider {slider} renamed to '{name}'")
    
    def get_app_display_name(self, original_name: str) -> str:
        """
        Haal de display naam op voor een app.
        
        Args:
            original_name: Originele app naam (bijv. "gw2.exe")
        
        Returns:
            Custom display naam of originele naam
        """
        mappings = self.config.get('app_name_mappings', {})
        return mappings.get(original_name, original_name)
    
    def set_app_display_name(self, original_name: str, display_name: str) -> None:
        """
        Stel een custom display naam in voor een app.
        
        Args:
            original_name: Originele app naam (bijv. "gw2.exe")
            display_name: Custom display naam (bijv. "Guild Wars 2")
        """
        if 'app_name_mappings' not in self.config:
            self.config['app_name_mappings'] = {}
        
        self.config['app_name_mappings'][original_name] = display_name
        self.save()
        print(f"✅ App '{original_name}' display name set to '{display_name}'")
    
    def get_all_app_name_mappings(self) -> dict:
        """
        Haal alle app naam mappings op.
        
        Returns:
            Dict met {original_name: display_name} mappings
        """
        return self.config.get('app_name_mappings', {}).copy()