"""
Test Script voor Disconnectie Detectie

Dit script demonstreert hoe het systeem disconnectie detecteert.

Run dit script om te testen:
    python test_disconnection.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
from serial_manager import SerialManager
from config_manager import ConfigManager


def connection_status_callback(is_connected: bool):
    """Callback voor connection status changes."""
    if is_connected:
        print("\n✅ ═══════════════════════════════════════")
        print("   🟢 VERBONDEN!")
        print("   ═══════════════════════════════════════\n")
    else:
        print("\n❌ ═══════════════════════════════════════")
        print("   🔴 VERBINDING VERBROKEN!")
        print("   ═══════════════════════════════════════\n")


def main():
    print("🧪 Disconnectie Detectie Test")
    print("=" * 50)
    print()
    
    # Maak managers
    config_manager = ConfigManager()
    serial_manager = SerialManager()
    
    # Register callback
    serial_manager.set_callback('CONNECTION_CHANGED', connection_status_callback)
    
    # Haal beschikbare poorten op
    print("📋 Beschikbare COM poorten:")
    ports = serial_manager.get_available_ports()
    
    if not ports:
        print("❌ Geen COM poorten gevonden!")
        print("   Sluit je Arduino/Pico aan en probeer opnieuw.")
        return
    
    for i, (port, desc) in enumerate(ports):
        print(f"   {i+1}. {port} - {desc}")
    
    print()
    
    # Kies poort
    if len(ports) == 1:
        port_name = ports[0][0]
        print(f"✅ Automatisch gekozen: {port_name}")
    else:
        choice = input(f"Kies een poort (1-{len(ports)}): ")
        try:
            idx = int(choice) - 1
            port_name = ports[idx][0]
        except:
            print("❌ Ongeldige keuze!")
            return
    
    print()
    print("=" * 50)
    print()
    
    # Start auto-reconnect
    print(f"🔄 Starting auto-reconnect voor {port_name}...")
    serial_manager.start_auto_reconnect(port_name)
    
    print()
    print("=" * 50)
    print("📝 INSTRUCTIES:")
    print("=" * 50)
    print("1. Wacht tot de verbinding tot stand komt")
    print("2. Trek de USB kabel los van je Arduino/Pico")
    print("3. Kijk hoe het systeem de disconnectie detecteert")
    print("4. Sluit de USB kabel weer aan")
    print("5. Kijk hoe het systeem automatisch reconnect")
    print()
    print("Druk op Ctrl+C om te stoppen")
    print("=" * 50)
    print()
    
    try:
        # Main loop - toon status updates
        last_status = None
        
        while True:
            # Haal huidige status op
            status = serial_manager.get_connection_status()
            
            # Alleen printen als status veranderd is
            if status != last_status:
                print(f"\n📊 Status Update:")
                print(f"   Connected: {status['connected']}")
                print(f"   Port: {status['port']}")
                print(f"   Port Open: {status['port_open']}")
                print(f"   Read Thread: {status['read_thread_alive']}")
                print(f"   Auto-Reconnect: {status['reconnect_active']}")
                
                if status['last_message_ago'] >= 0:
                    print(f"   Last Message: {status['last_message_ago']:.1f}s ago")
                
                last_status = status.copy()
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")
        serial_manager.stop_auto_reconnect()
        serial_manager.disconnect()
        print("✅ Gestopt!")


if __name__ == "__main__":
    main()
