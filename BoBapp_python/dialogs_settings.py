"""
Settings Dialog

Algemene instellingen voor de Stream Deck Manager:
- Verbinding (COM poort)
- Autostart met Windows
- Weergave (dark/light mode)
- Export / Import config
"""

import sys
from pathlib import Path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

import customtkinter as ctk
from typing import Optional, Callable

from autostart_manager import AutostartManager
from constants import APP_VERSION


class SettingsDialog(ctk.CTkToplevel):
    """
    Algemene instellingen dialog.

    Secties:
    - 🔌 Verbinding   — COM poort configureren
    - 🚀 Opstarten    — Autostart met Windows
    - 🎨 Weergave     — Dark / light mode
    - 💾 Configuratie — Export & import
    """

    # Kleur-palet: (light, dark) tuples zodat beide thema's goed werken
    C_CARD      = ("#e8e8e8", "#2b2b2b")
    C_CARD_SEP  = ("#c0c0c0", "#444444")
    C_BTN_MUTED = ("#d0d0d0", "#3a3a3a")
    C_BTN_HOVER = ("#b8b8b8", "#505050")
    C_BTN_TXT   = ("#111111", "#eeeeee")
    C_ICON_BTN  = ("#d8d8d8", "#383838")

    def __init__(
        self,
        parent,
        serial_manager,
        config_manager,
        on_port_selected: Optional[Callable[[str], None]] = None,
        on_export: Optional[Callable[[], None]] = None,
        on_import: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)

        self.parent = parent  # Store parent reference
        self.serial_manager   = serial_manager
        self.config_manager   = config_manager
        self.on_port_selected = on_port_selected
        self.on_export        = on_export
        self.on_import        = on_import

        self.title("⚙️ Instellingen")
        self.geometry("520x740")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - 260
        y = (self.winfo_screenheight() // 2) - 370
        self.geometry(f"520x740+{x}+{y}")

        self._build_ui()
        self._start_status_refresh()

    # ------------------------------------------------------------------ #
    #  UI bouwen                                                           #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        self._section_connection(scroll)
        self._spacer(scroll)
        self._section_startup(scroll)
        self._spacer(scroll)
        self._section_config(scroll)
        self._spacer(scroll)
        self._section_about(scroll)

        ctk.CTkButton(
            self,
            text="✅ Close",
            command=self.destroy,
            height=45,
            font=("Roboto", 14, "bold"),
            fg_color=("#2e7d32", "#2e7d32"),
            hover_color=("#1b5e20", "#1b5e20"),
            text_color="white"
        ).pack(fill="x", padx=20, pady=(0, 20))

    # ------------------------------------------------------------------ #
    #  Sectie: Verbinding                                                  #
    # ------------------------------------------------------------------ #

    def _section_connection(self, parent):
        frame = self._make_section(parent, "🔌 Connection")

        status_row = ctk.CTkFrame(frame, fg_color="transparent")
        status_row.pack(fill="x", padx=15, pady=(5, 8))

        ctk.CTkLabel(
            status_row, text="Status:",
            font=("Roboto", 12, "bold"), width=80, anchor="w"
        ).pack(side="left")

        self.conn_status_label = ctk.CTkLabel(
            status_row, text="Checking...",
            font=("Roboto", 12), anchor="w"
        )
        self.conn_status_label.pack(side="left")

        port_row = ctk.CTkFrame(frame, fg_color="transparent")
        port_row.pack(fill="x", padx=15, pady=(0, 8))

        ctk.CTkLabel(
            port_row, text="Port:",
            font=("Roboto", 12, "bold"), width=80, anchor="w"
        ).pack(side="left")

        preferred = self.config_manager.get_preferred_port()
        self.port_label = ctk.CTkLabel(
            port_row,
            text=preferred if preferred else "Not configured",
            font=("Roboto", 12), anchor="w"
        )
        self.port_label.pack(side="left")

        selector_row = ctk.CTkFrame(frame, fg_color="transparent")
        selector_row.pack(fill="x", padx=15, pady=(0, 15))

        ports = self.serial_manager.get_available_ports()
        port_options = [f"{p[0]} — {p[1]}" for p in ports] if ports else ["❌ No ports found"]

        self.port_var = ctk.StringVar()
        if preferred:
            for opt in port_options:
                if preferred in opt:
                    self.port_var.set(opt)
                    break
        if not self.port_var.get():
            self.port_var.set(port_options[0])

        self.port_menu = ctk.CTkOptionMenu(
            selector_row,
            variable=self.port_var,
            values=port_options,
            width=310,
            font=("Roboto", 12),
            command=self._on_port_select
        )
        self.port_menu.pack(side="left")

        ctk.CTkButton(
            selector_row,
            text="🔄", width=38, height=32,
            font=("Roboto", 14),
            command=self._refresh_ports,
            fg_color=self.C_ICON_BTN,
            hover_color=self.C_BTN_HOVER,
            text_color=self.C_BTN_TXT,
            border_width=0
        ).pack(side="left", padx=(8, 0))

    # ------------------------------------------------------------------ #
    #  Sectie: Opstarten                                                   #
    # ------------------------------------------------------------------ #

    def _section_startup(self, parent):
        frame = self._make_section(parent, "🚀 Startup")

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=15)

        text_col = ctk.CTkFrame(row, fg_color="transparent")
        text_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            text_col, text="Start with Windows",
            font=("Roboto", 13, "bold"), anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            text_col,
            text="Automatically start in the background\nwhen Windows starts.",
            font=("Roboto", 10), anchor="w", justify="left"
        ).pack(anchor="w")

        self.autostart_switch = ctk.CTkSwitch(
            row, text="", width=46,
            command=self._on_autostart_toggle
        )
        self.autostart_switch.pack(side="right", padx=(10, 0))

        if AutostartManager.is_enabled():
            self.autostart_switch.select()
        else:
            self.autostart_switch.deselect()

        if not AutostartManager.is_exe():
            ctk.CTkLabel(
                frame,
                text="⚠️  Only works with built .exe",
                font=("Roboto", 10), text_color="#e67e00", anchor="w"
            ).pack(padx=15, pady=(0, 12), anchor="w")

    # ------------------------------------------------------------------ #
    #  Sectie: Configuratie                                                #
    # ------------------------------------------------------------------ #

    def _section_config(self, parent):
        frame = self._make_section(parent, "💾 Configuration")

        ctk.CTkLabel(
            frame,
            text="Save your settings to a file or load a previously saved configuration.",
            font=("Roboto", 11), wraplength=440, justify="left", anchor="w"
        ).pack(padx=15, pady=(5, 15), anchor="w")

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            btn_row, text="📤 Export",
            command=self._do_export, height=42,
            font=("Roboto", 12, "bold"),
            fg_color=self.C_BTN_MUTED,
            hover_color=self.C_BTN_HOVER,
            text_color=self.C_BTN_TXT
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btn_row, text="📥 Import",
            command=self._do_import, height=42,
            font=("Roboto", 12, "bold"),
            fg_color=self.C_BTN_MUTED,
            hover_color=self.C_BTN_HOVER,
            text_color=self.C_BTN_TXT
        ).pack(side="right", expand=True, fill="x")

    # ------------------------------------------------------------------ #
    #  Sectie: About                                                       #
    # ------------------------------------------------------------------ #

    def _section_about(self, parent):
        frame = self._make_section(parent, "ℹ️ About")

        # Version info
        version_row = ctk.CTkFrame(frame, fg_color="transparent")
        version_row.pack(fill="x", padx=15, pady=(5, 8))

        ctk.CTkLabel(
            version_row, text="Version:",
            font=("Roboto", 12, "bold"), width=80, anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            version_row, text=f"v{APP_VERSION}",
            font=("Roboto Mono", 12), anchor="w"
        ).pack(side="left")

        # Check for updates button
        ctk.CTkButton(
            frame,
            text="🔍 Check for Updates",
            command=self._manual_check_updates,
            height=42,
            font=("Roboto", 12, "bold"),
            fg_color=self.C_BTN_MUTED,
            hover_color=self.C_BTN_HOVER,
            text_color=self.C_BTN_TXT
        ).pack(fill="x", padx=15, pady=(0, 8))

        # GitHub link
        ctk.CTkButton(
            frame,
            text="🌐 View on GitHub",
            command=self._open_github,
            height=42,
            font=("Roboto", 12, "bold"),
            fg_color=self.C_BTN_MUTED,
            hover_color=self.C_BTN_HOVER,
            text_color=self.C_BTN_TXT
        ).pack(fill="x", padx=15, pady=(0, 15))

    # ------------------------------------------------------------------ #
    #  Handlers                                                            #
    # ------------------------------------------------------------------ #

    def _on_port_select(self, selected: str):
        if "❌" in selected:
            return
        port_name = selected.split(" — ")[0].strip()
        self.config_manager.set_preferred_port(port_name)
        self.port_label.configure(text=port_name)
        self.serial_manager.stop_auto_reconnect()
        self.serial_manager.start_auto_reconnect(port_name)
        if self.on_port_selected:
            self.on_port_selected(port_name)

    def _refresh_ports(self):
        ports = self.serial_manager.get_available_ports()
        options = [f"{p[0]} — {p[1]}" for p in ports] if ports else ["❌ Geen poorten gevonden"]
        self.port_menu.configure(values=options)
        preferred = self.config_manager.get_preferred_port()
        if preferred:
            for opt in options:
                if preferred in opt:
                    self.port_var.set(opt)
                    return
        self.port_var.set(options[0])

    def _on_autostart_toggle(self):
        new_state = AutostartManager.toggle()
        if new_state:
            self.autostart_switch.select()
        else:
            self.autostart_switch.deselect()

    def _do_export(self):
        if self.on_export:
            self.on_export()

    def _do_import(self):
        if self.on_import:
            self.on_import()

    def _manual_check_updates(self):
        """Manually trigger update check."""
        if hasattr(self.parent, 'update_manager'):
            print("🔍 Manual update check triggered")
            
            # Disable button tijdens check
            # Note: we moeten de button widget opslaan als instance variable
            # voor nu gewoon direct checken
            
            # Check in background thread
            import threading
            def check_thread():
                has_update = self.parent.update_manager.check_for_updates(force=True)
                
                # Show result on main thread
                self.after(0, lambda: self._show_check_result(has_update))
            
            threading.Thread(target=check_thread, daemon=True).start()
            
            # Sluit dialog zodat update dialog kan verschijnen
            self.destroy()
        else:
            print("⚠️ Update manager not available")
    
    def _show_check_result(self, has_update: bool):
        """Show result of update check."""
        if not has_update:
            from tkinter import messagebox
            messagebox.showinfo(
                "No Updates",
                f"You're running the latest version (v{APP_VERSION})!",
                icon='info'
            )

    def _open_github(self):
        """Open GitHub repository in browser."""
        import webbrowser
        from constants import GITHUB_REPO
        webbrowser.open(f"https://github.com/{GITHUB_REPO}")

    # ------------------------------------------------------------------ #
    #  Status refresh                                                      #
    # ------------------------------------------------------------------ #

    def _update_status(self):
        status = self.serial_manager.get_connection_status()
        if self.serial_manager.is_connected and status.get('connected'):
            self.conn_status_label.configure(text="✅ Connected", text_color="#2e7d32")
        elif status.get('reconnect_active'):
            port = self.config_manager.get_preferred_port()
            self.conn_status_label.configure(
                text=f"🔄 Searching for {port}...", text_color="#e67e00"
            )
        else:
            self.conn_status_label.configure(text="❌ Not connected", text_color="#c0392b")

    def _start_status_refresh(self):
        self._update_status()
        self._refresh_timer = self.after(1000, self._start_status_refresh)

    def destroy(self):
        if hasattr(self, '_refresh_timer'):
            self.after_cancel(self._refresh_timer)
        super().destroy()

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _make_section(self, parent, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color=self.C_CARD, corner_radius=12)
        card.pack(fill="x", pady=(0, 2))

        ctk.CTkLabel(
            card, text=title,
            font=("Roboto", 14, "bold"), anchor="w"
        ).pack(padx=15, pady=(12, 4), anchor="w")

        ctk.CTkFrame(
            card, height=1, fg_color=self.C_CARD_SEP
        ).pack(fill="x", padx=15, pady=(0, 4))

        return card

    def _spacer(self, parent, h: int = 6):
        ctk.CTkFrame(parent, height=h, fg_color="transparent").pack()
