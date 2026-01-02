"""
Serial Communication Manager

Dit bestand beheert de communicatie met het fysieke Stream Deck apparaat
via seriële communicatie (USB/UART).

Protocol:
    - SYNC_START/SYNC_END voor volledige synchronisatie
    - MODE_COUNT:X voor aantal modes
    - MODE_NAME:X:name voor mode namen
    - BTN:mode:button:hotkey:label voor button config
    - MODE:mode voor mode switch
    - SLIDER:slider:app voor slider config
    - CLEAR:mode:button voor button wissen
"""

import serial
import serial.tools.list_ports
from typing import Optional, List, Tuple
import time


class SerialManager:
    """
    Beheert seriële communicatie met het Stream Deck apparaat.
    
    Attributes:
        port (Serial): De actieve seriële poort verbinding
        is_connected (bool): Status van de verbinding
        is_syncing (bool): True tijdens synchronisatie
    """
    
    def __init__(self):
        """Initialiseer de SerialManager zonder actieve verbinding."""
        self.port: Optional[serial.Serial] = None
        self.is_connected: bool = False
        self.is_syncing: bool = False
        self.sync_timeout: float = 10.0  # seconds
    
    def get_available_ports(self) -> List[Tuple[str, str]]:
        """
        Detecteer alle beschikbare seriële poorten.
        
        Returns:
            List van tuples (device_path, description)
            Bijvoorbeeld: [("COM3", "USB Serial Port (COM3)")]
        """
        ports = serial.tools.list_ports.comports()
        return [(port.device, port.description) for port in ports]
    
    def connect(self, port_name: str, baudrate: int = 9600) -> bool:
        """
        Maak verbinding met een seriële poort.
        
        Args:
            port_name: Naam van de poort (bijv. "COM3" of "/dev/ttyUSB0")
            baudrate: Communicatie snelheid (standaard: 9600)
        
        Returns:
            True als verbinding succesvol, False bij fout
        """
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
        """
        Verbreek de seriële verbinding.
        """
        if self.port and self.port.is_open:
            self.port.close()
            self.is_connected = False
            print("🔌 Disconnected")
    
    def send_message(self, message: str) -> bool:
        """
        Stuur een bericht naar het apparaat.
        
        Args:
            message: Het te verzenden bericht (wordt automatisch afgesloten met \\n)
        
        Returns:
            True als succesvol verzonden, False bij fout
        """
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
        """
        Stuur button configuratie naar het apparaat.
        
        Args:
            mode: Mode nummer (0-9)
            button: Button nummer (0-8)
            config: Dict met 'hotkey' en 'label' keys
        
        Returns:
            True als succesvol verzonden
        """
        hotkey = config.get('hotkey', '')
        label = config.get('label', 'Button')
        message = f"BTN:{mode}:{button}:{hotkey}:{label}"
        return self.send_message(message)
    
    def send_mode_switch(self, mode: int) -> bool:
        """Stuur mode wissel commando naar het apparaat."""
        return self.send_message(f"MODE:{mode}")
    
    def send_mode_count(self, count: int) -> bool:
        """Stuur aantal modes naar het apparaat."""
        return self.send_message(f"MODE_COUNT:{count}")
    
    def send_mode_name(self, mode: int, name: str) -> bool:
        """Stuur mode naam naar het apparaat."""
        return self.send_message(f"MODE_NAME:{mode}:{name}")
    
    def send_slider_config(self, slider: int, app_name: str) -> bool:
        """
        Stuur slider configuratie naar het apparaat.
        
        Args:
            slider: Slider nummer (0-2)
            app_name: Naam van de applicatie
        
        Returns:
            True als succesvol verzonden
        """
        return self.send_message(f"SLIDER:{slider}:{app_name}")
    
    def send_clear_button(self, mode: int, button: int) -> bool:
        """Stuur commando om button te wissen."""
        return self.send_message(f"CLEAR:{mode}:{button}")
    
    def send_sync_start(self) -> bool:
        """Start synchronisatie sessie."""
        self.is_syncing = True
        return self.send_message("SYNC_START")
    
    def send_sync_end(self) -> bool:
        """Beëindig synchronisatie sessie."""
        result = self.send_message("SYNC_END")
        self.is_syncing = False
        return result
    
    def send_ping(self) -> bool:
        """Stuur ping voor connection test."""
        return self.send_message("PING")
    
    def wait_for_ready(self, timeout: float = 5.0) -> bool:
        """
        Wacht tot Pico READY stuurt.
        
        Args:
            timeout: Maximum wachttijd in seconden
        
        Returns:
            True als READY ontvangen, False bij timeout
        """
        if not self.is_connected or not self.port or not self.port.is_open:
            print("❌ Not connected, cannot wait for READY")
            return False
        
        print(f"⏳ Waiting for READY (timeout: {timeout}s)...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.port.in_waiting > 0:
                try:
                    line = self.port.readline().decode('utf-8').strip()
                    print(f"📥 Received: {line}")
                    
                    if line.startswith("READY"):
                        # Parse version if present
                        parts = line.split(":")
                        version = parts[1] if len(parts) > 1 else "unknown"
                        print(f"✅ Pico ready (version: {version})")
                        return True
                except Exception as e:
                    print(f"❌ Error reading READY: {e}")
            
            time.sleep(0.1)
        
        print("❌ Timeout waiting for READY")
        return False
    
    def sync_all_configs(self, config_manager, slider_apps: List[str]) -> int:
        """
        Synchroniseer alle configuraties naar het apparaat.
        
        Dit is de COMPLETE sync procedure:
        1. SYNC_START
        2. MODE_COUNT
        3. Alle MODE_NAME's
        4. Alle BTN configuraties
        5. Alle SLIDER configuraties
        6. SYNC_END
        
        Args:
            config_manager: ConfigManager object met alle configuraties
            slider_apps: List van 3 app namen voor de sliders
        
        Returns:
            Aantal succesvol verzonden configuraties
        """
        if not self.is_connected:
            print("❌ Cannot sync: not connected")
            return 0
        
        print("🔄 Starting full synchronization...")
        count = 0
        
        # Step 1: SYNC_START
        if not self.send_sync_start():
            print("❌ Failed to send SYNC_START")
            return 0
        
        # Wait for ACK
        time.sleep(0.1)
        
        # Step 2: Send MODE_COUNT
        num_modes = config_manager.get_num_modes()
        if not self.send_mode_count(num_modes):
            print("❌ Failed to send MODE_COUNT")
            return 0
        print(f"✓ Sent MODE_COUNT: {num_modes}")
        time.sleep(0.05)
        
        # Step 3: Send all MODE_NAMEs
        for mode in range(num_modes):
            mode_name = config_manager.get_mode_name(mode)
            if self.send_mode_name(mode, mode_name):
                print(f"✓ Sent MODE_NAME {mode}: {mode_name}")
                count += 1
            time.sleep(0.05)
        
        # Step 4: Send all button configs
        for key, config in config_manager.config.items():
            if key.startswith("mode_") and "_btn_" in key:
                # Parse key: "mode_0_btn_3" -> mode=0, button=3
                parts = key.split("_")
                try:
                    mode = int(parts[1])
                    button = int(parts[3])
                    
                    if self.send_button_config(mode, button, config):
                        count += 1
                    time.sleep(0.05)
                except (IndexError, ValueError) as e:
                    print(f"❌ Error parsing config key {key}: {e}")
        
        # Step 5: Send slider configs
        for i, app in enumerate(slider_apps):
            if app:
                if self.send_slider_config(i, app):
                    print(f"✓ Sent SLIDER {i}: {app}")
                time.sleep(0.05)
        
        # Step 6: SYNC_END
        if not self.send_sync_end():
            print("❌ Failed to send SYNC_END")
            return 0
        
        print(f"✅ Sync complete: {count} configs + {len(slider_apps)} sliders")
        return count