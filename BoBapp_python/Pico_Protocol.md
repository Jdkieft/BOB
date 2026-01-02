# Stream Deck Pico - Serial Protocol Documentatie

## 📡 Communicatie Specificaties

- **Baudrate**: 9600
- **Data bits**: 8
- **Parity**: None
- **Stop bits**: 1
- **Line ending**: `\n` (newline)
- **Encoding**: UTF-8

---

## 📨 Commando Formaat

Alle commando's zijn **text-based** en eindigen met `\n`:

```
COMMANDO:parameter1:parameter2:parameter3\n
```

**Scheiding**: Gebruik `:` (dubbele punt) als separator

---

## 📋 Synchronisatie Flow

### **Bij Opstarten/Verbinden:**
1. Pico stuurt `READY\n`
2. PC stuurt `SYNC_START\n`
3. PC stuurt `MODE_COUNT:X\n`
4. PC stuurt alle `MODE_NAME:X:name\n`
5. PC stuurt alle `BTN:mode:button:hotkey:label\n`
6. PC stuurt alle `SLIDER:X:app\n`
7. PC stuurt `SYNC_END\n`
8. Pico stuurt `ACK:SYNC_COMPLETE\n`

### **Belangrijke Regel:**
⚠️ **Pico slaat NIETS op in EEPROM!** Alle data blijft in RAM.
Bij reset/power loss moet de PC opnieuw synchroniseren.

---

## 🎮 Commando's van PC → Pico

### 1️⃣ **BTN** - Button Configuratie
Configureer een button met hotkey en label.

**Format:**
```
BTN:mode:button:hotkey:label\n
```

**Parameters:**
- `mode`: Mode nummer (0-3)
- `button`: Button nummer (0-8)
- `hotkey`: Hotkey string (bijv. "ctrl+shift+m")
- `label`: Beschrijving (bijv. "Discord Mute")

**Voorbeelden:**
```
BTN:0:0:ctrl+shift+m:Discord Mute\n
BTN:0:1:ctrl+shift+d:Discord Deafen\n
BTN:1:5:f13:OBS Record\n
BTN:2:8:volumeup:Volume Up\n
```

**Pico actie:**
- Sla configuratie op in memory/EEPROM
- Update display (indien aanwezig)
- Stuur bevestiging terug (optioneel)

---

### 2️⃣ **MODE** - Mode Wissel
Wissel naar een andere mode.

**Format:**
```
MODE:mode\n
```

**Parameters:**
- `mode`: Mode nummer (0 tot num_modes-1)

**Voorbeelden:**
```
MODE:0\n
MODE:1\n
MODE:2\n
```

**Pico actie:**
- Valideer dat mode < num_modes
- Switch naar opgegeven mode
- Laad button configuraties voor die mode
- Update LEDs/display indien aanwezig
- Stuur `ACK:MODE:X` terug

---

### 3️⃣ **MODE_COUNT** - Aantal Modes Instellen
Vertelt Pico hoeveel modes er totaal zijn.

**Format:**
```
MODE_COUNT:count\n
```

**Parameters:**
- `count`: Totaal aantal modes (1-10)

**Voorbeelden:**
```
MODE_COUNT:4\n
MODE_COUNT:7\n
```

**Pico actie:**
- Sla num_modes op in RAM
- Resize/initialize mode arrays indien nodig
- Valideer toekomstige mode switches tegen dit getal
- Stuur `ACK:MODE_COUNT:X` terug

---

### 4️⃣ **MODE_NAME** - Mode Naam Instellen (NIEUW!)
Geef een mode een custom naam voor display.

**Format:**
```
MODE_NAME:mode:name\n
```

**Parameters:**
- `mode`: Mode nummer (0-9)
- `name`: Custom naam (max 20 karakters, UTF-8)

**Voorbeelden:**
```
MODE_NAME:0:Gaming\n
MODE_NAME:1:Streaming\n
MODE_NAME:2:Work Mode\n
MODE_NAME:3:🎵 Music\n
```

**Pico actie:**
- Sla mode naam op in RAM
- Update display indien aanwezig
- Mode naam kan emoji's bevatten (UTF-8 support)
- Stuur `ACK:MODE_NAME:mode` terug

**Let op:**
- Als geen MODE_NAME gestuurd wordt, gebruik "Mode X" als default
- Namen mogen spaties en emoji's bevatten
- Parsing: alles na tweede `:` is de naam (inclusief spaties)

