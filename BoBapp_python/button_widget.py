"""
Button Widget Component

Dit bestand bevat de ButtonWidget class die een enkele configureerbare
knop representeert in de 3x3 grid. Elke knop kan een icon, label en
hotkey weergeven en is volledig klikbaar.
"""

import customtkinter as ctk
from typing import Callable, Optional, Dict
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from constants import (
    BUTTON_SIZE, BUTTON_CORNER_RADIUS, BUTTON_BORDER_WIDTH,
    COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK,
    COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK,
    COLOR_BUTTON_ACTIVE, COLOR_BUTTON_FOCUS,
    FONT_ICON
)


class ButtonWidget:
    """
    Een enkele configureerbare button in de grid.
    
    Deze class beheert:
    - De visuele weergave van de button
    - Hover effecten
    - Click events
    - Configuratie weergave (icon, label, hotkey)
    
    Attributes:
        index (int): Button nummer (0-8)
        outer_frame (CTkFrame): Container frame
        main_frame (CTkFrame): Klikbare button frame
        icon_label (CTkLabel): Icon weergave (emoji)
        action_label (CTkLabel): Actie beschrijving
        hotkey_label (CTkLabel): Hotkey weergave
        num_label (CTkLabel): Button nummer badge
        on_click (Callable): Callback functie voor clicks
    """
    
    def __init__(
        self,
        parent: ctk.CTkFrame,
        index: int,
        row: int,
        col: int,
        on_click: Callable[[int], None]
    ):
        """
        Initialiseer een nieuwe button widget.
        
        Args:
            parent: Parent frame waar de button in komt
            index: Button nummer (0-8)
            row: Rij positie in grid (0-2)
            col: Kolom positie in grid (0-2)
            on_click: Callback functie die wordt aangeroepen bij click
        """
        self.index = index
        self.on_click = on_click
        
        # Maak outer container
        self.outer_frame = ctk.CTkFrame(
            parent,
            width=BUTTON_SIZE,
            height=BUTTON_SIZE,
            fg_color="transparent"
        )
        self.outer_frame.grid(row=row, column=col, padx=10, pady=10)
        self.outer_frame.grid_propagate(False)
        
        # Maak klikbare button frame
        self.main_frame = ctk.CTkFrame(
            self.outer_frame,
            width=BUTTON_SIZE,
            height=BUTTON_SIZE,
            corner_radius=BUTTON_CORNER_RADIUS,
            fg_color=(COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK),
            border_width=BUTTON_BORDER_WIDTH,
            border_color=(COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK)
        )
        self.main_frame.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Bind click event op frame zelf
        self.main_frame.bind("<Button-1>", lambda e: self._handle_click())
        
        # Maak icon label
        self.icon_label = ctk.CTkLabel(
            self.main_frame,
            text="➕",
            font=FONT_ICON,
            cursor="hand2"
        )
        self.icon_label.place(relx=0.5, rely=0.35, anchor="center")
        self.icon_label.bind("<Button-1>", lambda e: self._handle_click())
        
        # Maak action label
        self.action_label = ctk.CTkLabel(
            self.main_frame,
            text="Not Set",
            font=("Roboto", 11, "bold"),
            wraplength=140,
            cursor="hand2"
        )
        self.action_label.place(relx=0.5, rely=0.65, anchor="center")
        self.action_label.bind("<Button-1>", lambda e: self._handle_click())
        
        # Maak hotkey label
        self.hotkey_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=("Courier", 9),
            fg_color=(COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK),
            corner_radius=5,
            height=25,
            width=140,
            cursor="hand2"
        )
        self.hotkey_label.place(relx=0.5, rely=0.85, anchor="center")
        self.hotkey_label.bind("<Button-1>", lambda e: self._handle_click())
        
        # Maak nummer badge
        self.num_label = ctk.CTkLabel(
            self.main_frame,
            text=f"#{index + 1}",
            font=("Roboto", 13, "bold"),
            fg_color=(COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK),
            corner_radius=8,
            width=45,
            height=30,
            cursor="hand2"
        )
        self.num_label.place(x=8, y=8)
        self.num_label.bind("<Button-1>", lambda e: self._handle_click())
        
        # Bind hover events
        self.main_frame.bind("<Enter>", self._on_hover_enter)
        self.main_frame.bind("<Leave>", self._on_hover_leave)
        
        # Track of button geconfigureerd is
        self.is_configured = False
    
    def _handle_click(self) -> None:
        """
        Interne handler voor click events.
        Roept de externe on_click callback aan.
        """
        if self.on_click:
            self.on_click(self.index)
    
    def _on_hover_enter(self, event) -> None:
        """
        Handler voor mouse enter (hover start).
        Verander border naar focus kleur.
        """
        self.main_frame.configure(border_color=COLOR_BUTTON_FOCUS, cursor="hand2")
    
    def _on_hover_leave(self, event) -> None:
        """
        Handler voor mouse leave (hover end).
        Reset border naar normale of active kleur.
        """
        if self.is_configured:
            self.main_frame.configure(border_color=COLOR_BUTTON_ACTIVE)
        else:
            self.main_frame.configure(
                border_color=(COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK)
            )
    
    def update_display(self, config: Optional[Dict[str, str]]) -> None:
        """
        Update de visuele weergave van de button.
        
        Args:
            config: Dict met 'icon', 'label' en 'hotkey', of None om te clearen
        """
        if config:
            # Button is geconfigureerd
            self.is_configured = True
            
            # Update labels
            self.icon_label.configure(text=config.get('icon', '🎮'))
            self.action_label.configure(text=config.get('label', 'Action'))
            self.hotkey_label.configure(text=config.get('hotkey', ''))
            
            # Update border naar active kleur
            self.main_frame.configure(border_color=COLOR_BUTTON_ACTIVE)
        else:
            # Button is niet geconfigureerd
            self.is_configured = False
            
            # Reset naar defaults
            self.icon_label.configure(text="➕")
            self.action_label.configure(text="Not Set")
            self.hotkey_label.configure(text="")
            
            # Reset border naar normale kleur
            self.main_frame.configure(
                border_color=(COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK)
            )
    
    def get_widgets(self) -> Dict[str, ctk.CTkBaseClass]:
        """
        Geef alle widget componenten terug.
        
        Returns:
            Dict met alle CTk widgets voor low-level toegang
        """
        return {
            'outer': self.outer_frame,
            'frame': self.main_frame,
            'icon': self.icon_label,
            'action_label': self.action_label,
            'hotkey_label': self.hotkey_label,
            'num_label': self.num_label,
            'index': self.index
        }