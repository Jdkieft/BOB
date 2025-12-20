"""
Slider Widget Component
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
    """Een audio slider widget voor app volume controle."""
    
    def __init__(
        self,
        parent: ctk.CTkFrame,
        index: int,
        available_apps: List[str],
        on_app_change: Callable[[int, str], None]
    ):
        self.index = index
        self.on_app_change = on_app_change
        
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
        header = ctk.CTkLabel(
            self.frame,
            text=f"🎚️ Slider {index + 1}",
            font=("Roboto", 16, "bold")
        )
        header.pack(pady=(15, 5))
        
        # Instructie label
        ctk.CTkLabel(
            self.frame,
            text="Select App:",
            font=("Roboto", 11),
            text_color="gray"
        ).pack(pady=(5, 2))
        
        # App selectie variable
        self.app_var = ctk.StringVar(value="Master Volume")
        
        # Bouw dropdown menu opties
        menu_options = ["Master Volume", "System Sounds"] + available_apps
        
        # Maak dropdown menu
        self.app_menu = ctk.CTkOptionMenu(
            self.frame,
            variable=self.app_var,
            values=menu_options,
            width=280,
            height=35,
            command=self._handle_app_change
        )
        self.app_menu.pack(pady=5, padx=10)
        
        # Progress bar voor visuele feedback
        self.progress_bar = ctk.CTkProgressBar(
            self.frame,
            width=280,
            height=15
        )
        self.progress_bar.set(0.5)  # Standaard 50%
        self.progress_bar.pack(pady=10, padx=10)
        
        # Volume percentage label
        self.volume_label = ctk.CTkLabel(
            self.frame,
            text="50%",
            font=("Roboto", 12)
        )
        self.volume_label.pack(pady=(0, 15))
    
    def _handle_app_change(self, app_name: str) -> None:
        """Interne handler voor app selectie wijziging."""
        if self.on_app_change:
            self.on_app_change(self.index, app_name)
    
    def set_app(self, app_name: str) -> None:
        """Stel de geselecteerde app in (programmatisch)."""
        self.app_var.set(app_name)
    
    def get_selected_app(self) -> str:
        """Haal de momenteel geselecteerde app op."""
        return self.app_var.get()
    
    def update_volume_display(self, volume: float) -> None:
        """Update de visuele volume weergave."""
        # Clamp tussen 0 en 1
        volume = max(0.0, min(1.0, volume))
        
        # Update progress bar
        self.progress_bar.set(volume)
        
        # Update percentage label
        percentage = int(volume * 100)
        self.volume_label.configure(text=f"{percentage}%")
    
    def update_available_apps(self, apps: List[str]) -> None:
        """Update de lijst van beschikbare apps in de dropdown."""
        menu_options = ["Master Volume", "System Sounds"] + apps
        self.app_menu.configure(values=menu_options)
    
    def get_frame(self) -> ctk.CTkFrame:
        """Geef het container frame terug."""
        return self.frame