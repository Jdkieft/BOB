"""
Main Window - Stream Deck Manager GUI (FINAL VERSION)

Dit hoofdvenster bevat:
- Header met connectie status
- Button grid (3x3) met mode selector
- Audio sliders panel
- Quick actions en info panel
"""

import sys
from pathlib import Path
# Fix import paths
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

import customtkinter as ctk
import tkinter.filedialog as fd
from typing import List
import pyautogui  # Voor hotkey simulatie

# Import managers
from config_manager import ConfigManager
from serial_manager import SerialManager
from audio_manager import AudioManager

# Import GUI components
from button_widget import ButtonWidget
from slider_widget import SliderWidget
from dialogs import ButtonConfigDialog, SerialPortDialog

# Import constants
from constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, HEADER_HEIGHT,
    DEFAULT_MODES, MAX_MODES_LIMIT, MIN_MODES, BUTTONS_PER_MODE, NUM_SLIDERS,
    FONT_TITLE, FONT_HEADER, QUICK_ACTIONS,
    MSG_NO_DEVICES, MSG_CONNECTED, MSG_DISCONNECTED,
    MSG_INFO_DEFAULT, MSG_INFO_QUICK_ACTION,
    COLOR_BACKGROUND_LIGHT, COLOR_BACKGROUND_DARK,
    COLOR_SUCCESS, COLOR_ERROR
)


