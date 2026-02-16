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
    
    Van Pico naar PC:
    - BTN_PRESS:mode:button voor button indrukken
    - SLIDER_CHANGE:slider:value voor slider wijzigingen
    - MODE_CHANGE:mode voor mode wijzigingen
"""

import serial
import serial.tools.list_ports
from typing import Optional, List, Tuple, Callable
import time
import threading


class SerialManager:
    """
    Beheert seriële communicatie met het Stream Deck apparaat.
    
    Attributes:
        port (Serial): De actieve seriële poort verbinding
        is_connected (bool): Status van de verbinding
        is_syncing (bool): True tijdens synchronisatie
        read_thread (Thread): Background thread voor het lezen van data
        running (bool): Flag om read thread te stoppen
        callbacks (dict): Callbacks voor verschillende message types
    """
    
    def __init__(self):
        """Initialiseer de SerialManager zonder actieve verbinding."""
        self.port: Optional[serial.Serial] = None
        self.is_connected: bool = False
        self.is_syncing: bool = False
        self.sync_timeout: float = 10.0  # seconds
        
        # Threading voor lezen
        self.read_thread: Optional[threading.Thread] = None
        self.running: bool = False
        
        # READY event voor synchronisatie
        self.ready_event = threading.Event()
        self.ready_received = False
        self.ready_handled = False  # voorkom meerdere sync triggers
        
        # Auto-reconnect systeem
        self.reconnect_thread: Optional[threading.Thread] = None
        self.reconnect_running: bool = False
        self.preferred_port: Optional[str] = None
        self.reconnect_interval: float = 2.0  # seconds tussen reconnect pogingen
        
        # Heartbeat/keepalive systeem
        self.last_message_time: float = 0
        self.heartbeat_timeout: float = 5.0  # seconds - disconnect als geen bericht
        self.heartbeat_check_interval: float = 1.0  # check elke seconde
        
        # Keepalive naar Pico (optioneel)
        self.keepalive_enabled: bool = True
        self.keepalive_interval: float = 5.0  # stuur elke 5s een ping naar Pico
        self.last_keepalive_sent: float = 0
        
        # Callbacks voor inkomende berichten
        self.callbacks = {
            'BTN_PRESS': None,      # (mode, button) -> None
            'SLIDER_CHANGE': None,  # (slider, value) -> None
            'MODE_CHANGE': None,    # (mode) -> None
            'CONNECTION_CHANGED': None,  # (is_connected: bool) -> None
        }
    
    def set_callback(self, message_type: str, callback: Callable):
        """
        Stel een callback in voor een bepaald bericht type.
        
        Args:
            message_type: Type bericht ('BTN_PRESS', 'SLIDER_CHANGE', 'MODE_CHANGE')
            callback: Functie om aan te roepen bij dit bericht
        """
        if message_type in self.callbacks:
            self.callbacks[message_type] = callback
            print(f"✅ Callback registered for {message_type}")
    
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
            # Sla preferred port op voor auto-reconnect
            self.preferred_port = port_name
            
            self.port = serial.Serial(port_name, baudrate, timeout=0.1)
            self.is_connected = True
            
            # Reset READY state
            self.ready_event.clear()
            self.ready_received = False
            self.ready_handled = False
            
            # Initialize heartbeat
            self.last_message_time = time.time()
            self.last_keepalive_sent = time.time()
            
            # Start read thread
            self.running = True
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            
            print(f"✅ Connected to {port_name}")
            print(f"🔄 Started read thread")
            
            # Notify GUI via callback
            if self.callbacks['CONNECTION_CHANGED']:
                self.callbacks['CONNECTION_CHANGED'](True)
            
            return True
        except Exception as e:
            print(f"❌ Connection error: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> None:
        """
        Verbreek de seriële verbinding.
        """
        # Stop reconnect thread first
        self.stop_auto_reconnect()
        
        # Stop read thread
        self.running = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1.0)
        
        # Close port
        if self.port and self.port.is_open:
            self.port.close()
            self.is_connected = False
            print("🔌 Disconnected")
            
            # Notify GUI via callback
            if self.callbacks['CONNECTION_CHANGED']:
                self.callbacks['CONNECTION_CHANGED'](False)
    
    def _read_loop(self):
        """
        Background thread die continu data leest van de Pico.
        
        Detecteert ook disconnectie door:
        - Serial errors te monitoren
        - Timeouts te detecteren
        - Port status te checken
        - Stuurt keepalive pings naar Pico
        """
        print("🎧 Read loop started")
        buffer = ""
        consecutive_errors = 0
        max_errors = 5  # Na 5 errors -> consider disconnected
        
        while self.running and self.is_connected:
            try:
                # KEEPALIVE: stuur periodiek ping naar Pico om verbinding te bevestigen
                if self.keepalive_enabled:
                    now = time.time()
                    if now - self.last_keepalive_sent >= self.keepalive_interval:
                        self.send_message("PING")
                        self.last_keepalive_sent = now
                
                if self.port and self.port.is_open and self.port.in_waiting > 0:
                    # Lees alle beschikbare bytes
                    data = self.port.read(self.port.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    
                    # Reset error counter bij succesvolle read
                    consecutive_errors = 0
                    
                    # Verwerk complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line:
                            self._handle_incoming_message(line)
                
                # Check of port nog steeds open is
                elif not self.port or not self.port.is_open:
                    print("❌ Port is no longer open!")
                    self._handle_disconnection()
                    break
                
                # Kleine pauze om CPU niet te overbelasten
                time.sleep(0.01)
                
            except (serial.SerialException, OSError) as e:
                # Serial error - mogelijk disconnected
                consecutive_errors += 1
                print(f"⚠️ Serial error ({consecutive_errors}/{max_errors}): {e}")
                
                if consecutive_errors >= max_errors:
                    print("❌ Too many errors - device disconnected!")
                    self._handle_disconnection()
                    break
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"⚠️ Unexpected read error: {e}")
                consecutive_errors += 1
                
                if consecutive_errors >= max_errors:
                    print("❌ Too many errors - stopping read loop")
                    self._handle_disconnection()
                    break
                
                time.sleep(0.1)
        
        print("🛑 Read loop stopped")
    
    def _handle_disconnection(self):
        """
        Handle disconnectie - wordt aangeroepen vanuit read thread.
        
        Deze methode zorgt ervoor dat:
        1. De connection status wordt gereset
        2. De GUI wordt genotificeerd
        3. Auto-reconnect blijft actief (als dat al draaide)
        """
        if not self.is_connected:
            return  # Already handled
        
        print("🔌 Handling disconnection...")
        
        # Update status
        self.is_connected = False
        
        # Close port safely
        try:
            if self.port and self.port.is_open:
                self.port.close()
        except:
            pass
        
        # Notify GUI via callback
        if self.callbacks['CONNECTION_CHANGED']:
            self.callbacks['CONNECTION_CHANGED'](False)
        
        print("❌ Disconnected - auto-reconnect will continue if enabled")
    
    def _handle_incoming_message(self, message: str):
        """
        Verwerk een bericht van de Pico.
        
        Args:
            message: Het ontvangen bericht
        """
        # Update last message time (voor heartbeat monitoring)
        self.last_message_time = time.time()
        
        print(f"📥 Received: {message}")
        
        # Parse message type
        if ':' in message:
            parts = message.split(':', 1)
            msg_type = parts[0]
            params = parts[1] if len(parts) > 1 else ""
            
            # BTN_PRESS:mode:button
            if msg_type == "BTN_PRESS":
                try:
                    param_parts = params.split(':')
                    mode = int(param_parts[0])
                    button = int(param_parts[1])
                    
                    if self.callbacks['BTN_PRESS']:
                        self.callbacks['BTN_PRESS'](mode, button)
                except Exception as e:
                    print(f"❌ Error parsing BTN_PRESS: {e}")
            
            # SLIDER_CHANGE:slider:value
            elif msg_type == "SLIDER_CHANGE":
                try:
                    param_parts = params.split(':')
                    slider = int(param_parts[0])
                    value = int(param_parts[1])
                    
                    if self.callbacks['SLIDER_CHANGE']:
                        self.callbacks['SLIDER_CHANGE'](slider, value)
                except Exception as e:
                    print(f"❌ Error parsing SLIDER_CHANGE: {e}")
            
            # MODE_CHANGE:mode
            elif msg_type == "MODE_CHANGE":
                try:
                    mode = int(params)
                    
                    if self.callbacks['MODE_CHANGE']:
                        self.callbacks['MODE_CHANGE'](mode)
                except Exception as e:
                    print(f"❌ Error parsing MODE_CHANGE: {e}")
            
            # ACK berichten (voor debugging)
            elif msg_type.startswith("ACK"):
                print(f"✅ ACK: {params}")
            
            # READY bericht
            elif msg_type == "READY":
                print(f"🎯 Pico ready: {params}")
                
                # Alleen eerste keer triggeren
                if not self.ready_received:
                    self.ready_received = True
                    self.ready_event.set()  # Signal dat READY ontvangen is
                else:
                    # Herhaalde READY berichten - log maar trigger niet opnieuw
                    print(f"   (heartbeat - already received)")

            
            # Error berichten
            elif msg_type.startswith("ERROR"):
                print(f"⚠️ Pico error: {params}")
        
        else:
            # Bericht zonder ':'
            if message == "Pong":
                print("🏓 Pong received")
                
                # Als we nog op READY wachten, accepteer Pong als bewijs dat Pico actief is
                # Dit gebeurt als Pico al verbonden was en niet opnieuw READY stuurt
                if not self.ready_received:
                    print("   (accepting Pong as ready signal - Pico was already connected)")
                    self.ready_received = True
                    self.ready_event.set()
            else:
                print(f"ℹ️ Info: {message}")
    
    def send_message(self, message: str) -> bool:
        """
        Stuur een bericht naar het apparaat.
        
        Args:
            message: Het te verzenden bericht (wordt automatisch afgesloten met \n)
        
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
    
    def send_spotify_track(self, artist: str, title: str) -> bool:
        """
        Stuur Spotify track informatie naar het apparaat.
        
        Args:
            artist: Artiest naam
            title: Track titel
        
        Returns:
            True als succesvol verzonden
        """
        # Gebruik | als separator omdat artist/title ":" kunnen bevatten
        return self.send_message(f"SPOTIFY:{artist}|{title}")
    
    def wait_for_ready(self, timeout: float = 5.0) -> bool:
        """
        Wacht tot Pico READY stuurt (of Pong als Pico al connected was).
        
        Deze functie wacht op een threading.Event dat wordt gezet door
        de read thread wanneer READY of Pong ontvangen wordt.
        
        Args:
            timeout: Maximum wachttijd in seconden
        
        Returns:
            True als READY of Pong ontvangen, False bij timeout
        """
        if not self.is_connected:
            print("❌ Not connected, cannot wait for READY")
            return False
        
        print(f"⏳ Waiting for READY (timeout: {timeout}s)...")
        
        # Stuur eerst een PING om te testen of Pico reageert
        # Als Pico al verbonden was, krijgen we Pong in plaats van READY
        self.send_ping()
        
        # Wacht op event (thread-safe!)
        ready = self.ready_event.wait(timeout=timeout)
        
        if ready:
            print(f"✅ Pico READY received!")
            return True
        else:
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
        for i, apps in enumerate(slider_apps):
            if apps:
                # Send as comma-separated list or one by one
                if isinstance(apps, list):
                    apps_str = ",".join(apps) if apps else "NONE"
                else:
                    apps_str = str(apps)
                
                if self.send_slider_config(i, apps_str):
                    print(f"✓ Sent SLIDER {i}: {len(apps) if isinstance(apps, list) else 1} apps")
                time.sleep(0.05)
        
        # Step 6: SYNC_END
        if not self.send_sync_end():
            print("❌ Failed to send SYNC_END")
            return 0
        
        print(f"✅ Sync complete: {count} configs + {len(slider_apps)} sliders")
        return count
    
    def start_auto_reconnect(self, port_name: str) -> None:
        """
        Start auto-reconnect thread voor een specifieke poort.
        
        Deze thread probeert continu te verbinden met de opgegeven poort
        als de verbinding verbroken is.
        
        Args:
            port_name: COM poort om mee te verbinden (bijv. "COM3")
        """
        if self.reconnect_running:
            print("⚠️ Auto-reconnect already running")
            return
        
        self.preferred_port = port_name
        self.reconnect_running = True
        
        self.reconnect_thread = threading.Thread(
            target=self._reconnect_loop,
            daemon=True
        )
        self.reconnect_thread.start()
        
        print(f"🔄 Auto-reconnect started for {port_name}")
    
    def stop_auto_reconnect(self) -> None:
        """
        Stop de auto-reconnect thread.
        """
        if not self.reconnect_running:
            return
        
        self.reconnect_running = False
        
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            self.reconnect_thread.join(timeout=1.0)
        
        print("🛑 Auto-reconnect stopped")
    
    def _reconnect_loop(self) -> None:
        """
        Background thread die continu probeert te reconnecten.
        """
        print(f"🔄 Reconnect loop started for {self.preferred_port}")
        
        while self.reconnect_running:
            # Alleen proberen als niet verbonden
            if not self.is_connected and self.preferred_port:
                try:
                    # Check of de poort beschikbaar is
                    available_ports = [p[0] for p in self.get_available_ports()]
                    
                    if self.preferred_port in available_ports:
                        print(f"🔌 Attempting to connect to {self.preferred_port}...")
                        
                        # Probeer te verbinden
                        if self.connect(self.preferred_port):
                            print(f"✅ Auto-reconnect successful!")
                            # Blijf loop runnen voor het geval van disconnectie
                        else:
                            print(f"❌ Connect attempt failed")
                    
                except Exception as e:
                    print(f"❌ Reconnect error: {e}")
            
            # Wacht voor volgende poging
            time.sleep(self.reconnect_interval)
        
        print("🛑 Reconnect loop stopped")
    
    def check_connection_health(self) -> bool:
        """
        Check of de verbinding nog gezond is.
        
        Deze methode controleert:
        1. Of we denken verbonden te zijn
        2. Of de port nog open is
        3. Of we recent berichten ontvangen hebben (heartbeat)
        
        Returns:
            True als verbinding gezond is, False als er problemen zijn
        """
        if not self.is_connected:
            return False
        
        # Check of port nog open is
        if not self.port or not self.port.is_open:
            print("⚠️ Port check failed - not open")
            self._handle_disconnection()
            return False
        
        # Check heartbeat (optioneel - kan uitgeschakeld als Pico geen regelmatige berichten stuurt)
        # if time.time() - self.last_message_time > self.heartbeat_timeout:
        #     print(f"⚠️ Heartbeat timeout ({self.heartbeat_timeout}s)")
        #     self._handle_disconnection()
        #     return False
        
        return True
    
    def get_connection_status(self) -> dict:
        """
        Haal gedetailleerde connection status op.
        
        Returns:
            Dict met connection info voor debugging/display
        """
        status = {
            'connected': self.is_connected,
            'port': self.preferred_port or "None",
            'port_open': self.port.is_open if self.port else False,
            'read_thread_alive': self.read_thread.is_alive() if self.read_thread else False,
            'reconnect_active': self.reconnect_running,
            'last_message_ago': time.time() - self.last_message_time if self.last_message_time > 0 else -1
        }
        return status
