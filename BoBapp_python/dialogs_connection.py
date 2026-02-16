"""
Connection Dialog - COM Port Selector

Dit venster laat de gebruiker een COM poort kiezen die persistent wordt
onthouden en automatisch reconnect als de verbinding verbroken is.

Features:
- Dropdown met beschikbare COM poorten
- Auto-refresh van beschikbare poorten
- Persistent opslaan van gekozen poort
- Visuele status indicator
- Auto-reconnect in de achtergrond
"""

import customtkinter as ctk
from typing import Callable, List, Tuple, Optional


class ConnectionDialog(ctk.CTkToplevel):
    """
    Dialog voor het kiezen van een COM poort met auto-reconnect.
    
    Attributes:
        serial_manager: SerialManager instance
        config_manager: ConfigManager instance
        on_port_selected: Callback die aangeroepen wordt bij poort selectie
        port_var: StringVar voor de geselecteerde poort
        port_menu: Dropdown menu met COM poorten
        status_label: Label met connection status
        refresh_timer: After timer voor auto-refresh
    """
    
    def __init__(
        self,
        parent,
        serial_manager,
        config_manager,
        on_port_selected: Optional[Callable[[str], None]] = None
    ):
        """
        Initialiseer de connection dialog.
        
        Args:
            parent: Parent window
            serial_manager: SerialManager instance
            config_manager: ConfigManager instance
            on_port_selected: Callback (port_name) wanneer poort gekozen wordt
        """
        super().__init__(parent)
        
        self.serial_manager = serial_manager
        self.config_manager = config_manager
        self.on_port_selected = on_port_selected
        
        # Window configuratie
        self.title("🔌 COM Port Configuration")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        # Haal huidige preferred port op
        self.preferred_port = config_manager.get_preferred_port()
        
        # Setup UI
        self._create_widgets()
        
        # Start auto-refresh
        self._schedule_refresh()
        
        # Initial port scan
        self._refresh_ports()
    
    def _create_widgets(self):
        """Maak alle UI elementen."""
        
        # Header
        header = ctk.CTkLabel(
            self,
            text="🔌 COM Port Configuration",
            font=("Roboto", 24, "bold")
        )
        header.pack(pady=20)
        
        # Info text
        info = ctk.CTkLabel(
            self,
            text="Kies een COM poort voor je Stream Deck.\n"
                 "Het programma zal automatisch blijven proberen\n"
                 "te verbinden met de gekozen poort.",
            font=("Roboto", 12),
            text_color="gray"
        )
        info.pack(pady=10)
        
        # Current status
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.pack(pady=15, fill="x", padx=30)
        
        ctk.CTkLabel(
            status_frame,
            text="Huidige status:",
            font=("Roboto", 11, "bold")
        ).pack(side="left", padx=5)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="❌ Niet verbonden",
            font=("Roboto", 11, "bold"),
            text_color="red"
        )
        self.status_label.pack(side="left", padx=5)
        
        # Separator
        separator = ctk.CTkFrame(self, height=2, fg_color="gray")
        separator.pack(fill="x", padx=30, pady=10)
        
        # Port selector
        selector_frame = ctk.CTkFrame(self, fg_color="transparent")
        selector_frame.pack(pady=15, fill="x", padx=30)
        
        ctk.CTkLabel(
            selector_frame,
            text="Selecteer COM Poort:",
            font=("Roboto", 13, "bold")
        ).pack(pady=5)
        
        self.port_var = ctk.StringVar(value=self.preferred_port if self.preferred_port else "Selecteer een poort...")
        
        self.port_menu = ctk.CTkOptionMenu(
            selector_frame,
            variable=self.port_var,
            values=["Scanning..."],
            width=350,
            height=40,
            font=("Roboto", 12),
            command=self._on_port_select
        )
        self.port_menu.pack(pady=10)
        
        # Info over current selection
        if self.preferred_port:
            info_text = f"💾 Opgeslagen poort: {self.preferred_port}"
        else:
            info_text = "⚠️ Nog geen poort geselecteerd"
        
        self.saved_port_label = ctk.CTkLabel(
            selector_frame,
            text=info_text,
            font=("Roboto", 10),
            text_color="gray"
        )
        self.saved_port_label.pack(pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20, side="bottom", fill="x", padx=30)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Ververs Poorten",
            command=self._refresh_ports,
            width=150,
            height=40,
            font=("Roboto", 12)
        )
        refresh_btn.pack(side="left", padx=5)
        
        # Close button
        close_btn = ctk.CTkButton(
            button_frame,
            text="✅ Sluiten",
            command=self.destroy,
            width=150,
            height=40,
            font=("Roboto", 12),
            fg_color="green",
            hover_color="darkgreen"
        )
        close_btn.pack(side="right", padx=5)
    
    def _refresh_ports(self):
        """Ververs de lijst van beschikbare COM poorten."""
        ports = self.serial_manager.get_available_ports()
        
        if ports:
            # Update menu met beschikbare poorten
            port_names = [f"{port[0]} - {port[1]}" for port in ports]
            self.port_menu.configure(values=port_names)
            
            # Als preferred port beschikbaar is, selecteer die
            if self.preferred_port:
                for port_option in port_names:
                    if self.preferred_port in port_option:
                        self.port_var.set(port_option)
                        break
        else:
            self.port_menu.configure(values=["❌ Geen poorten gevonden"])
            self.port_var.set("❌ Geen poorten gevonden")
        
        # Update status
        self._update_status()
    
    def _on_port_select(self, selected: str):
        """
        Handler voor port selectie.
        
        Args:
            selected: De geselecteerde optie uit het menu
        """
        if "❌" in selected or "Selecteer" in selected or "Scanning" in selected:
            return
        
        # Extract COM port name (bijv. "COM3 - USB Serial" -> "COM3")
        port_name = selected.split(" - ")[0].strip()
        
        print(f"📌 User selected port: {port_name}")
        
        # Sla op in config
        self.config_manager.set_preferred_port(port_name)
        self.preferred_port = port_name
        
        # Update saved port label
        self.saved_port_label.configure(
            text=f"💾 Opgeslagen poort: {port_name}"
        )
        
        # Start auto-reconnect met deze poort
        self.serial_manager.stop_auto_reconnect()
        self.serial_manager.start_auto_reconnect(port_name)
        
        # Callback
        if self.on_port_selected:
            self.on_port_selected(port_name)
        
        print(f"✅ Auto-reconnect gestart voor {port_name}")
    
    def _update_status(self):
        """Update de connection status label met meer details."""
        status = self.serial_manager.get_connection_status()
        
        if self.serial_manager.is_connected and status['connected']:
            # Verbonden en gezond
            self.status_label.configure(
                text="✅ Verbonden & Actief",
                text_color="green"
            )
        elif status['reconnect_active'] and self.preferred_port:
            # Auto-reconnect actief maar nog niet verbonden
            self.status_label.configure(
                text=f"🔄 Zoeken naar {self.preferred_port}...",
                text_color="orange"
            )
        else:
            # Niet verbonden
            if self.preferred_port:
                self.status_label.configure(
                    text=f"❌ Niet verbonden met {self.preferred_port}",
                    text_color="red"
                )
            else:
                self.status_label.configure(
                    text="❌ Niet verbonden",
                    text_color="red"
                )
    
    def _schedule_refresh(self):
        """Schedule een periodieke refresh van de status."""
        self._update_status()
        
        # Schedule next update (elke 1 seconde)
        self.refresh_timer = self.after(1000, self._schedule_refresh)
    
    def destroy(self):
        """Clean up bij sluiten van dialog."""
        # Cancel scheduled refresh
        if hasattr(self, 'refresh_timer'):
            self.after_cancel(self.refresh_timer)
        
        super().destroy()