class StreamDeckManager(ctk.CTk):
    """
    Hoofdvenster van de Stream Deck Manager applicatie.
    
    Deze class beheert:
    - UI layout en componenten
    - Interactie tussen managers
    - Event handling
    - State synchronisatie
    
    Attributes:
        config_manager (ConfigManager): Beheert configuratie opslag
        serial_manager (SerialManager): Beheert device communicatie
        audio_manager (AudioManager): Beheert audio detectie
        current_mode (int): Huidige actieve mode (0-3)
        slider_apps (List[str]): App assignments voor sliders
        button_widgets (List[ButtonWidget]): Alle button widgets
        slider_widgets (List[SliderWidget]): Alle slider widgets
    """
    
    def __init__(self):
        """Initialiseer het hoofdvenster en alle componenten."""
        super().__init__()
        
        # Window setup
        self.title("Stream Deck Manager")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        # Appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Managers
        self.config_manager = ConfigManager()
        self.serial_manager = SerialManager()
        self.audio_manager = AudioManager()
        
        # Register callbacks voor berichten van Pico
        self.serial_manager.set_callback('BTN_PRESS', self._handle_pico_button_press)
        self.serial_manager.set_callback('SLIDER_CHANGE', self._handle_pico_slider_change)
        self.serial_manager.set_callback('MODE_CHANGE', self._handle_pico_mode_change)
        
        # State
        self.current_mode = 0
        self.num_modes = self.config_manager.get_num_modes()
        self.slider_apps = [[], [], [], []]  # 3 voor apps + 1 voor master volume
        
        # UI Components (worden later gevuld)
        self.button_widgets: List[ButtonWidget] = []
        self.slider_widgets: List[SliderWidget] = []
        self.mode_buttons: List[ctk.CTkButton] = []
        
        # Maak UI
        self._create_layout()
        
        # Laad opgeslagen state
        self._load_initial_state()
    
    # ========================================================================
    # UI CREATION
    # ========================================================================
    
    def _create_layout(self):
        """Maak de volledige UI layout."""
        self._create_header()
        self._create_main_container()
    
    def _create_header(self):
        """Maak header met titel en connectie status."""
        header = ctk.CTkFrame(
            self,
            height=HEADER_HEIGHT,
            fg_color=(COLOR_BACKGROUND_LIGHT, COLOR_BACKGROUND_DARK)
        )
        header.pack(fill="x", padx=10, pady=10)
        
        # Titel
        ctk.CTkLabel(
            header,
            text="Stream Deck + Audio Sliders",
            font=FONT_TITLE
        ).pack(side="left", padx=20)
        
        # Serial status indicator
        self.serial_status = ctk.CTkLabel(
            header,
            text=MSG_DISCONNECTED,
            font=("Roboto", 12),
            fg_color=("gray80", "gray25"),
            corner_radius=5,
            width=120,
            height=30
        )
        self.serial_status.pack(side="right", padx=5)
        
        # Connect button
        self.serial_button = ctk.CTkButton(
            header,
            text="🔌 Connect",
            command=self._handle_connect_click,
            width=120,
            height=40
        )
        self.serial_button.pack(side="right", padx=10)
    
    def _create_main_container(self):
        """Maak main container met alle panels."""
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Drie kolommen: buttons, sliders, quick actions
        self._create_button_panel(main_container)
        self._create_slider_panel(main_container)
        self._create_right_panel(main_container)
    
    def _create_button_panel(self, parent):
        """Maak linker panel met button grid."""
        left_panel = ctk.CTkFrame(parent, width=650)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Mode selector
        self._create_mode_selector(left_panel)
        
        # Button grid
        self._create_button_grid(left_panel)
    
    def _create_mode_selector(self, parent):
        """Maak mode selector buttons."""
        mode_frame = ctk.CTkFrame(parent, height=100)
        mode_frame.pack(fill="x", padx=10, pady=10)
        
        # Header met title en add/remove buttons
        header_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        header_frame.pack(pady=(10, 5), fill="x", padx=10)
        
        ctk.CTkLabel(
            header_frame,
            text="Mode Selector",
            font=("Roboto", 18, "bold")
        ).pack(side="left")
        
        # Mode counter
        self.mode_counter_label = ctk.CTkLabel(
            header_frame,
            text=f"({self.num_modes}/{MAX_MODES_LIMIT})",
            font=("Roboto", 12),
            text_color="gray"
        )
        self.mode_counter_label.pack(side="left", padx=10)
        
        # Add mode button
        self.add_mode_btn = ctk.CTkButton(
            header_frame,
            text="➕ Add Mode",
            command=self._add_mode,
            width=100,
            height=30,
            font=("Roboto", 11, "bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.add_mode_btn.pack(side="right", padx=5)
        
        # Remove mode button
        self.remove_mode_btn = ctk.CTkButton(
            header_frame,
            text="➖ Remove Current",
            command=self._remove_mode,
            width=120,
            height=30,
            font=("Roboto", 11, "bold"),
            fg_color="red",
            hover_color="darkred"
        )
        self.remove_mode_btn.pack(side="right", padx=5)
        
        # Scrollable frame voor mode buttons
        self.mode_buttons_container = ctk.CTkScrollableFrame(
            mode_frame,
            height=60,
            orientation="horizontal",
            fg_color="transparent"
        )
        self.mode_buttons_container.pack(pady=10, fill="x", padx=10)
        
        # Maak initial mode buttons
        self._rebuild_mode_buttons()
    
    def _create_button_grid(self, parent):
        """Maak 3x3 button grid."""
        grid_frame = ctk.CTkFrame(parent)
        grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Grid title
        self.grid_title = ctk.CTkLabel(
            grid_frame,
            text=f"Button Grid - Mode {self.current_mode + 1}",
            font=FONT_HEADER
        )
        self.grid_title.pack(pady=15)
        
        # Button container
        self.button_grid_frame = ctk.CTkFrame(grid_frame)
        self.button_grid_frame.pack(pady=10, padx=20)
        
        # Maak 9 buttons (3x3)
        for row in range(3):
            for col in range(3):
                btn_index = row * 3 + col
                button = ButtonWidget(
                    self.button_grid_frame,
                    btn_index,
                    row,
                    col,
                    on_click=self._handle_button_click
                )
                self.button_widgets.append(button)
    
    def _create_slider_panel(self, parent):
        """Maak middle panel met audio sliders."""
        middle_panel = ctk.CTkFrame(parent, width=350)
        middle_panel.pack(side="left", fill="both", padx=(0, 10))
        
        ctk.CTkLabel(
            middle_panel,
            text="Audio Sliders",
            font=FONT_HEADER
        ).pack(pady=15)
        
        ctk.CTkLabel(
            middle_panel,
            text="Koppel apps aan fysieke sliders\nvoor volume control",
            font=("Roboto", 11),
            text_color="gray"
        ).pack(pady=(0, 10))
        
        # Haal beschikbare apps op
        available_apps = self.audio_manager.get_audio_applications()
        
        # Maak sliders (0-2 voor apps, 3 voor master volume)
        for i in range(NUM_SLIDERS):
            # Slider 3 is master volume (geen apps)
            if i == 3:
                slider = SliderWidget(
                    middle_panel,
                    i,
                    [],  # Geen apps voor master volume
                    on_app_change=self._handle_slider_change,
                    is_master_volume=True  # Special flag
                )
            else:
                slider = SliderWidget(
                    middle_panel,
                    i,
                    available_apps,
                    on_app_change=self._handle_slider_change
                )
            self.slider_widgets.append(slider)
    
    def _create_right_panel(self, parent):
        """Maak rechter panel met quick actions en info."""
        right_panel = ctk.CTkFrame(parent, width=350)
        right_panel.pack(side="right", fill="both")
        
        # Quick actions
        self._create_quick_actions(right_panel)
        
        # Info panel
        self._create_info_panel(right_panel)
        
        # Export/Import buttons
        self._create_export_import_buttons(right_panel)
    
    def _create_quick_actions(self, parent):
        """Maak quick actions lijst."""
        ctk.CTkLabel(
            parent,
            text="⚡ Quick Actions",
            font=("Roboto", 18, "bold")
        ).pack(pady=15)
        
        quick_frame = ctk.CTkScrollableFrame(parent, height=300)
        quick_frame.pack(fill="x", padx=10, pady=10)
        
        # Maak button voor elke quick action
        for action in QUICK_ACTIONS:
            btn = ctk.CTkButton(
                quick_frame,
                text=f"{action['icon']} {action['name']}",
                command=lambda a=action: self._show_quick_action_info(a),
                height=45,
                font=("Roboto", 13),
                anchor="w",
                fg_color=("gray70", "gray30"),
                hover_color=("gray60", "gray40")
            )
            btn.pack(fill="x", pady=3, padx=5)
    
    def _create_info_panel(self, parent):
        """Maak info panel."""
        info_frame = ctk.CTkFrame(parent)
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text="ℹ️ Info",
            font=("Roboto", 14, "bold")
        ).pack(pady=10)
        
        self.info_label = ctk.CTkLabel(
            info_frame,
            text=MSG_INFO_DEFAULT,
            font=("Roboto", 11),
            wraplength=300,
            justify="left"
        )
        self.info_label.pack(pady=10, padx=10)
    
    def _create_export_import_buttons(self, parent):
        """Maak export/import buttons."""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame,
            text="📤 Export",
            command=self._handle_export,
            height=35
        ).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(
            button_frame,
            text="📥 Import",
            command=self._handle_import,
            height=35
        ).pack(side="right", padx=5, expand=True, fill="x")
    
    # ========================================================================
    # MODE MANAGEMENT
    # ========================================================================
    
    def _rebuild_mode_buttons(self):
        """Herbouw alle mode buttons op basis van num_modes."""
        # Verwijder oude buttons
        for btn in self.mode_buttons:
            btn.destroy()
        self.mode_buttons.clear()
        
        # Maak nieuwe buttons
        for i in range(self.num_modes):
            mode_name = self.config_manager.get_mode_name(i)
            
            btn = ctk.CTkButton(
                self.mode_buttons_container,
                text=mode_name,
                command=lambda m=i: self.switch_mode(m),
                width=120,
                height=45,
                font=("Roboto", 14, "bold")
            )
            btn.pack(side="left", padx=5)
            
            # Right-click to rename
            btn.bind("<Button-3>", lambda e, m=i: self._rename_mode_dialog(m))
            
            self.mode_buttons.append(btn)
        
        # Update active button
        self._update_mode_button_colors()
        
        # Update add/remove button states
        self._update_mode_button_states()
    
    def _update_mode_button_states(self):
        """Update de enabled/disabled state van add/remove buttons."""
        # Disable remove als we op minimum zitten
        if self.num_modes <= MIN_MODES:
            self.remove_mode_btn.configure(state="disabled")
        else:
            self.remove_mode_btn.configure(state="normal")
        
        # Disable add als we op maximum zitten
        if self.num_modes >= MAX_MODES_LIMIT:
            self.add_mode_btn.configure(state="disabled")
        else:
            self.add_mode_btn.configure(state="normal")
        
        # Update counter
        self.mode_counter_label.configure(text=f"({self.num_modes}/{MAX_MODES_LIMIT})")
    
    def _add_mode(self):
        """Voeg een nieuwe mode toe."""
        if self.num_modes >= MAX_MODES_LIMIT:
            self.info_label.configure(
                text=f"❌ Maximum aantal modes bereikt!\n\nJe kunt maximaal {MAX_MODES_LIMIT} modes hebben."
            )
            return
        
        self.num_modes += 1
        self.config_manager.set_num_modes(self.num_modes)
        
        # Send to Pico
        if self.serial_manager.is_connected:
            self.serial_manager.send_mode_count(self.num_modes)
            # Send default name for new mode
            default_name = f"Mode {self.num_modes}"
            self.serial_manager.send_mode_name(self.num_modes - 1, default_name)
        
        # Rebuild buttons
        self._rebuild_mode_buttons()
        
        # Update info
        self.info_label.configure(
            text=f"✅ Mode {self.num_modes} toegevoegd!\n\nJe hebt nu {self.num_modes} modes."
        )
        
        print(f"✅ Added mode {self.num_modes}")
    
    def _remove_mode(self):
        """Verwijder de huidige geselecteerde mode."""
        if self.num_modes <= MIN_MODES:
            self.info_label.configure(
                text=f"❌ Minimum aantal modes!\n\nJe moet minimaal {MIN_MODES} mode hebben."
            )
            return
        
        mode_to_remove = self.current_mode
        mode_name = self.config_manager.get_mode_name(mode_to_remove)
        
        # Check of deze mode configuraties heeft
        has_configs = False
        for btn in range(BUTTONS_PER_MODE):
            if self.config_manager.get_button_config(mode_to_remove, btn):
                has_configs = True
                break
        
        # Vraag bevestiging
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Delete")
        dialog.geometry("450x250")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(
            dialog,
            text=f"⚠️ {mode_name} verwijderen?",
            font=("Roboto", 20, "bold")
        ).pack(pady=20)
        
        if has_configs:
            warning_text = "Deze mode heeft geconfigureerde buttons.\nAlle configuraties worden permanent verwijderd!"
            text_color = "red"
        else:
            warning_text = "Deze mode is leeg en kan veilig\nverwijderd worden."
            text_color = "gray"
        
        ctk.CTkLabel(
            dialog,
            text=warning_text,
            font=("Roboto", 13),
            text_color=text_color
        ).pack(pady=10)
        
        ctk.CTkLabel(
            dialog,
            text=f"Modes na deze worden hernummerd.\n(Mode {mode_to_remove + 2} → Mode {mode_to_remove + 1}, etc.)",
            font=("Roboto", 11),
            text_color="gray"
        ).pack(pady=5)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Cancel",
            command=dialog.destroy,
            width=180,
            height=45,
            font=("Roboto", 14, "bold")
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="🗑️ Delete Mode",
            command=lambda: [self._confirm_remove_current_mode(mode_to_remove), dialog.destroy()],
            width=180,
            height=45,
            font=("Roboto", 14, "bold"),
            fg_color="red",
            hover_color="darkred"
        ).pack(side="right", padx=10)
    
    def _confirm_remove_current_mode(self, mode_to_remove: int):
        """Bevestig en voer mode removal uit voor huidige geselecteerde mode."""
        
        # Verwijder alle button configs voor deze mode
        for btn in range(BUTTONS_PER_MODE):
            self.config_manager.clear_button_config(mode_to_remove, btn)
            # Send clear to Pico
            if self.serial_manager.is_connected:
                self.serial_manager.send_clear_button(mode_to_remove, btn)
        
        # Verwijder mode naam
        mode_name_key = f"mode_{mode_to_remove}_name"
        if mode_name_key in self.config_manager.config:
            del self.config_manager.config[mode_name_key]
        
        # Shift alle modes na deze mode omlaag
        for mode in range(mode_to_remove + 1, self.num_modes):
            # Shift button configs
            for btn in range(BUTTONS_PER_MODE):
                config = self.config_manager.get_button_config(mode, btn)
                if config:
                    # Verplaats naar mode - 1
                    self.config_manager.set_button_config(mode - 1, btn, config)
                    # Verwijder oude
                    self.config_manager.clear_button_config(mode, btn)
                    
                    # Send to Pico
                    if self.serial_manager.is_connected:
                        self.serial_manager.send_button_config(mode - 1, btn, config)
                        self.serial_manager.send_clear_button(mode, btn)
            
            # Shift mode namen
            old_name_key = f"mode_{mode}_name"
            new_name_key = f"mode_{mode - 1}_name"
            if old_name_key in self.config_manager.config:
                mode_name = self.config_manager.config[old_name_key]
                self.config_manager.config[new_name_key] = mode_name
                del self.config_manager.config[old_name_key]
                
                # Send to Pico
                if self.serial_manager.is_connected:
                    self.serial_manager.send_mode_name(mode - 1, mode_name)
        
        # Verlaag aantal modes
        self.num_modes -= 1
        self.config_manager.set_num_modes(self.num_modes)
        
        # Send to Pico
        if self.serial_manager.is_connected:
            self.serial_manager.send_mode_count(self.num_modes)
        
        # Switch naar veilige mode
        if self.current_mode >= self.num_modes:
            self.current_mode = self.num_modes - 1
        
        # Rebuild buttons
        self._rebuild_mode_buttons()
        
        # Reload current mode
        self._load_button_states()
        
        # Update info
        self.info_label.configure(
            text=f"✅ Mode verwijderd!\n\nJe hebt nu {self.num_modes} modes.\nModes zijn hernummerd."
        )
        
        print(f"✅ Removed mode {mode_to_remove + 1} and shifted remaining modes")
    
    def _rename_mode_dialog(self, mode: int):
        """Open dialog om mode naam te wijzigen."""
        current_name = self.config_manager.get_mode_name(mode)
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Rename {current_name}")
        dialog.geometry("450x220")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(
            dialog,
            text=f"✏️ Rename {current_name}",
            font=("Roboto", 20, "bold")
        ).pack(pady=20)
        
        ctk.CTkLabel(
            dialog,
            text="Enter new name:",
            font=("Roboto", 12),
            text_color="gray"
        ).pack(pady=(0, 5))
        
        # Name entry
        name_entry = ctk.CTkEntry(
            dialog,
            width=350,
            height=45,
            placeholder_text="e.g. Gaming, Streaming, Work...",
            font=("Roboto", 14)
        )
        name_entry.insert(0, current_name)
        name_entry.pack(pady=10)
        name_entry.focus()
        
        # Select all text
        name_entry.select_range(0, 'end')
        
        def save_name():
            new_name = name_entry.get().strip()
            if new_name and len(new_name) <= 20:
                self.config_manager.set_mode_name(mode, new_name)
                self._rebuild_mode_buttons()
                
                # Send to Pico
                if self.serial_manager.is_connected:
                    self.serial_manager.send_mode_name(mode, new_name)
                
                # Update grid title if this is current mode
                if mode == self.current_mode:
                    self.grid_title.configure(text=f"📱 Button Grid - {new_name}")
                
                self.info_label.configure(
                    text=f"✅ Mode hernoemd!\n\n'{current_name}' → '{new_name}'"
                )
                dialog.destroy()
            elif len(new_name) > 20:
                error_label = ctk.CTkLabel(
                    dialog,
                    text="❌ Naam te lang! (max 20 karakters)",
                    font=("Roboto", 11, "bold"),
                    text_color="red"
                )
                error_label.pack(pady=5)
                dialog.after(2000, error_label.destroy)
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            width=150,
            height=40,
            font=("Roboto", 13)
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Save Name",
            command=save_name,
            width=150,
            height=40,
            font=("Roboto", 13, "bold"),
            fg_color="green",
            hover_color="darkgreen"
        ).pack(side="right", padx=10)
        
        # Enter key to save
        name_entry.bind("<Return>", lambda e: save_name())
    
    def _update_mode_button_colors(self):
        """Update de kleuren van mode buttons."""
        for i, btn in enumerate(self.mode_buttons):
            if i == self.current_mode:
                btn.configure(fg_color=("#3B82F6", "#1E40AF"))
            else:
                btn.configure(fg_color=("gray60", "gray40"))
    
    # ========================================================================
    # STATE MANAGEMENT
    # ========================================================================
    
    def _load_initial_state(self):
        """Laad opgeslagen configuratie bij start."""
        # Laad button states
        self._load_button_states()
        
        # Laad slider states (now list of apps per slider)
        for i in range(NUM_SLIDERS):
            apps = self.config_manager.get_slider_config(i)
            # Config returns string, but we need list
            if isinstance(apps, str):
                # Old config format - convert
                self.slider_apps[i] = [apps] if apps and apps != "Master Volume" else []
            elif isinstance(apps, list):
                self.slider_apps[i] = apps
            else:
                self.slider_apps[i] = []
            
            self.slider_widgets[i].set_assigned_apps(self.slider_apps[i])
    
    def _load_button_states(self):
        """Laad button states voor huidige mode."""
        for i in range(BUTTONS_PER_MODE):
            config = self.config_manager.get_button_config(self.current_mode, i)
            self.button_widgets[i].update_display(config)
    
    # ========================================================================
    # EVENT HANDLERS
    # ========================================================================
    
    def _handle_button_click(self, button_index: int):
        """Handle click op een button in de grid."""
        current_config = self.config_manager.get_button_config(
            self.current_mode,
            button_index
        )
        
        # Open configuratie dialog
        ButtonConfigDialog(
            self,
            button_index,
            self.current_mode,
            current_config,
            on_save=lambda config: self._save_button_config(button_index, config),
            on_clear=lambda: self._clear_button_config(button_index)
        )
    
    def _save_button_config(self, button_index: int, config: dict):
        """Sla button configuratie op."""
        # Save to config manager
        self.config_manager.set_button_config(
            self.current_mode,
            button_index,
            config
        )
        
        # Update display
        self.button_widgets[button_index].update_display(config)
        
        # Send to device
        self.serial_manager.send_button_config(
            self.current_mode,
            button_index,
            config
        )
    
    def _clear_button_config(self, button_index: int):
        """Clear button configuratie."""
        # Clear from config
        self.config_manager.clear_button_config(self.current_mode, button_index)
        
        # Update display
        self.button_widgets[button_index].update_display(None)
        
        # Send clear to device
        self.serial_manager.send_clear_button(self.current_mode, button_index)
    
    def _handle_slider_change(self, slider_index: int, app_names: List[str]):
        """Handle slider app lijst wijziging."""
        # Slider 3 (master volume) slaat geen apps op
        if slider_index == 3:
            return
        
        # Update state
        self.slider_apps[slider_index] = app_names
        
        # Save to config (as list now!)
        self.config_manager.set_slider_config(slider_index, app_names)
        
        # Send to device (send each app separately or as JSON)
        if self.serial_manager.is_connected:
            # Send as comma-separated list
            apps_str = ",".join(app_names) if app_names else "NONE"
            self.serial_manager.send_slider_config(slider_index, apps_str)
        
        print(f"Slider {slider_index + 1} → {len(app_names)} apps: {app_names}")
    
    def _handle_connect_click(self):
        """Handle connect button click."""
        # Haal beschikbare poorten op
        ports = self.serial_manager.get_available_ports()
        
        if not ports:
            self.info_label.configure(text=MSG_NO_DEVICES)
            return
        
        # Open port selector dialog
        SerialPortDialog(
            self,
            ports,
            on_connect=self._connect_to_port
        )
    
    def _connect_to_port(self, port_name: str):
        """Maak verbinding met geselecteerde poort."""
        self.info_label.configure(text="🔌 Connecting...")
        
        success = self.serial_manager.connect(port_name)
        
        if success:
            # Update UI
            self.serial_button.configure(
                text="⏳ Waiting...",
                fg_color="orange"
            )
            self.serial_status.configure(
                text="⏳ Waiting for device",
                fg_color="orange"
            )
            self.info_label.configure(
                text=f"⏳ Connected to:\n{port_name}\n\nWaiting for Pico READY..."
            )
            
            # Wait for READY signal in background
            self.after(100, lambda: self._wait_for_ready_and_sync(port_name))
        else:
            self.serial_button.configure(
                text="🔌 Connect",
                fg_color=("gray60", "gray40")
            )
            self.serial_status.configure(
                text=MSG_DISCONNECTED,
                fg_color=("gray80", "gray25")
            )
            self.info_label.configure(text="❌ Connection failed")
    
    def _wait_for_ready_and_sync(self, port_name: str):
        """Wacht op READY en start synchronisatie."""
        # Wait for READY (timeout: 5 seconds)
        if self.serial_manager.wait_for_ready(timeout=5.0):
            # READY received!
            self.serial_button.configure(
                text="✅ Connected",
                fg_color=COLOR_SUCCESS
            )
            self.serial_status.configure(
                text=MSG_CONNECTED,
                fg_color=COLOR_SUCCESS
            )
            self.info_label.configure(
                text=f"✅ Device ready!\n\nStarting sync..."
            )
            
            # Start sync after short delay
            self.after(200, self._sync_all_configs)
        else:
            # Timeout - no READY received
            self.serial_button.configure(
                text="⚠️ No Response",
                fg_color="orange"
            )
            self.serial_status.configure(
                text="⚠️ No Response",
                fg_color="orange"
            )
            self.info_label.configure(
                text=f"⚠️ Connected but no response\n\nDevice might not be ready.\nCheck Pico firmware.\n\nRetry sync manually?"
            )
    
    def _sync_all_configs(self):
        """Synchroniseer alle configuraties naar device."""
        count = self.serial_manager.sync_all_configs(
            self.config_manager,
            self.slider_apps
        )
        
        self.info_label.configure(
            text=f"✅ Sync complete!\n\n{count} buttons configured\n{NUM_SLIDERS} sliders configured"
        )
    
    def _show_quick_action_info(self, action: dict):
        """Toon info over quick action."""
        self.info_label.configure(
            text=MSG_INFO_QUICK_ACTION.format(**action)
        )
    
    def _handle_export(self):
        """Export configuratie naar bestand."""
        filename = fd.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if filename:
            self.config_manager.export_to_file(filename)
            self.info_label.configure(
                text=f"✅ Exported to:\n{Path(filename).name}"
            )
    
    def _handle_import(self):
        """Import configuratie van bestand."""
        filename = fd.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        
        if filename:
            success = self.config_manager.import_from_file(filename)
            
            if success:
                # Reload UI
                self._load_button_states()
                
                for i in range(NUM_SLIDERS):
                    apps = self.config_manager.get_slider_config(i)
                    if isinstance(apps, str):
                        apps = [apps] if apps else []
                    self.slider_apps[i] = apps
                    self.slider_widgets[i].set_assigned_apps(apps)
                
                # Sync to device
                if self.serial_manager.is_connected:
                    self._sync_all_configs()
                
                self.info_label.configure(
                    text=f"✅ Imported from:\n{Path(filename).name}"
                )
    
    # ========================================================================
    # PUBLIC METHODS
    # ========================================================================
    
    def switch_mode(self, mode: int):
        """
        Wissel naar andere mode.
        
        Args:
            mode: Mode nummer (0 tot num_modes-1)
        """
        # Valideer mode nummer
        if mode < 0 or mode >= self.num_modes:
            print(f"❌ Invalid mode: {mode}")
            return
        
        self.current_mode = mode
        
        # Update mode buttons
        self._update_mode_button_colors()
        
        # Update grid title
        mode_name = self.config_manager.get_mode_name(mode)
        self.grid_title.configure(text=f"📱 Button Grid - {mode_name}")
        
        # Reload button states
        self._load_button_states()
        
        # Send to device (with mode name!)
        if self.serial_manager.is_connected:
            mode_name = self.config_manager.get_mode_name(mode)
            self.serial_manager.send_mode_switch(mode)
        
        print(f"🔄 Switched to Mode {mode + 1}")
    # ========================================================================
    # PICO MESSAGE HANDLERS (NIEUWE CODE!)
    # ========================================================================
    
    def _handle_pico_button_press(self, mode: int, button: int):
        """
        Handle button press bericht van Pico.
        
        Deze functie wordt aangeroepen door de serial manager wanneer
        de Pico een BTN_PRESS bericht stuurt.
        
        Args:
            mode: Mode nummer van de button
            button: Button nummer (0-8)
        """
        print(f"🔘 Pico button press: Mode {mode}, Button {button}")
        
        # Haal de configuratie op voor deze button
        config = self.config_manager.get_button_config(mode, button)
        
        if not config:
            print(f"⚠️  Button {button} in mode {mode} not configured")
            return
        
        # Haal hotkey op
        hotkey = config.get('hotkey', '')
        label = config.get('label', 'Unknown')
        
        if not hotkey:
            print(f"⚠️  No hotkey configured for button {button}")
            return
        
        # Simuleer de hotkey!
        try:
            print(f"⌨️  Simulating hotkey: {hotkey} for '{label}'")
            
            # Parse hotkey string (bijv. "ctrl+shift+m")
            keys = hotkey.lower().split('+')
            
            # Gebruik pyautogui om hotkey te simuleren
            pyautogui.hotkey(*keys)
            
            print(f"✅ Hotkey '{hotkey}' executed successfully")
            
            # Update UI om te laten zien dat knop werkt
            self.after(0, lambda: self.info_label.configure(
                text=f"🎯 Button Pressed!\n\n{label}\n\nHotkey: {hotkey}"
            ))
            
        except Exception as e:
            print(f"❌ Error executing hotkey '{hotkey}': {e}")
            self.after(0, lambda: self.info_label.configure(
                text=f"❌ Hotkey Error!\n\n{label}\n\n{str(e)}"
            ))
    
    def _handle_pico_slider_change(self, slider: int, value: int):
        """
        Handle slider change bericht van Pico.
        
        Args:
            slider: Slider nummer (0-3: 0-2 voor apps, 3 voor master volume)
            value: Nieuwe waarde (0-100)
        """
        if slider >= NUM_SLIDERS:
            print(f"⚠️  Slider {slider} out of range (max {NUM_SLIDERS-1})")
            return
        
        print(f"🎚️ Pico slider {slider} changed to {value}%")
        
        # Update visuele weergave (moet op main thread)
        self.after(0, lambda: self.slider_widgets[slider].update_volume_display(value / 100.0))
        
        # Converteer 0-100 naar 0.0-1.0
        volume_float = value / 100.0
        
        # Check of dit slider 3 is (master volume)
        if slider == 3:
            # Stel master volume in
            try:
                success = self.audio_manager.set_master_volume(volume_float)
                
                if success:
                    print(f"🔊 Set master volume to {value}%")
                else:
                    print(f"⚠️  Could not set master volume")
                    
            except Exception as e:
                print(f"❌ Error setting master volume: {e}")
            return
        
        # Voor sliders 0-2: app volume control
        # Haal apps op die aan deze slider zijn gekoppeld
        apps = self.slider_apps[slider]
        
        if not apps:
            print(f"ℹ️  Slider {slider} has no apps assigned")
            return
        
        # Stel volume in voor elke app
        for app in apps:
            try:
                # Probeer volume te zetten
                success = self.audio_manager.set_volume_for_app(app, volume_float)
                
                if success:
                    print(f"🔊 Set volume for {app} to {value}%")
                else:
                    print(f"⚠️  Could not set volume for {app}")
                    
            except Exception as e:
                print(f"❌ Error setting volume for {app}: {e}")
    
    def _handle_pico_mode_change(self, mode: int):
        """
        Handle mode change bericht van Pico.
        
        Deze functie wordt aangeroepen wanneer de gebruiker op de Pico
        zelf de mode verandert (bijv. met encoder of mode buttons).
        
        Args:
            mode: Nieuwe mode nummer
        """
        print(f"🔄 Pico changed mode to {mode}")
        
        # Update de GUI om te synchroniseren met Pico
        # Gebruik after() om thread-safe te zijn
        self.after(0, lambda: self.switch_mode(mode))
