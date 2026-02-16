"""
Main Window - Stream Deck Manager GUI (IMPROVED LAYOUT VERSION)

Dit hoofdvenster bevat:
- Header met connectie status
- Button grid (3x3) met mode selector
- Audio sliders panel (breder en beter schalend)
- Info panel en export/import functionaliteit
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
from spotify_manager import SpotifyManager

# Import GUI components
from button_widget import ButtonWidget
from slider_widget import SliderWidget
from dialogs import ButtonConfigDialog
from dialogs_connection import ConnectionDialog

# Import constants
from constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, HEADER_HEIGHT,
    DEFAULT_MODES, MAX_MODES_LIMIT, MIN_MODES, BUTTONS_PER_MODE, NUM_SLIDERS,
    FONT_TITLE, FONT_HEADER,
    MSG_NO_DEVICES, MSG_INFO_DEFAULT,
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
        
        # Bind window close event voor cleanup
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Managers
        self.config_manager = ConfigManager()
        self.serial_manager = SerialManager()
        self.audio_manager = AudioManager()
        self.spotify_manager = SpotifyManager()
        
        # Register callbacks voor berichten van Pico
        self.serial_manager.set_callback('BTN_PRESS', self._handle_pico_button_press)
        self.serial_manager.set_callback('SLIDER_CHANGE', self._handle_pico_slider_change)
        self.serial_manager.set_callback('MODE_CHANGE', self._handle_pico_mode_change)
        self.serial_manager.set_callback('CONNECTION_CHANGED', self._handle_connection_changed)
        
        # Register Spotify callback
        self.spotify_manager.set_callback(self._handle_spotify_track_change)
        
        # State
        self.current_mode = 0
        self.num_modes = self.config_manager.get_num_modes()
        self.slider_apps = [[], [], [], []]  # 3 voor apps + 1 voor master volume
        
        # UI Components (worden later gevuld)
        self.button_widgets: List[ButtonWidget] = []
        self.slider_widgets: List[SliderWidget] = []
        self.mode_buttons: List[ctk.CTkButton] = []
        
        # System tray
        self.system_tray_available = False
        self.system_tray_active = False
        self.tray_icon = None
        
        # Maak UI
        self._create_layout()
        
        # Maak system tray icon
        self._create_system_tray()
        
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
            fg_color=("gray92", "gray17")  # Subtiele gradient-achtige kleur
        )
        header.pack(fill="x", padx=10, pady=10)
        
        # Titel met subtiel gradient effect
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(
            title_frame,
            text="Stream Deck + Audio Sliders",
            font=FONT_TITLE,
            text_color=("#2563EB", "#60A5FA")  # Gradient-achtig blauw
        ).pack()
        
        # Connection status container
        status_container = ctk.CTkFrame(header, fg_color="transparent")
        status_container.pack(side="right", padx=20)
        
        # Status indicator (animated dot)
        self.status_indicator = ctk.CTkLabel(
            status_container,
            text="⚫",
            font=("Roboto", 20),
            text_color="gray"
        )
        self.status_indicator.pack(side="left", padx=(0, 10))
        
        # Status text
        self.status_text = ctk.CTkLabel(
            status_container,
            text="Niet verbonden",
            font=("Roboto", 13),
            text_color="gray"
        )
        self.status_text.pack(side="left", padx=(0, 15))
        
        # Connect button
        self.serial_button = ctk.CTkButton(
            status_container,
            text="⚙️ Configureer",
            command=self._handle_connect_click,
            width=140,
            height=40,
            font=("Roboto", 12, "bold")
        )
        self.serial_button.pack(side="left")
        
        # Start status update loop
        self._update_connection_status()
    
    def _create_main_container(self):
        """Maak main container met alle panels."""
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Twee kolommen: buttons (links) en sliders (rechts, breder)
        self._create_button_panel(main_container)
        self._create_slider_panel(main_container)
    
    def _create_button_panel(self, parent):
        """Maak linker panel met button grid, info en export/import."""
        left_panel = ctk.CTkFrame(parent)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Mode selector
        self._create_mode_selector(left_panel)
        
        # Button grid (met expand voor betere scaling)
        self._create_button_grid(left_panel)
        
        # Info panel onderaan
        self._create_info_panel(left_panel)
        
        # Export/Import buttons onderaan
        self._create_export_import_buttons(left_panel)
    
    def _create_mode_selector(self, parent):
        """Maak mode selector buttons."""
        mode_frame = ctk.CTkFrame(
            parent, 
            height=100,
            fg_color=("gray88", "gray18")  # Subtiele gradient kleur
        )
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
        """Maak 3x3 button grid met betere scaling."""
        grid_frame = ctk.CTkFrame(
            parent,
            fg_color=("gray88", "gray18")  # Subtiele gradient achtergrond
        )
        grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Grid title
        self.grid_title = ctk.CTkLabel(
            grid_frame,
            text=f"Button Grid - Mode {self.current_mode + 1}",
            font=FONT_HEADER
        )
        self.grid_title.pack(pady=15)
        
        # Button container (centraal gepositioneerd, schaalt niet extreem ver uit)
        button_container = ctk.CTkFrame(grid_frame, fg_color="transparent")
        button_container.pack(expand=True, pady=10)
        
        # Inner grid frame voor de buttons zelf
        self.button_grid_frame = ctk.CTkFrame(button_container, fg_color="transparent")
        self.button_grid_frame.pack()
        
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
        """Maak rechter panel met audio sliders - nu veel breder en beter schalend."""
        # Maak een scrollable frame zodat het altijd past, zelfs op kleine schermen
        slider_panel = ctk.CTkScrollableFrame(
            parent, 
            width=500,
            fg_color=("gray90", "gray16")  # Subtiele gradient achtergrond
        )
        slider_panel.pack(side="right", fill="both", expand=True)
        
        # Header met gradient-achtige styling
        header_frame = ctk.CTkFrame(
            slider_panel,
            fg_color="transparent"
        )
        header_frame.pack(pady=15, padx=15, fill="x")
        
        ctk.CTkLabel(
            header_frame,
            text="Audio Sliders",
            font=FONT_HEADER,
            text_color=("#2563EB", "#3B82F6")  # Gradient blauw
        ).pack()
        
        ctk.CTkLabel(
            slider_panel,
            text="Koppel apps aan fysieke sliders\nvoor volume control\n(Right-click op naam om te hernoemen)",
            font=("Roboto", 10),
            text_color="gray",
            justify="center"
        ).pack(pady=(0, 10))
        
        # Haal beschikbare apps op
        available_apps = self.audio_manager.get_audio_applications()
        
        # Maak sliders (0-2 voor apps, 3 voor master volume)
        for i in range(NUM_SLIDERS):
            # Haal opgeslagen naam op
            slider_name = self.config_manager.get_slider_name(i)
            
            # Slider 3 is master volume (geen apps)
            if i == 3:
                slider = SliderWidget(
                    slider_panel,
                    i,
                    [],  # Geen apps voor master volume
                    on_app_change=self._handle_slider_change,
                    is_master_volume=True,  # Special flag
                    slider_name=slider_name
                )
            else:
                slider = SliderWidget(
                    slider_panel,
                    i,
                    available_apps,
                    on_app_change=self._handle_slider_change,
                    slider_name=slider_name
                )
            
            # Stel rename callback in
            slider.set_rename_callback(self._handle_slider_rename)
            
            # Stel app rename callback in
            slider.set_app_rename_callback(self._handle_app_rename)
            
            # Laad app naam mappings
            app_mappings = self.config_manager.get_all_app_name_mappings()
            slider.set_app_name_mappings(app_mappings)
            
            self.slider_widgets.append(slider)
    
    # _create_right_panel REMOVED - Quick Actions feature has been removed
    # Info panel and export/import buttons are now in the left column
    
    def _create_info_panel(self, parent):
        """Maak info panel (nu in linker kolom, compacter)."""
        info_frame = ctk.CTkFrame(
            parent,
            fg_color=("gray85", "gray22"),  # Subtiele gradient kleur
            border_width=1,
            border_color=("gray70", "gray35")
        )
        info_frame.pack(fill="x", padx=10, pady=(5, 5))
        
        ctk.CTkLabel(
            info_frame,
            text="ℹ️ Info",
            font=("Roboto", 14, "bold")
        ).pack(pady=(10, 5))
        
        self.info_label = ctk.CTkLabel(
            info_frame,
            text=MSG_INFO_DEFAULT,
            font=("Roboto", 11),
            wraplength=600,
            justify="center"
        )
        self.info_label.pack(pady=(5, 10), padx=10)
    
    def _create_export_import_buttons(self, parent):
        """Maak export/import buttons (nu in linker kolom)."""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkButton(
            button_frame,
            text="📤 Export Config",
            command=self._handle_export,
            height=40,
            font=("Roboto", 12, "bold")
        ).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(
            button_frame,
            text="📥 Import Config",
            command=self._handle_import,
            height=40,
            font=("Roboto", 12, "bold")
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
                    self.grid_title.configure(text=f"Button Grid - {new_name}")
                
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
                btn.configure(
                    fg_color=("#3B82F6", "#2563EB"),  # Gradient van licht naar donker blauw
                    hover_color=("#60A5FA", "#3B82F6")  # Lichter bij hover
                )
            else:
                btn.configure(
                    fg_color=("gray60", "gray40"),
                    hover_color=("gray50", "gray50")
                )
    
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
        
        # Check voor preferred port en start auto-reconnect
        preferred_port = self.config_manager.get_preferred_port()
        if preferred_port:
            print(f"🔄 Preferred port found: {preferred_port}")
            print(f"🔄 Starting auto-reconnect...")
            self.serial_manager.start_auto_reconnect(preferred_port)
            self.info_label.configure(
                text=f"🔄 Zoeken naar {preferred_port}...\n\nAuto-reconnect actief.\nSluit je Pico aan om te verbinden."
            )
        
        # Start Spotify monitor
        print("🎵 Starting Spotify monitor...")
        self.spotify_manager.start()
    
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
    
    def _handle_slider_rename(self, slider_index: int, new_name: str):
        """
        Handle slider rename.
        
        Args:
            slider_index: Slider nummer (0-3)
            new_name: Nieuwe naam voor de slider
        """
        # Sla op in config
        self.config_manager.set_slider_name(slider_index, new_name)
        
        # Update info label
        self.info_label.configure(
            text=f"✅ Slider hernoemd!\n\nSlider {slider_index + 1} → '{new_name}'"
        )
        
        print(f"✅ Slider {slider_index} renamed to '{new_name}'")
    
    def _handle_app_rename(self, original_name: str, display_name: str):
        """
        Handle app rename.
        
        Args:
            original_name: Originele app naam (bijv. "gw2.exe")
            display_name: Nieuwe display naam (bijv. "Guild Wars 2")
        """
        # Sla op in config
        self.config_manager.set_app_display_name(original_name, display_name)
        
        # Update alle sliders met de nieuwe mapping
        app_mappings = self.config_manager.get_all_app_name_mappings()
        for slider in self.slider_widgets:
            slider.set_app_name_mappings(app_mappings)
        
        # Update info label
        self.info_label.configure(
            text=f"✅ App hernoemd!\n\n'{original_name}' → '{display_name}'"
        )
        
        print(f"✅ App '{original_name}' renamed to '{display_name}'")
    
    def _handle_connect_click(self):
        """Handle connect button click - open connection dialog."""
        # Open de nieuwe connection dialog
        ConnectionDialog(
            self,
            self.serial_manager,
            self.config_manager,
            on_port_selected=self._on_port_selected
        )
    
    def _on_port_selected(self, port_name: str):
        """
        Callback wanneer een poort geselecteerd wordt.
        
        Args:
            port_name: De geselecteerde COM poort naam
        """
        print(f"📌 Port selected: {port_name}")
        self.info_label.configure(
            text=f"🔄 Auto-reconnect actief voor:\n{port_name}\n\nZodra de Pico verbonden is,\nwordt automatisch gesynchroniseerd."
        )
    
    def _handle_connection_changed(self, is_connected: bool):
        """
        Callback wanneer connection status verandert.
        
        Args:
            is_connected: True als verbonden, False als disconnected
        """
        if is_connected:
            # We zijn verbonden!
            self.status_indicator.configure(text="🟡", text_color="orange")
            self.status_text.configure(text="Verbonden - Wachten...", text_color="orange")
            
            port_name = self.serial_manager.preferred_port or "Unknown"
            self.info_label.configure(
                text=f"⏳ Connected to:\n{port_name}\n\nWaiting for Pico READY..."
            )
            
            # Wait for READY signal in background
            self.after(100, lambda: self._wait_for_ready_and_sync(port_name))
        else:
            # Verbinding verbroken
            self.status_indicator.configure(text="🔴", text_color="red")
            
            preferred = self.config_manager.get_preferred_port()
            if preferred:
                self.status_text.configure(
                    text=f"Zoeken naar {preferred}...",
                    text_color="orange"
                )
                self.info_label.configure(
                    text=f"🔄 Verbinding verbroken!\n\nZoeken naar {preferred}...\n\nAuto-reconnect actief.\nSluit je Pico aan om te verbinden."
                )
            else:
                self.status_text.configure(text="Niet verbonden", text_color="gray")
                self.info_label.configure(text=MSG_INFO_DEFAULT)
    
    def _update_connection_status(self):
        """
        Periodieke update van connection status (elke seconde).
        
        Deze methode checkt de connection health en update de visuele indicators.
        """
        # Check connection health
        is_healthy = self.serial_manager.check_connection_health()
        
        # Update visual status
        if self.serial_manager.is_connected and is_healthy:
            # Alles goed - blauwe indicator
            self.status_indicator.configure(text="●", text_color="#3B82F6")
            port = self.serial_manager.preferred_port or "Unknown"
            self.status_text.configure(text=f"Verbonden met {port}", text_color="#3B82F6")
        elif self.serial_manager.reconnect_running and self.serial_manager.preferred_port:
            # Auto-reconnect actief - oranje indicator
            self.status_indicator.configure(text="●", text_color="orange")
            port = self.serial_manager.preferred_port
            self.status_text.configure(text=f"Zoeken naar {port}...", text_color="orange")
        else:
            # Niet verbonden - grijze indicator
            self.status_indicator.configure(text="●", text_color="gray")
            self.status_text.configure(text="Niet verbonden", text_color="gray")
        
        # Schedule volgende update
        self.after(1000, self._update_connection_status)
    
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
            self.info_label.configure(text="❌ Connection failed")
    
    def _wait_for_ready_and_sync(self, port_name: str):
        """Wacht op READY en start synchronisatie."""
        # Wait for READY (timeout: 5 seconds)
        if self.serial_manager.wait_for_ready(timeout=5.0):
            # READY received!
            self.status_indicator.configure(text="🟢", text_color="green")
            self.status_text.configure(text=f"Verbonden met {port_name}", text_color="green")
            
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
    
    # _show_quick_action_info REMOVED - Quick Actions feature has been removed
    
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
        self.grid_title.configure(text=f"Button Grid - {mode_name}")
        
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
        
        label = config.get('label', 'Unknown')
        
        # Check of dit een app launch is
        app_path = config.get('app_path', '')
        if app_path:
            # Launch application
            try:
                import subprocess
                import os
                
                print(f"🚀 Launching application: {app_path}")
                
                # Use subprocess to launch the app
                if os.path.exists(app_path):
                    subprocess.Popen([app_path], shell=True)
                    print(f"✅ Application '{label}' launched successfully")
                    
                    # Update UI
                    self.after(0, lambda: self.info_label.configure(
                        text=f"🚀 App Launched!\n\n{label}\n\n{os.path.basename(app_path)}"
                    ))
                else:
                    print(f"❌ Application not found: {app_path}")
                    self.after(0, lambda: self.info_label.configure(
                        text=f"❌ App Not Found!\n\n{label}\n\n{app_path}"
                    ))
                    
            except Exception as e:
                print(f"❌ Error launching app '{app_path}': {e}")
                self.after(0, lambda: self.info_label.configure(
                    text=f"❌ Launch Error!\n\n{label}\n\n{str(e)}"
                ))
            return
        
        # Otherwise, execute hotkey
        hotkey = config.get('hotkey', '')
        
        if not hotkey:
            print(f"⚠️  No hotkey or app configured for button {button}")
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
    
    def _handle_spotify_track_change(self, artist: str, title: str):
        """
        Callback wanneer Spotify track wijzigt.
        Stuurt track info naar Pico voor display.
        
        Args:
            artist: Artiest naam
            title: Track titel
        """
        if not self.serial_manager.is_connected:
            return
        
        # Stuur naar Pico via serial_manager
        self.serial_manager.send_spotify_track(artist, title)
        
        print(f"🎵 Spotify → Pico: {artist} - {title}")
    
    # ========================================================================
    # CLEANUP & SYSTEM TRAY
    # ========================================================================
    
    def _create_system_tray(self):
        """
        Maak system tray icon.
        
        Deze methode creëert een icon in het systeemvak zodat de app
        op de achtergrond kan draaien zonder venster.
        """
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            # Maak een simpel icon (zwarte cirkel met SD)
            def create_icon_image():
                width = 64
                height = 64
                image = Image.new('RGB', (width, height), 'black')
                draw = ImageDraw.Draw(image)
                
                # Teken cirkel
                draw.ellipse([8, 8, 56, 56], fill='#3B82F6', outline='white', width=2)
                
                # Teken tekst "SD"
                draw.text((18, 22), "SD", fill='white')
                
                return image
            
            # Maak menu items
            def on_show(icon, item):
                """Toon het venster weer."""
                # Toon window in main thread
                self.after(0, self._show_from_tray)
            
            def on_quit(icon, item):
                """Echt afsluiten."""
                icon.stop()
                self.after(0, self._real_quit)
            
            # Maak het menu
            menu = pystray.Menu(
                pystray.MenuItem("🖥️ Toon Venster", on_show, default=True),
                pystray.MenuItem("❌ Afsluiten", on_quit)
            )
            
            # Maak tray icon
            self.tray_icon = pystray.Icon(
                "stream_deck",
                create_icon_image(),
                "Stream Deck Manager",
                menu
            )
            
            self.system_tray_available = True
            print("✅ System tray icon created")
            
        except ImportError:
            print("⚠️ pystray not installed - minimize to tray disabled")
            print("   Install with: pip install pystray pillow")
            self.system_tray_available = False
            self.tray_icon = None
    
    def _minimize_to_tray(self):
        """
        Minimaliseer de app naar system tray.
        
        Het venster wordt verborgen en een icon verschijnt in het systeemvak.
        """
        if not self.system_tray_available:
            print("⚠️ System tray not available - closing app")
            self._real_quit()
            return
        
        # Check of tray al actief is
        if self.system_tray_active:
            print("📥 Already in system tray - just hiding window")
            self.withdraw()
            return
        
        print("📥 Minimizing to system tray...")
        
        # Verberg window
        self.withdraw()
        
        # Start tray icon in background thread
        self.system_tray_active = True
        
        import threading
        tray_thread = threading.Thread(target=self._run_tray_icon, daemon=True)
        tray_thread.start()
        
        print("✅ App minimized to system tray")
    
    def _run_tray_icon(self):
        """
        Run tray icon in background thread.
        
        Deze methode draait in een aparte thread en blijft actief
        zolang de tray icon zichtbaar is.
        """
        try:
            print("🎯 Tray icon thread started")
            self.tray_icon.run()
            print("🛑 Tray icon stopped")
        except Exception as e:
            print(f"❌ Tray icon error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.system_tray_active = False
            print("📍 Tray icon thread ended")
    
    def _show_from_tray(self):
        """
        Toon het venster weer vanuit system tray.
        
        Deze methode wordt aangeroepen vanuit het tray menu
        en toont het window weer zonder de tray icon te stoppen.
        """
        print("🖥️ Showing window from tray...")
        
        # Toon window weer
        self.deiconify()
        
        # Breng window naar voren
        self.lift()
        self.focus_force()
        
        print("✅ Window restored")

    
    def _real_quit(self):
        """
        Echt afsluiten van de applicatie.
        
        Deze methode wordt aangeroepen vanuit het system tray menu
        of wanneer system tray niet beschikbaar is.
        """
        print("\n🛑 Application closing...")
        
        try:
            # Stop tray icon als die actief is
            if self.system_tray_active and self.tray_icon:
                print("   Stopping tray icon...")
                try:
                    self.tray_icon.stop()
                except:
                    pass
                self.system_tray_active = False
            
            # Stop Spotify monitor
            if hasattr(self, 'spotify_manager'):
                print("   Stopping Spotify monitor...")
                self.spotify_manager.stop()
            
            # Stop auto-reconnect eerst
            if self.serial_manager.reconnect_running:
                print("   Stopping auto-reconnect...")
                self.serial_manager.stop_auto_reconnect()
            
            # Disconnect netjes
            if self.serial_manager.is_connected:
                print("   Disconnecting from device...")
                self.serial_manager.disconnect()
            
            print("✅ Cleanup complete!")
        
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")
        
        finally:
            # Sluit window
            self.destroy()
    
    def _on_closing(self):
        """
        Handle window close event - minimaliseer naar tray.
        
        Deze methode zorgt ervoor dat de app naar de system tray gaat
        in plaats van volledig af te sluiten. De seriële verbinding
        blijft actief op de achtergrond.
        """
        # Normale sluiting -> naar tray
        self._minimize_to_tray()

