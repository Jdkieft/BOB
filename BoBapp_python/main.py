"""
Stream Deck Manager - Main Entry Point

Single instance: als de app al draait wordt het bestaande venster
naar voren gehaald in plaats van een nieuwe instantie te starten.
"""

import sys
import socket
import threading
from pathlib import Path

# Voeg de directory van dit script toe aan Python's zoekpad
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from main_window import StreamDeckManager

# Vaste poort voor single instance communicatie
SINGLE_INSTANCE_PORT = 47823


def is_already_running() -> bool:
    """
    Probeer een socket te binden op een vaste poort.
    Als dat mislukt draait de app al.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        sock.bind(('127.0.0.1', SINGLE_INSTANCE_PORT))
        # Gelukt - sla socket op zodat hij niet gesloten wordt
        sys.modules[__name__]._instance_socket = sock
        return False
    except OSError:
        return True


def signal_existing_instance():
    """Stuur SHOW signaal naar de al draaiende instantie."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', SINGLE_INSTANCE_PORT))
        sock.send(b'SHOW')
        sock.close()
    except Exception:
        pass


def start_instance_listener(app: StreamDeckManager):
    """
    Luister in een background thread naar SHOW signalen.
    Als een signaal binnenkomt haal het venster naar voren.
    """
    sock = sys.modules[__name__]._instance_socket
    sock.listen(5)

    def listen_loop():
        while True:
            try:
                conn, _ = sock.accept()
                data = conn.recv(16)
                conn.close()
                if data == b'SHOW':
                    # Naar voren halen vanuit de main thread
                    app.after(0, app._show_from_tray)
            except Exception:
                break

    thread = threading.Thread(target=listen_loop, daemon=True)
    thread.start()


def main():
    """Start de Stream Deck Manager applicatie."""

    # Als de app al draait: bestaande instantie naar voren halen
    if is_already_running():
        print("App draait al - bestaande instantie naar voren halen")
        signal_existing_instance()
        return

    app = StreamDeckManager()
    app.switch_mode(0)

    # Start luisteraar voor signalen van nieuwe instanties
    start_instance_listener(app)

    # Minimized starten als dat gevraagd wordt (installer / autostart)
    if "--minimized" in sys.argv:
        app.after(100, app._minimize_to_tray)

    app.mainloop()


if __name__ == "__main__":
    main()
