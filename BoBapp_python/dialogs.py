"""
Dialog Windows
"""

import sys
from pathlib import Path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

import customtkinter as ctk
from typing import Callable, Optional, Dict, List, Tuple

from constants import (
    COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK,
    HOTKEY_INFO_TEXT, MSG_EMPTY_HOTKEY
)


class ButtonConfigDialog:
    """Dialog voor het configureren van een button."""
    
    def __init__(
        self,
        parent: ctk.CTk,
        button_index: int,
        mode: int,
        current_config: Optional[Dict[str, str]],
        on_save: Callable[[Dict[str, str]], None],
        on_clear: Optional[Callable[[], None]] = None
    ):
        self.on_save = on_save
        self.on_clear = on_clear
        
        # Maak toplevel dialog
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(f"Configure Button {button_index + 1}")
        self.dialog.geometry("600x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Header
        self._create_header(button_index, mode)
        
        # Content area (scrollable)
        self.content = ctk.CTkScrollableFrame(self.dialog)
        self.content.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Create input fields
        self.icon_entry = self._create_icon_input(current_config)
        self.label_entry = self._create_label_input(current_config)
        
        # Create hotkey builder
        self.modifier_vars = self._create_hotkey_builder(current_config)
        self.key_entry = self._create_key_input(current_config)
        
        # Create preview
        self.preview_label = self._create_preview()
        
        # Bind updates
        self._bind_preview_updates()
        self._update_preview()
        
        # Info text
        self._create_info_text()
        
        # Buttons
        self._create_buttons(current_config)
    
    def _create_header(self, button_index: int, mode: int) -> None:
        """Maak header met titel."""
        header_frame = ctk.CTkFrame(
            self.dialog,
            fg_color=(COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK)
        )
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header_frame,
            text=f"Button {button_index + 1} - Mode {mode + 1}",
            font=("Roboto", 24, "bold")
        ).pack(pady=20)
    
    def _create_icon_input(self, current_config: Optional[Dict]) -> ctk.CTkEntry:
        """Maak icon input field."""
        ctk.CTkLabel(
            self.content,
            text="Icon:",
            font=("Roboto", 14, "bold")
        ).pack(pady=(15, 5), anchor="w")
        
        icon_entry = ctk.CTkEntry(
            self.content,
            width=500,
            height=45,
            placeholder_text="🎮",
            font=("Segoe UI Emoji", 16)
        )
        if current_config:
            icon_entry.insert(0, current_config.get('icon', ''))
        icon_entry.pack(pady=5)
        
        return icon_entry
    
    def _create_label_input(self, current_config: Optional[Dict]) -> ctk.CTkEntry:
        """Maak label input field."""
        ctk.CTkLabel(
            self.content,
            text="Label:",
            font=("Roboto", 14, "bold")
        ).pack(pady=(15, 5), anchor="w")
        
        label_entry = ctk.CTkEntry(
            self.content,
            width=500,
            height=45,
            placeholder_text="Discord Mute",
            font=("Roboto", 14)
        )
        if current_config:
            label_entry.insert(0, current_config.get('label', ''))
        label_entry.pack(pady=5)
        
        return label_entry
    
    def _create_hotkey_builder(
        self,
        current_config: Optional[Dict]
    ) -> Dict[str, ctk.BooleanVar]:
        """Maak hotkey modifier checkboxes."""
        ctk.CTkLabel(
            self.content,
            text="Hotkey Combinatie:",
            font=("Roboto", 14, "bold")
        ).pack(pady=(20, 5), anchor="w")
        
        # Haal huidige hotkey op
        current_hotkey = current_config.get('hotkey', '') if current_config else ''
        
        # Modifier frame
        modifier_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        modifier_frame.pack(fill="x", pady=5)
        
        # Maak variables en checkboxes
        modifiers = {
            'ctrl': ctk.BooleanVar(value='ctrl' in current_hotkey),
            'shift': ctk.BooleanVar(value='shift' in current_hotkey),
            'alt': ctk.BooleanVar(value='alt' in current_hotkey),
            'win': ctk.BooleanVar(value='win' in current_hotkey)
        }
        
        for name, var in modifiers.items():
            ctk.CTkCheckBox(
                modifier_frame,
                text=name.capitalize(),
                variable=var,
                font=("Roboto", 13)
            ).pack(side="left", padx=10)
        
        return modifiers
    
    def _create_key_input(self, current_config: Optional[Dict]) -> ctk.CTkEntry:
        """Maak main key input field."""
        ctk.CTkLabel(
            self.content,
            text="Main Key:",
            font=("Roboto", 12)
        ).pack(pady=(10, 5), anchor="w")
        
        # Extract main key van hotkey
        main_key = ""
        if current_config:
            current_hotkey = current_config.get('hotkey', '')
            if current_hotkey:
                parts = current_hotkey.split('+')
                if parts:
                    main_key = parts[-1]
        
        key_entry = ctk.CTkEntry(
            self.content,
            width=500,
            height=45,
            placeholder_text="For Example: m, f13, volumeup",
            font=("Courier", 14)
        )
        key_entry.insert(0, main_key)
        key_entry.pack(pady=5)
        
        return key_entry
    
    def _create_preview(self) -> ctk.CTkLabel:
        """Maak hotkey preview label."""
        preview_label = ctk.CTkLabel(
            self.content,
            text="Preview: -",
            font=("Courier", 12, "bold"),
            fg_color=(COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK),
            corner_radius=8,
            height=40
        )
        preview_label.pack(pady=10, fill="x")
        return preview_label
    
    def _bind_preview_updates(self) -> None:
        """Bind events voor preview updates."""
        for var in self.modifier_vars.values():
            var.trace_add("write", lambda *args: self._update_preview())
        
        self.key_entry.bind("<KeyRelease>", lambda e: self._update_preview())
    
    def _update_preview(self) -> None:
        """Update de hotkey preview."""
        parts = []
        
        # Voeg modifiers toe
        for name, var in self.modifier_vars.items():
            if var.get():
                parts.append(name)
        
        # Voeg main key toe
        key = self.key_entry.get().strip().lower()
        if key:
            parts.append(key)
        
        # Update preview
        hotkey = "+".join(parts) if parts else "-"
        self.preview_label.configure(text=f"Preview: {hotkey}")
    
    def _create_info_text(self) -> None:
        """Maak info text met beschikbare keys."""
        ctk.CTkLabel(
            self.content,
            text=HOTKEY_INFO_TEXT,
            font=("Courier", 9),
            text_color="gray",
            justify="left"
        ).pack(pady=10, anchor="w")
    
    def _create_buttons(self, current_config: Optional[Dict]) -> None:
        """Maak save en clear buttons."""
        # Save button
        save_btn = ctk.CTkButton(
            self.dialog,
            text="💾 Save Configuration",
            command=self._handle_save,
            height=55,
            font=("Roboto", 16, "bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        save_btn.pack(pady=15, padx=20, fill="x")
        
        # Clear button (alleen als geconfigureerd)
        if current_config and self.on_clear:
            delete_btn = ctk.CTkButton(
                self.dialog,
                text="🗑️ Clear Button",
                command=self._handle_clear,
                height=45,
                font=("Roboto", 16, "bold"),
                fg_color="red",
                hover_color="darkred"
            )
            delete_btn.pack(pady=(0, 20), padx=20, fill="x")
    
    def _handle_save(self) -> None:
        """Handle save button click."""
        # Valideer en bouw config
        icon = self.icon_entry.get().strip() or '🎮'
        label = self.label_entry.get().strip() or 'Unnamed'
        
        # Bouw hotkey
        parts = []
        for name, var in self.modifier_vars.items():
            if var.get():
                parts.append(name)
        
        key = self.key_entry.get().strip().lower()
        if key:
            parts.append(key)
        
        hotkey = "+".join(parts)
        
        # Valideer
        if not hotkey or not key:
            error_label = ctk.CTkLabel(
                self.content,
                text=MSG_EMPTY_HOTKEY,
                font=("Roboto", 12, "bold"),
                text_color="red"
            )
            error_label.pack(pady=10)
            self.dialog.after(2000, error_label.destroy)
            return
        
        # Maak config dict
        new_config = {
            'icon': icon,
            'label': label,
            'hotkey': hotkey
        }
        
        # Call callback
        if self.on_save:
            self.on_save(new_config)
        
        # Sluit dialog
        self.dialog.destroy()
    
    def _handle_clear(self) -> None:
        """Handle clear button click."""
        if self.on_clear:
            self.on_clear()
        self.dialog.destroy()


class SerialPortDialog:
    """Dialog voor het selecteren van een seriële poort."""
    
    def __init__(
        self,
        parent: ctk.CTk,
        ports: List[Tuple[str, str]],
        on_connect: Callable[[str], None]
    ):
        self.ports = ports
        self.on_connect = on_connect
        
        # Maak dialog
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Select Device")
        self.dialog.geometry("450x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Header
        ctk.CTkLabel(
            self.dialog,
            text="🔌 Select Serial Port:",
            font=("Roboto", 18, "bold")
        ).pack(pady=20)
        
        # Port selection
        self.port_var = ctk.StringVar(value=ports[0][0] if ports else "")
        
        for device, description in ports:
            ctk.CTkRadioButton(
                self.dialog,
                text=f"{device} - {description}",
                variable=self.port_var,
                value=device,
                font=("Roboto", 12)
            ).pack(pady=8, padx=20, anchor="w")
        
        # Connect button
        ctk.CTkButton(
            self.dialog,
            text="Connect",
            command=self._handle_connect,
            height=50,
            font=("Roboto", 14, "bold")
        ).pack(pady=30)
    
    def _handle_connect(self) -> None:
        """Handle connect button click."""
        selected_port = self.port_var.get()
        if selected_port and self.on_connect:
            self.on_connect(selected_port)
        self.dialog.destroy()