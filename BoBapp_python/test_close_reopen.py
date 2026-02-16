"""
Test Script voor App Close & Reopen Scenario (STANDALONE)

Dit script test het probleem waar Pico en Python niet meer verbinden
na het sluiten en heropenen van de Python app.

Run dit script om te testen:
    python test_close_reopen.py
"""

import serial
import serial.tools.list_ports
import time


def get_available_ports():
    """Haal beschikbare COM poorten op."""
    ports = serial.tools.list_ports.comports()
    return [(port.device, port.description) for port in ports]


def test_connection(port_name, test_number):
    """Test een enkele connectie cyclus."""
    print(f"\n{'='*60}")
    print(f"TEST #{test_number} - Nieuwe verbinding")
    print(f"{'='*60}")
    
    try:
        # Verbind
        print(f"🔌 Verbinden met {port_name}...")
        ser = serial.Serial(port_name, 9600, timeout=0.1)
        print("✅ Verbonden!")
        
        # Wacht op READY
        print("⏳ Wachten op READY bericht...")
        buffer = ""
        ready_received = False
        start_time = time.time()
        timeout = 15  # 15 seconden timeout
        
        while time.time() - start_time < timeout:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                buffer += data
                
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line:
                        print(f"   📥 {line}")
                        if "READY" in line:
                            ready_received = True
                            print("   ✅ READY ontvangen!")
                            break
            
            if ready_received:
                break
            
            time.sleep(0.1)
        
        if not ready_received:
            print("   ❌ TIMEOUT - Geen READY ontvangen")
            print("   ⚠️  Pico zit waarschijnlijk nog in 'pc_connected' mode")
            ser.close()
            return False
        
        # Stuur SYNC_START
        print("\n📤 Sturen: SYNC_START")
        ser.write(b"SYNC_START\n")
        time.sleep(0.5)
        
        # Lees ACK
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            print(f"   📥 Response: {data.strip()}")
        
        print("\n✅ Verbinding succesvol!")
        
        # Stuur een paar PINGs om de verbinding te testen
        print("\n🔄 Testen verbinding met PINGs...")
        for i in range(3):
            ser.write(b"PING\n")
            time.sleep(0.2)
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                print(f"   💓 PING {i+1}: {response.strip()}")
        
        # Sluit netjes
        print("\n🔌 Netjes disconnecten...")
        ser.close()
        print("✅ Verbinding gesloten")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("🧪 App Close & Reopen Test (Standalone)")
    print("=" * 60)
    print()
    print("Dit script simuleert het sluiten en heropenen van de Python app")
    print("om te testen of de Pico correct reconnect.")
    print()
    
    # Haal beschikbare poorten op
    print("📋 Beschikbare COM poorten:")
    ports = get_available_ports()
    
    if not ports:
        print("❌ Geen COM poorten gevonden!")
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
            if idx < 0 or idx >= len(ports):
                print("❌ Ongeldige keuze!")
                return
            port_name = ports[idx][0]
        except:
            print("❌ Ongeldige keuze!")
            return
    
    print()
    print("=" * 60)
    print("📝 TEST PLAN:")
    print("=" * 60)
    print("1. Verbind en disconnect 3x achter elkaar")
    print("2. Tussen elke test wachten we 3 seconden")
    print("3. Dit simuleert het sluiten en heropenen van de app")
    print()
    print("Als de fix werkt:")
    print("   ✅ Alle 3 tests zouden moeten slagen")
    print("   ✅ Pico reset zijn pc_connected status na disconnect")
    print()
    print("Druk op Enter om te starten...")
    input()
    
    # Run meerdere tests
    results = []
    
    for test_num in range(1, 4):
        success = test_connection(port_name, test_num)
        results.append(success)
        
        if test_num < 3:
            print(f"\n⏳ Wachten 3 seconden voor volgende test...")
            time.sleep(3)
    
    # Samenvatting
    print("\n" + "=" * 60)
    print("📊 TEST RESULTATEN")
    print("=" * 60)
    
    for i, success in enumerate(results):
        status = "✅ GESLAAGD" if success else "❌ GEFAALD"
        print(f"   Test #{i+1}: {status}")
    
    print()
    
    if all(results):
        print("🎉 PERFECTE! Alle tests geslaagd!")
        print()
        print("✅ De fix werkt correct:")
        print("   - Python sluit netjes de verbinding")
        print("   - Pico detecteert disconnect na timeout")
        print("   - Pico reset zijn pc_connected status")
        print("   - Reconnectie werkt elke keer perfect")
    else:
        failed_count = results.count(False)
        print(f"⚠️  {failed_count} van 3 tests gefaald")
        print()
        print("Mogelijke oorzaken:")
        print("   - Pico code niet geüpdatet")
        print("   - PC_TIMEOUT te lang (moet 10s zijn)")
        print("   - Python stuurt geen keepalive pings")
        
        if results[0] and not results[1]:
            print()
            print("⚠️  Eerste test OK, tweede FAIL:")
            print("   → Pico reset zijn status niet na disconnect")
            print("   → Check de PC timeout detectie in Pico code")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