---

### 5️⃣ **SLIDER** - Slider Configuratie
Koppel een slider aan een applicatie.

**Format:**
```
SLIDER:slider:app_name\n
```

**Parameters:**
- `slider`: Slider nummer (0-2)
- `app_name`: Applicatie naam (bijv. "Discord.exe")

**Voorbeelden:**
```
SLIDER:0:Discord.exe\n
SLIDER:1:Spotify.exe\n
SLIDER:2:Master Volume\n
```

**Pico actie:**
- Sla app assignment op
- Start met monitoren van slider positie
- Stuur slider updates naar PC

---

### 6️⃣ **CLEAR** - Clear Button
Wis een button configuratie.

**Format:**
```
CLEAR:mode:button\n
```

**Parameters:**
- `mode`: Mode nummer (0-9)
- `button`: Button nummer (0-8)

**Voorbeelden:**
```
CLEAR:0:0\n
CLEAR:1:5\n
```

**Pico actie:**
- Verwijder configuratie uit RAM
- Reset button naar default state
- Update display
- Stuur `ACK:CLEAR:mode:button` terug

---

### 7️⃣ **SYNC_START** - Start Synchronisatie (NIEUW!)
PC begint met synchroniseren van alle data.

**Format:**
```
SYNC_START\n
```

**Pico actie:**
- Wis alle huidige configuraties uit RAM
- Zet sync mode aan (wacht op data)
- Stuur `ACK:SYNC_START` terug
- Buffer alle inkomende commands tot SYNC_END

**Waarom?**
- Zorgt voor clean slate bij verbinding
- Voorkomt partial/corrupt configs
- Alle data komt in één sessie binnen

---

### 8️⃣ **SYNC_END** - Einde Synchronisatie (NIEUW!)
PC is klaar met synchroniseren.

**Format:**
```
SYNC_END\n
```

**Pico actie:**
- Verwerk alle gebufferde commands
- Valideer ontvangen data
- Zet sync mode uit
- Stuur `ACK:SYNC_COMPLETE` terug
- Systeem is nu klaar voor gebruik

---

### 9️⃣ **PING** - Connection Test
Test of verbinding actief is.

**Format:**
```
PING\n
```

**Pico actie:**
- Stuur onmiddellijk `PONG\n` terug

---

### 🔟 **RESET** - Reset All
Reset alle configuraties naar default.

**Format:**
```
RESET\n
```

**Pico actie:**
- Wis alle button configuraties uit RAM
- Wis alle slider configuraties uit RAM
- Wis alle mode namen uit RAM
- Reset naar Mode 0
- Reset num_modes naar 1
- Stuur `ACK:RESET` terug

**Waarom?**
- Debugging/troubleshooting
- Factory reset functie
- Na RESET moet PC opnieuw SYNC_START sturen

---

## 📤 Commando's van Pico → PC

### 1️⃣ **READY** - Opstarten Compleet (AANGEPAST!)
Stuur wanneer Pico klaar is.

**Format:**
```
READY:version\n
```

**Parameters:**
- `version`: Firmware versie (optioneel, bijv. "1.0.0")

**Voorbeelden:**
```
READY:1.0.0\n
READY\n
```

**PC actie:**
- Log firmware versie
- Start SYNC_START procedure
- Begin met synchroniseren van configuraties

**Belangrijke timing:**
- Pico stuurt READY na boot/reset
- PC wacht op READY voordat sync begint
- Als PC geen READY krijgt binnen 5 sec → timeout error
Stuur wanneer een button wordt ingedrukt.

**Format:**
```
BTN_PRESS:mode:button\n
```

**Voorbeelden:**
```
BTN_PRESS:0:0\n
BTN_PRESS:1:5\n
```

**PC actie:**
- Trigger de hotkey voor deze button
- Optioneel: stuur `ACK:BTN_PRESS:mode:button` terug

---

### 3️⃣ **SLIDER_CHANGE** - Slider Positie
Stuur wanneer een slider beweegt.

**Format:**
```
SLIDER_CHANGE:slider:value\n
```

**Parameters:**
- `slider`: Slider nummer (0-2)
- `value`: Waarde 0-1023 (of 0-100 voor percentage)

**Voorbeelden:**
```
SLIDER_CHANGE:0:512\n
SLIDER_CHANGE:1:768\n
SLIDER_CHANGE:2:0\n
```

**PC actie:**
- Update volume van gekoppelde app
- Update UI progress bar

