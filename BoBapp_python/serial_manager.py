"""
Serial Communication Manager
"""

import serial
import serial.tools.list_ports
from typing import Optional, List, Tuple


class SerialManager:
    """Beheert seriële communicatie met het Stream Deck apparaat."""
    
    def __init__(self):
        """Initialiseer de SerialManager zonder actieve verbinding."""
        self.port: Optional[serial.Serial] = None
        self.is_connected: bool = False
    
    def get_available_ports(self) -> List[Tuple[str, str]]:
        """Detecteer alle beschikbare seriële poorten."""
        ports = serial.tools.list_ports.comports()
        return [(port.device, port.description) for port in ports]
    
    def connect(self, port_name: str, baudrate: int = 9600) -> bool:
        """Maak verbinding met een seriële poort."""
        try:
            self.port = serial.Serial(port_name, baudrate, timeout=1)
            self.is_connected = True
            print(f"✅ Connected to {port_name}")
            return True
        except Exception as e:
            print(f"❌ Connection error: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Verbreek de seriële verbinding."""
        if self.port and self.port.is_open:
            self.port.close()
            self.is_connected = False
            print("🔌 Disconnected")
    
    def send_message(self, message: str) -> bool:
        """Stuur een bericht naar het apparaat."""
        if not self.is_connected or not self.port or not self.port.is_open:
            print("❌ Not connected")
            return False
        
        try:
            self.port.write(f"{message}\n".encode('utf-8'))
            print(f"📤 Sent: {message}")
            return True
        except Exception as e:
            print(f"❌ Send error: {e}")
            self.is_connected = False
            return False
    
    def send_button_config(self, mode: int, button: int, config: dict) -> bool:
        """Stuur button configuratie naar het apparaat."""
        hotkey = config.get('hotkey', '')
        label = config.get('label', 'Button')
        message = f"BTN:{mode}:{button}:{hotkey}:{label}"
        return self.send_message(message)
    
    def send_mode_switch(self, mode: int) -> bool:
        """Stuur mode wissel commando naar het apparaat."""
        return self.send_message(f"MODE:{mode}")
    
    def send_slider_config(self, slider: int, app_name: str) -> bool:
        """Stuur slider configuratie naar het apparaat."""
        return self.send_message(f"SLIDER:{slider}:{app_name}")
    
    def send_clear_button(self, mode: int, button: int) -> bool:
        """Stuur commando om button te wissen."""
        return self.send_message(f"CLEAR:{mode}:{button}")
    
    def sync_all_configs(self, config_manager, slider_apps: List[str]) -> int:
        """Synchroniseer alle configuraties naar het apparaat."""
        if not self.is_connected:
            print("❌ Cannot sync: not connected")
            return 0
        
        count = 0
        
        # Verzend alle button configuraties
        for key, config in config_manager.config.items():
            if key.startswith("mode_"):
                parts = key.split("_")
                mode = int(parts[1])
                button = int(parts[3])
                
                if self.send_button_config(mode, button, config):
                    count += 1
        
        # Verzend slider configuraties
        for i, app in enumerate(slider_apps):
            if app:
                self.send_slider_config(i, app)
        
        print(f"✅ Synced {count} button configs + {len(slider_apps)} sliders")
        return count