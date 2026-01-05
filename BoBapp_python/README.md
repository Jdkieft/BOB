# Stream Deck Manager

Een Python applicatie voor het configureren van een custom Stream Deck met audio sliders.

## Bestands Structuur

```
stream_deck_manager/
│
├── main.py                    # Hoofdbestand - start de applicatie
├── constants.py               # Alle constanten en configuratie
├── config_manager.py          # Configuratie opslag (JSON)
├── serial_manager.py          # Seriële communicatie met device
├── audio_manager.py           # Audio applicatie detectie
│
├── gui/
│   ├── __init__.py           # GUI package initializer
│   ├── main_window.py        # Hoofdvenster
│   ├── button_widget.py      # Configureerbare button component
│   ├── slider_widget.py      # Audio slider component
│   └── dialogs.py            # Dialog windows (config, serial)
│
└── streamdeck_config.json    # Configuratie bestand (wordt automatisch aangemaakt)
```

## Uitleg per Bestand

### `main.py`
Het entry point van de applicatie. Start het hoofdvenster en de event loop.

**Gebruik:**
```bash
python main.py
```

### `constants.py`
Bevat alle constanten zoals:
- Kleuren (light/dark mode)
- Fonts en groottes
- Window afmetingen
- Quick Actions lijst
- Error/info berichten

**Wijzig hier om:** Kleuren, fonts, window grootte, of standaard quick actions aan te passen.

### `config_manager.py`
Beheert het opslaan en laden van configuraties in JSON formaat.

**Verantwoordelijkheden:**
- Button configuraties per mode opslaan
- Slider app assignments opslaan
- Export/import functionaliteit
- Validatie van configuratie

**Config Structuur:**
```json
{
  "mode_0_btn_0": {
    "icon": "🎮",
    "label": "Discord Mute",
    "hotkey": "ctrl+shift+m"
  },
  "slider_0": "Discord.exe"
}
```

### `serial_manager.py`
Beheert seriële communicatie met het fysieke device (Arduino/Pico).

**Protocol:**
```
BTN:mode:button:hotkey:label     # Configureer button
MODE:mode                         # Wissel mode
SLIDER:slider:app                 # Configureer slider
CLEAR:mode:button                 # Wis button
```

**Verantwoordelijkheden:**
- Detecteer beschikbare COM poorten
- Maak/verbreek seriële verbinding
- Stuur commando's naar device
- Synchroniseer alle configuraties

### `audio_manager.py`
Detecteert actieve audio applicaties op Windows met pycaw library.

**Functionaliteit:**
- Haal lijst van audio apps op
- Volume detection (placeholder)
- Volume control (placeholder)

**Dependencies:**
```bash
pip install pycaw
```

### `gui/main_window.py`
Het hoofdvenster van de applicatie. Orkestreert alle componenten.

**Verantwoordelijkheden:**
- Maak complete UI layout
- Beheer state (current mode, slider apps)
- Coördineer managers (config, serial, audio)
- Event handling (clicks, changes)
- State synchronisatie tussen UI en managers

**Belangrijke Methoden:**
- `switch_mode(mode)` - Wissel tussen modes
- `_handle_button_click(index)` - Open configuratie dialog
- `_sync_all_configs()` - Synchroniseer met device

### `gui/button_widget.py`
Een herbruikbare component voor één configureerbare button.

**Features:**
- Volledig klikbaar oppervlak
- Hover effecten
- Visuele feedback (groen = geconfigureerd)
- Icon, label en hotkey weergave
- Button nummer badge

**Gebruik:**
```python
button = ButtonWidget(
    parent=frame,
    index=0,
    row=0,
    col=0,
    on_click=self._handle_click
)
button.update_display(config)
```

### `gui/slider_widget.py`
Een herbruikbare component voor één audio slider.

**Features:**
- App selectie dropdown
- Visuele progress bar
- Volume percentage weergave
- Auto-update beschikbare apps

**Gebruik:**
```python
slider = SliderWidget(
    parent=frame,
    index=0,
    available_apps=["Discord.exe", "Spotify.exe"],
    on_app_change=self._handle_change
)
slider.set_app("Discord.exe")
slider.update_volume_display(0.75)  # 75%
```

### `gui/dialogs.py`
Bevat alle dialog windows.

**ButtonConfigDialog:**
- Icon input (emoji)
- Label input (tekst)
- Hotkey builder (modifiers + key)
- Live preview
- Save/Clear buttons

**SerialPortDialog:**
- Lijst van beschikbare poorten
- Radio button selectie
- Connect actie

## Installatie

### Vereisten
```bash
pip install customtkinter
pip install pyserial
pip install pycaw  # Optioneel, voor audio detectie
```

### Setup
1. Plaats alle bestanden in de juiste structuur
2. Zorg dat `gui/` folder bestaat met `__init__.py`
3. Start met `python main.py`

## Gebruik

### 1. Verbinden met Device
- Click "🔌 Connect" in de header
- Selecteer je Arduino/Pico COM poort
- Configuraties worden automatisch gesynchroniseerd

### 2. Button Configureren
- Click op een button (#1-9) in de grid
- Voer icon, label en hotkey in
- Preview toont de hotkey live
- Click "Save" om op te slaan

### 3. Slider Configureren
- Selecteer een app in de dropdown
- De slider wordt gekoppeld aan die app
- Volume wordt visueel weergegeven

### 4. Mode Wisselen
- Click "Mode 1" tot "Mode 4" bovenaan
- Elke mode heeft 9 unieke buttons
- Configuraties worden per mode opgeslagen

### 5. Quick Actions
- Click een quick action rechts
- Click daarna een button om toe te wijzen
- Quick action wordt automatisch ingevuld

### 6. Export/Import
- Export: Sla configuratie op als .json
- Import: Laad configuratie van .json
- Handig voor backups of delen

## Aanpassingen Maken

### Kleuren Wijzigen
Pas aan in `constants.py`:
```python
COLOR_BUTTON_FOCUS = "#3B82F6"  # Blauw -> Rood
```

### Meer Modes Toevoegen
Pas aan in `constants.py`:
```python
MAX_MODES = 6  # Was 4
```

### Nieuwe Quick Actions
Voeg toe in `constants.py`:
```python
QUICK_ACTIONS.append({
    "name": "My Action",
    "icon": "🚀",
    "hotkey": "ctrl+alt+x"
})
```

### Serial Protocol Aanpassen
Pas aan in `serial_manager.py` en je Arduino/Pico code:
```python
# Nieuw commando toevoegen
def send_custom_command(self, data):
    return self.send_message(f"CUSTOM:{data}")
```

## Troubleshooting

### "No devices found"
- Controleer of Arduino/Pico aangesloten is
- Controleer of juiste drivers geïnstalleerd zijn
- Check Device Manager (Windows)

### Audio apps niet gevonden
- Installeer pycaw: `pip install pycaw`
- Start apps met audio sessies
- Check of apps daadwerkelijk audio afspelen

### Config wordt niet opgeslagen
- Check write permissions in folder
- Kijk of `streamdeck_config.json` bestaat
- Check console voor error messages

### UI reageert niet
- Check of event handlers correct gebind zijn
- Kijk naar console voor exceptions
- Test met `print()` statements
