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
from pathlib import Path
from typing import Dict, Any, Optional


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
        self.config_file = Path(config_file)
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