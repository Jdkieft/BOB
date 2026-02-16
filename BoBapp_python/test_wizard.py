"""
Test Script voor Wizard Button Config Dialog

Run dit script om de nieuwe wizard-style dialog te testen.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import customtkinter as ctk
from dialogs_wizard import WizardButtonConfigDialog

# Zet appearance mode
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def on_save(config):
    """Callback wanneer config wordt opgeslagen."""
    print("✅ Configuration saved!")
    print(f"   Icon: {config['icon']}")
    print(f"   Label: {config['label']}")
    print(f"   Hotkey: {config['hotkey']}")


def on_clear():
    """Callback wanneer button wordt gewist."""
    print("🗑️ Button cleared!")


# Maak hoofdvenster
root = ctk.CTk()
root.title("Wizard Dialog Test")
root.geometry("400x300")

# Header
header = ctk.CTkLabel(
    root,
    text="🧙 Wizard Button Config Dialog",
    font=("Roboto", 24, "bold")
)
header.pack(pady=30)

# Info
info = ctk.CTkLabel(
    root,
    text="Test de nieuwe wizard-style dialog!\n\nKlik op een knop hieronder om te beginnen:",
    font=("Roboto", 13),
    justify="center"
)
info.pack(pady=20)

# Test button 1: Nieuwe config
def open_new_config():
    dialog = WizardButtonConfigDialog(
        parent=root,
        button_index=0,
        mode=0,
        current_config=None,  # Geen bestaande config
        on_save=on_save,
        on_clear=on_clear
    )

btn1 = ctk.CTkButton(
    root,
    text="➕ New Button Configuration",
    command=open_new_config,
    height=50,
    font=("Roboto", 14, "bold"),
    fg_color="green",
    hover_color="darkgreen"
)
btn1.pack(pady=10, padx=30, fill="x")

# Test button 2: Bestaande config bewerken
def open_edit_config():
    existing_config = {
        'icon': '🎤',
        'label': 'Discord Mute',
        'hotkey': 'ctrl+shift+m'
    }
    
    dialog = WizardButtonConfigDialog(
        parent=root,
        button_index=3,
        mode=1,
        current_config=existing_config,  # Bestaande config
        on_save=on_save,
        on_clear=on_clear
    )

btn2 = ctk.CTkButton(
    root,
    text="✏️ Edit Existing Configuration",
    command=open_edit_config,
    height=50,
    font=("Roboto", 14, "bold")
)
btn2.pack(pady=10, padx=30, fill="x")

# Start app
root.mainloop()
