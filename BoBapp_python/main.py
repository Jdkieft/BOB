"""
Stream Deck Manager - Main Entry Point (FIXED VERSION)

Deze versie zorgt ervoor dat Python altijd in de juiste directory zoekt,
ongeacht vanuit welke folder je het script start.

Gebruik:
    python main.py
    
OF vanuit elke andere folder - gebruik gewoon het volledige pad
"""

import sys
from pathlib import Path

# Voeg de directory van dit script toe aan Python's zoekpad
# Zo kan Python alle andere modules vinden, ongeacht vanuit welke
# folder je het script uitvoert
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from main_window import StreamDeckManager


def main():
    """
    Start de Stream Deck Manager applicatie.
    
    Deze functie:
    1. Creëert een nieuw StreamDeckManager object
    2. Zet de initiële mode op 0 (Mode 1)
    3. Start de GUI event loop
    """
    app = StreamDeckManager()
    app.switch_mode(0)  # Start in Mode 1
    app.mainloop()


if __name__ == "__main__":
    main()