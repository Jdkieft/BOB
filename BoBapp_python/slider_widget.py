"""
Slider Widget Component - Drag & Drop Audio Group System

Dit bestand bevat de SliderWidget class die een audio slider representeert.
Elke slider kan gekoppeld worden aan MEERDERE applicaties (groep volume controle).

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
    - Drag & drop style interface
    - Compact tag display met remove buttons
    - Volume visualisatie (van Pico)
    
    Attributes:
        index (int): Slider nummer (0-2)
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
        on_app_change: Callable[[int, List[str]], None],  # Sends list of apps!
        is_master_volume: bool = False  # True voor master volume slider
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
        self.assigned_apps = []  # List of app names in this group
        
        # Maak container frame
        self.frame = ctk.CTkFrame(
            parent,
            corner_radius=15,
            fg_color=(COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK),
            border_width=2,
            border_color=(COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK)
        )
        self.frame.pack(pady=10, padx=15, fill="x")
        
        # Header met slider nummer
        if is_master_volume:
            header_text = f"🔊 Master Volume (Slider {index + 1})"
            header_color = "orange"
        else:
            header_text = f"🎚️ Slider {index + 1}"
            header_color = None
        
        header = ctk.CTkLabel(
            self.frame,
            text=header_text,
            font=("Roboto", 16, "bold"),
            text_color=header_color
        )
        header.pack(pady=(15, 5))
        
        # Instructie label
        if is_master_volume:
            ctk.CTkLabel(
                self.frame,
                text="⚙️ Controleert systeem volume",
                font=("Roboto", 11, "bold"),
                text_color="orange"
            ).pack(pady=(5, 2))
        else:
            ctk.CTkLabel(
                self.frame,
                text="Klik op apps hieronder om toe te voegen:",
                font=("Roboto", 10),
                text_color="gray"
            ).pack(pady=(5, 2))
        
        # Apps container (scrollable, compact) - alleen voor app sliders
        if not is_master_volume:
            self.apps_container = ctk.CTkScrollableFrame(
                self.frame,
                height=150,
                fg_color=("gray90", "gray15")
            )
            self.apps_container.pack(pady=5, padx=10, fill="x")
        else:
            # Voor master volume: smaller container met info
            self.apps_container = None
            info_frame = ctk.CTkFrame(
                self.frame,
                height=150,
                fg_color=("gray90", "gray15")
            )
            info_frame.pack(pady=5, padx=10, fill="x")
            
            ctk.CTkLabel(
                info_frame,
                text="🎵 System Audio Control\n\nDeze slider regelt het\nvolledige systeem volume",
                font=("Roboto", 11),
                justify="center"
            ).pack(expand=True, pady=50)
        
        # Empty state label (alleen voor app sliders)
        if not is_master_volume:
            self.empty_label = ctk.CTkLabel(
                self.apps_container,
                text="Geen apps toegewezen\n\nKlik hieronder om apps toe te voegen",
                text_color="gray",
                font=("Roboto", 10)
            )
            self.empty_label.pack(pady=10)
        else:
            self.empty_label = None
        
        # Separator en dropdown (alleen voor app sliders)
        if not is_master_volume:
            separator = ctk.CTkFrame(self.frame, height=2, fg_color="gray")
            separator.pack(fill="x", padx=10, pady=5)
            
            # Available apps selector (dropdown)
            ctk.CTkLabel(
                self.frame,
                text="Voeg app toe:",
                font=("Roboto", 10),
                text_color="gray"
            ).pack(pady=(5, 2))
            
            self.available_apps = available_apps
            self.app_var = ctk.StringVar(value="")
            
            # Dropdown menu for available apps
            menu_options = ["Selecteer een app..."] + available_apps
            
            self.app_menu = ctk.CTkOptionMenu(
                self.frame,
                variable=self.app_var,
                values=menu_options,
                width=250,
                height=30,
                font=("Roboto", 11),
                command=self._handle_app_select
            )
            self.app_menu.pack(pady=5, padx=10)
        else:
            self.available_apps = []
            self.app_var = None
            self.app_menu = None
        
        # Volume indicator (read-only, shows Pico slider position)
        volume_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        volume_frame.pack(pady=(10, 5), fill="x", padx=10)
        
        ctk.CTkLabel(
            volume_frame,
            text="Volume:",
            font=("Roboto", 9),
            text_color="gray"
        ).pack(side="left", padx=5)
        
        self.volume_label = ctk.CTkLabel(
            volume_frame,
            text="50%",
            font=("Roboto", 12, "bold")
        )
        self.volume_label.pack(side="right", padx=5)
        
        # Progress bar (read-only visual)
        self.progress_bar = ctk.CTkProgressBar(
            self.frame,
            width=250,
            height=8
        )
        self.progress_bar.set(0.5)
        self.progress_bar.pack(pady=(5, 15), padx=10)
    
    def _handle_app_select(self, app_name: str):
        """
        Handle app selectie uit dropdown.
        
        Voegt de geselecteerde app toe aan de groep en maakt een tag.
        
        Args:
            app_name: Geselecteerde app naam
        """
        if app_name == "Selecteer een app...":
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
        self.app_var.set("Selecteer een app...")
    
    def _create_app_tag(self, app_name: str):
        """
        Maak een compact app tag met remove button.
        
        Args:
            app_name: Naam van de app om weer te geven
        """
        # Niet voor master volume
        if self.is_master_volume or self.apps_container is None:
            return
        
        # Remove empty label if it exists and is mapped
        try:
            if self.empty_label and self.empty_label.winfo_exists():
                self.empty_label.pack_forget()
        except:
            pass  # Label is al vernietigd, geen probleem
        
        # App tag frame (compact horizontal layout)
        tag_frame = ctk.CTkFrame(
            self.apps_container,
            fg_color=("gray80", "gray25"),
            corner_radius=5,
            height=30
        )
        tag_frame.pack(fill="x", pady=2, padx=5)
        tag_frame.pack_propagate(False)
        
        # App name label
        app_label = ctk.CTkLabel(
            tag_frame,
            text=app_name,
            font=("Roboto", 11),
            anchor="w"
        )
        app_label.pack(side="left", padx=10, fill="x", expand=True)
        
        # Remove button
        remove_btn = ctk.CTkButton(
            tag_frame,
            text="✕",
            width=25,
            height=25,
            fg_color="red",
            hover_color="darkred",
            font=("Roboto", 12, "bold"),
            command=lambda: self._remove_app(app_name, tag_frame)
        )
        remove_btn.pack(side="right", padx=3, pady=2)
    
    def _remove_app(self, app_name: str, tag_frame: ctk.CTkFrame):
        """
        Verwijder app uit deze slider groep.
        
        Args:
            app_name: Naam van de app om te verwijderen
            tag_frame: Frame van de tag om te vernietigen
        """
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
                text="Geen apps toegewezen\n\nKlik hieronder om apps toe te voegen",
                text_color="gray",
                font=("Roboto", 10)
            )
            self.empty_label.pack(pady=10)
    
    def update_volume_display(self, volume: float):
        """
        Update de visuele volume weergave (komt van Pico).
        
        Args:
            volume: Volume level tussen 0.0 en 1.0
        """
        # Clamp tussen 0 en 1
        volume = max(0.0, min(1.0, volume))
        
        # Update progress bar
        self.progress_bar.set(volume)
        
        # Update percentage label
        percentage = int(volume * 100)
        self.volume_label.configure(text=f"{percentage}%")
    
    def update_available_apps(self, apps: List[str]):
        """
        Update de lijst van beschikbare apps in de dropdown.
        
        Args:
            apps: Nieuwe lijst van app namen
        """
        if self.is_master_volume or self.app_menu is None:
            return
        
        self.available_apps = apps
        menu_options = ["Selecteer een app..."] + apps
        self.app_menu.configure(values=menu_options)
    
    def get_assigned_apps(self) -> List[str]:
        """
        Haal de lijst van toegewezen apps op.
        
        Returns:
            Copy van de assigned apps lijst
        """
        return self.assigned_apps.copy()
    
    def set_assigned_apps(self, apps: List[str]):
        """
        Stel de lijst van toegewezen apps in (bij laden config).
        
        Wist huidige tags en maakt nieuwe tags voor elke app.
        
        Args:
            apps: Lijst van app namen om toe te wijzen
        """
        # Niet voor master volume
        if self.is_master_volume or self.apps_container is None:
            return
        
        # Clear current apps (including empty_label!)
        for widget in self.apps_container.winfo_children():
            widget.destroy()
        
        # Reset empty_label reference (het is nu vernietigd)
        self.empty_label = None
        
        self.assigned_apps = apps.copy()
        
        # Recreate app tags
        if len(apps) == 0:
            self._update_empty_state()
        else:
            for app_name in apps:
                self._create_app_tag(app_name)
    
    def get_frame(self) -> ctk.CTkFrame:
        """
        Geef het container frame terug.
        
        Returns:
            Het CTkFrame object
        """
        return self.frame