---

### 4️⃣ **MODE_CHANGE** - Mode Gewisseld
Stuur wanneer user handmatig mode wisselt op Pico.

**Format:**
```
MODE_CHANGE:mode\n
```

**Voorbeelden:**
```
MODE_CHANGE:1\n
MODE_CHANGE:3\n
```

**PC actie:**
- Update UI naar juiste mode
- Laad button states voor die mode

---

### 5️⃣ **ACK** - Acknowledge
Bevestig dat commando ontvangen is.

**Format:**
```
ACK:command:parameters\n
```

**Voorbeelden:**
```
ACK:BTN:0:0\n
ACK:MODE:2\n
ACK:RESET\n
```

**Speciale ACKs:**
```
ACK:SYNC_START\n          # Klaar om te ontvangen
ACK:SYNC_COMPLETE\n       # All data ontvangen & verwerkt
ACK:MODE_COUNT:5\n        # Mode count ingesteld op 5
ACK:MODE_NAME:2\n         # Mode 2 naam ontvangen
```

---

### 6️⃣ **ERROR** - Error Melding
Stuur bij een fout.

**Format:**
```
ERROR:code:message\n
```

**Voorbeelden:**
```
ERROR:1:Invalid mode number\n
ERROR:2:Button not configured\n
ERROR:3:Parse error\n
```

---

### 6️⃣ **READY** - Opstarten Compleet
Stuur wanneer Pico klaar is.

**Format:**
```
READY\n
```

**PC actie:**
- Begin met synchroniseren van configuraties

---

## 🔄 Typische Message Flow

### **Opstarten:**
```
[Pico → PC] READY:1.0.0\n
[PC → Pico] SYNC_START\n
[Pico → PC] ACK:SYNC_START\n

[PC → Pico] MODE_COUNT:4\n
[Pico → PC] ACK:MODE_COUNT:4\n

[PC → Pico] MODE_NAME:0:🎮 Gaming\n
[Pico → PC] ACK:MODE_NAME:0\n
[PC → Pico] MODE_NAME:1:🎙️ Streaming\n
[Pico → PC] ACK:MODE_NAME:1\n
[PC → Pico] MODE_NAME:2:💼 Work\n
[Pico → PC] ACK:MODE_NAME:2\n
[PC → Pico] MODE_NAME:3:🎵 Music\n
[Pico → PC] ACK:MODE_NAME:3\n

[PC → Pico] BTN:0:0:ctrl+shift+m:Discord Mute\n
[Pico → PC] ACK:BTN:0:0\n
[PC → Pico] BTN:0:1:ctrl+shift+d:Discord Deafen\n
[Pico → PC] ACK:BTN:0:1\n
... (alle geconfigureerde buttons)

[PC → Pico] SLIDER:0:Discord.exe\n
[Pico → PC] ACK:SLIDER:0\n
[PC → Pico] SLIDER:1:Spotify.exe\n
[Pico → PC] ACK:SLIDER:1\n
[PC → Pico] SLIDER:2:Master Volume\n
[Pico → PC] ACK:SLIDER:2\n

[PC → Pico] SYNC_END\n
[Pico → PC] ACK:SYNC_COMPLETE\n

✅ Systeem klaar voor gebruik!
```

### **Runtime - Button Press:**
```
[Pico → PC] BTN_PRESS:0:0\n
[PC → Pico] ACK:BTN_PRESS:0:0\n
```

### **Runtime - Mode Switch:**
```
[PC → Pico] MODE:1\n
[Pico → PC] ACK:MODE:1\n
```

### **Runtime - User Renames Mode in PC:**
```
[PC → Pico] MODE_NAME:2:💻 Coding\n
[Pico → PC] ACK:MODE_NAME:2\n
```

### **Runtime - User Adds Mode in PC:**
```
[PC → Pico] MODE_COUNT:5\n
[Pico → PC] ACK:MODE_COUNT:5\n
[PC → Pico] MODE_NAME:4:New Mode\n
[Pico → PC] ACK:MODE_NAME:4\n
```

### **Runtime - User Removes Mode in PC:**
```
[PC → Pico] MODE_COUNT:3\n
[Pico → PC] ACK:MODE_COUNT:3\n
[PC → Pico] CLEAR:2:0\n    # Clear all buttons in removed mode
[PC → Pico] CLEAR:2:1\n
... (all 9 buttons)
```

---

## 💾 Pico Data Structuur (RAM Only!)

