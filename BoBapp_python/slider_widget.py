"""
Slider Widget Component - Compact Layout Version

Dit bestand bevat de SliderWidget class die een audio slider representeert.
Elke slider kan gekoppeld worden aan MEERDERE applicaties (groep volume controle).

NIEUWE COMPACTE LAYOUT:
- Master volume: minimaal design
- App sliders: apps links, controls rechts (horizontaal)

File: slider_widget.py
"""

import sys
from pathlib import Path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

import customtkinter as ctk
from typing import Callable, List

from constants import (
    COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK,
    COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK
)


class SliderWidget:
    """
    Een audio slider widget voor groep volume controle.
    
    Fysieke slider op Pico controleert het volume van alle apps in deze groep.
    
    Features:
    - Meerdere apps per slider
    - Compact horizontale layout
    - Volume controls rechts van apps
    - Minimaal master volume design
    
    Attributes:
        index (int): Slider nummer (0-3)
        assigned_apps (List[str]): Lijst van app namen in deze groep
        frame (CTkFrame): Container frame
        apps_container (CTkScrollableFrame): Container voor app tags
        app_menu (CTkOptionMenu): Dropdown voor app selectie
        progress_bar (CTkProgressBar): Visuele volume indicator
        volume_label (CTkLabel): Volume percentage tekst
        on_app_change (Callable): Callback bij app lijst wijziging
    """
    
    def __init__(
        self,
        parent: ctk.CTkFrame,
        index: int,
        available_apps: List[str],
        on_app_change: Callable[[int, List[str]], None],
        is_master_volume: bool = False
    ):
        """
        Initialiseer een nieuwe slider widget.
        
        Args:
            parent: Parent frame waar de slider in komt
            index: Slider nummer (0-3: 0-2 voor apps, 3 voor master)
            available_apps: List van beschikbare app namen (leeg voor master)
            on_app_change: Callback (slider_index, app_list) bij wijziging
            is_master_volume: True als dit de master volume slider is
        """
        self.index = index
        self.on_app_change = on_app_change
        self.is_master_volume = is_master_volume
        self.assigned_apps = []
        
        # Maak container frame
        self.frame = ctk.CTkFrame(
            parent,
            corner_radius=15,
            fg_color=(COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK),
            border_width=2,
            border_color=(COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK)
        )
        self.frame.pack(pady=8, padx=15, fill="x")
        
        if is_master_volume:
            self._create_master_volume_layout()
        else:
            self._create_app_slider_layout(available_apps)
    
    def _create_master_volume_layout(self):
        """Maak compacte master volume layout."""
        # Header row met alles in één lijn
        header_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        header_row.pack(fill="x", padx=15, pady=10)
        
        # Icon + Title links
        ctk.CTkLabel(
            header_row,
            text=f"🔊 Master Volume",
            font=("Roboto", 16, "bold"),
            text_color="orange"
        ).pack(side="left")
        
        # Volume display rechts
        self.volume_label = ctk.CTkLabel(
            header_row,
            text="50%",
            font=("Roboto", 15, "bold"),
            text_color="orange"
        )
        self.volume_label.pack(side="right", padx=5)
        
        ctk.CTkLabel(
            header_row,
            text="Volume:",
            font=("Roboto", 12),
            text_color="gray"
        ).pack(side="right", padx=(0, 3))
        
        # Progress bar onder header (full width)
        self.progress_bar = ctk.CTkProgressBar(
            self.frame,
            height=8
        )
        self.progress_bar.set(0.5)
        self.progress_bar.pack(pady=(0, 10), padx=15, fill="x")
        
        # Dummy vars voor compatibiliteit
        self.apps_container = None
        self.empty_label = None
        self.available_apps = []
        self.app_var = None
        self.app_menu = None
    
    def _create_app_slider_layout(self, available_apps: List[str]):
        """Maak compacte app slider layout - horizontaal."""
        # Header
        header = ctk.CTkLabel(
            self.frame,
            text=f"🎚️ Slider {self.index + 1}",
            font=("Roboto", 16, "bold")
        )
        header.pack(pady=(12, 8))
        
        # Main content: HORIZONTALE layout
        content_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # LINKS: Apps container (neemt meer ruimte)
        left_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        ctk.CTkLabel(
            left_frame,
            text="Toegewezen apps:",
            font=("Roboto", 11),
            text_color="gray",
            anchor="w"
        ).pack(fill="x", pady=(0, 3))
        
        # Apps scrollable container
        self.apps_container = ctk.CTkScrollableFrame(
            left_frame,
            height=90,
            fg_color=("gray90", "gray15")
        )
        self.apps_container.pack(fill="both", expand=True)
        
        # Empty state label
        self.empty_label = ctk.CTkLabel(
            self.apps_container,
            text="Geen apps\ntoegewezen",
            text_color="gray",
            font=("Roboto", 11),
            justify="center"
        )
        self.empty_label.pack(pady=15)
        
        # RECHTS: Controls (dropdown + volume indicator)
        right_frame = ctk.CTkFrame(content_frame, fg_color="transparent", width=180)
        right_frame.pack(side="right", fill="y")
        right_frame.pack_propagate(False)
        
        # Dropdown label
        ctk.CTkLabel(
            right_frame,
            text="Voeg app toe:",
            font=("Roboto", 11),
            text_color="gray"
        ).pack(pady=(0, 3))
        
        # Dropdown menu
        self.available_apps = available_apps
        self.app_var = ctk.StringVar(value="")
        menu_options = ["Selecteer..."] + available_apps
        
        self.app_menu = ctk.CTkOptionMenu(
            right_frame,
            variable=self.app_var,
            values=menu_options,
            width=170,
            height=30,
            font=("Roboto", 12),
            command=self._handle_app_select
        )
        self.app_menu.pack(pady=(0, 10))
        
        # Separator
        separator = ctk.CTkFrame(right_frame, height=1, fg_color="gray40")
        separator.pack(fill="x", pady=8, padx=5)
        
        # Volume indicator
        ctk.CTkLabel(
            right_frame,
            text="Volume:",
            font=("Roboto", 11),
            text_color="gray"
        ).pack(pady=(0, 2))
        
        self.volume_label = ctk.CTkLabel(
            right_frame,
            text="50%",
            font=("Roboto", 14, "bold")
        )
        self.volume_label.pack(pady=(0, 5))
        
        # Progress bar (vertical oriented visually)
        self.progress_bar = ctk.CTkProgressBar(
            right_frame,
            width=140,
            height=6
        )
        self.progress_bar.set(0.5)
        self.progress_bar.pack()
    
    def _handle_app_select(self, app_name: str):
        """Handle app selectie uit dropdown."""
        if app_name == "Selecteer...":
            return
        
        # Add to this slider group
        if app_name not in self.assigned_apps:
            self.assigned_apps.append(app_name)
            self._create_app_tag(app_name)
            self._update_empty_state()
            
            # Notify callback
            if self.on_app_change:
                self.on_app_change(self.index, self.assigned_apps)
        
        # Reset dropdown
        self.app_var.set("Selecteer...")
    
    def _create_app_tag(self, app_name: str):
        """Maak een compact app tag met remove button."""
        if self.is_master_volume or self.apps_container is None:
            return
        
        # Remove empty label if it exists
        try:
            if self.empty_label and self.empty_label.winfo_exists():
                self.empty_label.pack_forget()
        except:
            pass
        
        # App tag frame (compact)
        tag_frame = ctk.CTkFrame(
            self.apps_container,
            fg_color=("gray80", "gray25"),
            corner_radius=5,
            height=30
        )
        tag_frame.pack(fill="x", pady=2, padx=3)
        tag_frame.pack_propagate(False)
        
        # App name label
        app_label = ctk.CTkLabel(
            tag_frame,
            text=app_name,
            font=("Roboto", 12),
            anchor="w"
        )
        app_label.pack(side="left", padx=8, fill="x", expand=True)
        
        # Remove button (klein)
        remove_btn = ctk.CTkButton(
            tag_frame,
            text="✕",
            width=24,
            height=24,
            fg_color="red",
            hover_color="darkred",
            font=("Roboto", 11, "bold"),
            command=lambda: self._remove_app(app_name, tag_frame)
        )
        remove_btn.pack(side="right", padx=2, pady=2)
    
    def _remove_app(self, app_name: str, tag_frame: ctk.CTkFrame):
        """Verwijder app uit deze slider groep."""
        if app_name in self.assigned_apps:
            self.assigned_apps.remove(app_name)
            tag_frame.destroy()
            self._update_empty_state()
            
            # Notify callback
            if self.on_app_change:
                self.on_app_change(self.index, self.assigned_apps)
    
    def _update_empty_state(self):
        """Update empty state label visibility."""
        if self.is_master_volume or self.apps_container is None:
            return
        
        if len(self.assigned_apps) == 0:
            self.empty_label = ctk.CTkLabel(
                self.apps_container,
                text="Geen apps\ntoegewezen",
                text_color="gray",
                font=("Roboto", 11),
                justify="center"
            )
            self.empty_label.pack(pady=15)
    
    def update_volume_display(self, volume: float):
        """Update de visuele volume weergave."""
        volume = max(0.0, min(1.0, volume))
        
        # Update progress bar
        self.progress_bar.set(volume)
        
        # Update percentage label
        percentage = int(volume * 100)
        self.volume_label.configure(text=f"{percentage}%")
    
    def update_available_apps(self, apps: List[str]):
        """Update de lijst van beschikbare apps in de dropdown."""
        if self.is_master_volume or self.app_menu is None:
            return
        
        self.available_apps = apps
        menu_options = ["Selecteer..."] + apps
        self.app_menu.configure(values=menu_options)
    
    def get_assigned_apps(self) -> List[str]:
        """Haal de lijst van toegewezen apps op."""
        return self.assigned_apps.copy()
    
    def set_assigned_apps(self, apps: List[str]):
        """Stel de lijst van toegewezen apps in (bij laden config)."""
        if self.is_master_volume or self.apps_container is None:
            return
        
        # Clear current apps
        for widget in self.apps_container.winfo_children():
            widget.destroy()
        
        # Reset empty_label reference
        self.empty_label = None
        
        self.assigned_apps = apps.copy()
        
        # Recreate app tags
        if len(apps) == 0:
            self._update_empty_state()
        else:
            for app_name in apps:
                self._create_app_tag(app_name)
    
    def get_frame(self) -> ctk.CTkFrame:
        """Geef het container frame terug."""
        return self.frame
