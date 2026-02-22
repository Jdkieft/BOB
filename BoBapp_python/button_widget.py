"""
Button Widget Component

Vaste maar comfortabele knopgrootte (185x185px).
Fonts zijn proportioneel en leesbaar op alle schermen.

File: button_widget.py
"""

import customtkinter as ctk
from typing import Callable, Optional, Dict
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from constants import (
    BUTTON_CORNER_RADIUS, BUTTON_BORDER_WIDTH,
    COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK,
    COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK,
    COLOR_BUTTON_ACTIVE, COLOR_BUTTON_FOCUS,
)

BUTTON_SIZE = 185


class ButtonWidget:
    """Een enkele configureerbare button in de 3x3 grid."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        index: int,
        row: int,
        col: int,
        on_click: Callable[[int], None]
    ):
        self.index = index
        self.on_click = on_click
        self.is_configured = False

        # Outer container met vaste maat
        self.outer_frame = ctk.CTkFrame(
            parent,
            width=BUTTON_SIZE,
            height=BUTTON_SIZE,
            fg_color="transparent"
        )
        self.outer_frame.grid(row=row, column=col, padx=8, pady=8)
        self.outer_frame.grid_propagate(False)

        # Klikbare button frame
        self.main_frame = ctk.CTkFrame(
            self.outer_frame,
            corner_radius=BUTTON_CORNER_RADIUS,
            fg_color=(COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK),
            border_width=BUTTON_BORDER_WIDTH,
            border_color=(COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK)
        )
        self.main_frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.main_frame.bind("<Button-1>", lambda e: self._handle_click())

        # Icon
        self.icon_label = ctk.CTkLabel(
            self.main_frame,
            text="➕",
            font=("Segoe UI Emoji", 46),
            cursor="hand2"
        )
        self.icon_label.place(relx=0.5, rely=0.33, anchor="center")
        self.icon_label.bind("<Button-1>", lambda e: self._handle_click())

        # Actie-naam
        self.action_label = ctk.CTkLabel(
            self.main_frame,
            text="Not Set",
            font=("Roboto", 13, "bold"),
            wraplength=155,
            cursor="hand2"
        )
        self.action_label.place(relx=0.5, rely=0.63, anchor="center")
        self.action_label.bind("<Button-1>", lambda e: self._handle_click())

        # Hotkey badge
        self.hotkey_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=("Courier", 10),
            fg_color=(COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK),
            corner_radius=5,
            height=26,
            cursor="hand2"
        )
        self.hotkey_label.place(relx=0.5, rely=0.87, anchor="center", relwidth=0.85)
        self.hotkey_label.bind("<Button-1>", lambda e: self._handle_click())

        # Nummer badge
        self.num_label = ctk.CTkLabel(
            self.main_frame,
            text=f"#{index + 1}",
            font=("Roboto", 13, "bold"),
            fg_color=(COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK),
            corner_radius=7,
            width=42,
            height=28,
            cursor="hand2"
        )
        self.num_label.place(x=8, y=8)
        self.num_label.bind("<Button-1>", lambda e: self._handle_click())

        self.main_frame.bind("<Enter>", self._on_hover_enter)
        self.main_frame.bind("<Leave>", self._on_hover_leave)

    def _handle_click(self):
        if self.on_click:
            self.on_click(self.index)

    def _on_hover_enter(self, event):
        self.main_frame.configure(border_color=COLOR_BUTTON_FOCUS, cursor="hand2")

    def _on_hover_leave(self, event):
        if self.is_configured:
            self.main_frame.configure(border_color=COLOR_BUTTON_ACTIVE)
        else:
            self.main_frame.configure(
                border_color=(COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK)
            )

    def update_display(self, config: Optional[Dict[str, str]]) -> None:
        if config:
            self.is_configured = True
            self.icon_label.configure(text=config.get('icon', '🎮'))
            self.action_label.configure(text=config.get('label', 'Action'))
            if config.get('app_path'):
                self.hotkey_label.configure(text='🚀 Launch App')
            else:
                self.hotkey_label.configure(text=config.get('hotkey', ''))
            self.main_frame.configure(border_color=COLOR_BUTTON_ACTIVE)
        else:
            self.is_configured = False
            self.icon_label.configure(text="➕")
            self.action_label.configure(text="Not Set")
            self.hotkey_label.configure(text="")
            self.main_frame.configure(
                border_color=(COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK)
            )

    def get_widgets(self) -> Dict[str, ctk.CTkBaseClass]:
        return {
            'outer': self.outer_frame,
            'frame': self.main_frame,
            'icon': self.icon_label,
            'action_label': self.action_label,
            'hotkey_label': self.hotkey_label,
            'num_label': self.num_label,
            'index': self.index
        }