### **In Memory (RAM) - GEEN EEPROM!**
```
[Pico → PC] SLIDER_CHANGE:0:512\n
[Pico → PC] SLIDER_CHANGE:0:513\n
[Pico → PC] SLIDER_CHANGE:0:514\n
```

---

## ⚠️ Error Handling

### **Pico moet checken:**
- Mode nummer tussen 0-3
- Button nummer tussen 0-8
- Slider nummer tussen 0-2
- Commando's correct formatted

### **Bij fouten:**
```
ERROR:code:message\n
```

**Error Codes:**
- `1`: Invalid parameter
- `2`: Unknown command
- `3`: Parse error
- `4`: Not configured
- `5`: Hardware error

```c
// Button configuration
struct ButtonConfig {
    bool configured;
    char hotkey[64];
    char label[64];
};

// Mode configuration
struct ModeConfig {
    char name[24];  // UTF-8, max 20 chars + null terminator + buffer
    ButtonConfig buttons[9];
};

// Global state (RAM ONLY!)
ModeConfig modes[10];       // Max 10 modes
char slider_apps[3][64];    // 3 sliders
int num_modes;              // Current number of modes
int current_mode;           // Currently active mode
bool in_sync;               // True tijdens SYNC_START...SYNC_END

// IMPORTANT: NO EEPROM/FLASH WRITES!
// All data is lost on reset/power cycle
// PC must re-sync on every connection
```

### **Waarom geen EEPROM?**
- ✅ **Flexibiliteit**: Geen limiet op aantal updates
- ✅ **Snelheid**: Geen write delays
- ✅ **Betrouwbaarheid**: Geen wear-out van flash
- ✅ **Eenvoud**: Geen persistence layer nodig
- ✅ **Toekomstbestendig**: Makkelijk uit te breiden

### **Wat gebeurt bij reset?**
1. Pico reset → alle RAM gewist
2. Pico stuurt `READY\n`
3. PC detecteert READY
4. PC start volledige SYNC procedure
5. Binnen ~1 seconde is alles weer gesynchroniseerd

---

## 🧪 Test Commando's (Handmatig)

Voor debugging kun je deze handmatig sturen via Serial Monitor:

```
SYNC_START\n
MODE_COUNT:3\n
MODE_NAME:0:Gaming\n
MODE_NAME:1:Work\n
MODE_NAME:2:Music\n
BTN:0:0:ctrl+m:Test Button\n
MODE:1\n
SLIDER:0:Discord.exe\n
SYNC_END\n
PING\n
CLEAR:0:0\n
RESET\n
```

---

## 📝 Implementatie Tips (PC Kant)
```python
serial_port.write(b"BTN:0:0:ctrl+m:Test\n")
response = serial_port.readline().decode('utf-8').strip()
```

### **C/C++ (Pico kant):**
```c
void parse_command(char* line) {
    char* token = strtok(line, ":");
    
    if (strcmp(token, "BTN") == 0) {
        int mode = atoi(strtok(NULL, ":"));
        int button = atoi(strtok(NULL, ":"));
        char* hotkey = strtok(NULL, ":");
        char* label = strtok(NULL, ":");
        
        // Sla op in struct
        buttons[mode][button].configured = true;
        strcpy(buttons[mode][button].hotkey, hotkey);
        strcpy(buttons[mode][button].label, label);
    }
    else if (strcmp(token, "MODE") == 0) {
        current_mode = atoi(strtok(NULL, ":"));
    }
    // etc...
}
```

### **MicroPython (Pico kant):**
```python
def parse_command(line):
    parts = line.strip().split(':')
    
    if parts[0] == 'BTN':
        mode = int(parts[1])
        button = int(parts[2])
        hotkey = parts[3]
        label = parts[4]
        
        buttons[mode][button] = {
            'hotkey': hotkey,
            'label': label
        }
    
    elif parts[0] == 'MODE':
        current_mode = int(parts[1])
```

---

## ✅ Checklist voor Pico Code

- [ ] Serial initialisatie op 9600 baud
- [ ] Command parser (split op `:`)
- [ ] Button state array (4 modes × 9 buttons)
- [ ] Slider reading (3 analog inputs)
- [ ] Mode switching logic
- [ ] Stuur `READY` bij opstarten
- [ ] Stuur `BTN_PRESS` bij button press
- [ ] Stuur `SLIDER_CHANGE` bij slider movement
- [ ] Error handling met `ERROR` messages

