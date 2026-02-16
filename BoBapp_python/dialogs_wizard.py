"""
Dialog Windows - Wizard Style Version

Wizard-style button configuratie dialog met duidelijke stappen:
- Step 1: Icon & Label kiezen
- Step 2: Hotkey configureren
- Step 3: Preview & Bevestigen
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


class WizardButtonConfigDialog:
    """Wizard-style dialog voor het configureren van een button."""
    
    # Media control presets
    MEDIA_CONTROLS = [
        {"name": "Play/Pause", "hotkey": "playpause", "icon": "⏯️"},
        {"name": "Next Track", "hotkey": "nexttrack", "icon": "⏭️"},
        {"name": "Previous Track", "hotkey": "previoustrack", "icon": "⏮️"},
    ]
    
    # Uitgebreide emoji lijst - gecategoriseerd
    EMOJI_CATEGORIES = {
        "Media": ["🎮", "🎵", "🎤", "🔊", "🔇", "📢", "⏯️", "⏭️", "⏮️", "⏹️", "🔁", "🔀", "🎧", "📻", "🎬", "📺"],
        "Tech": ["💻", "⌨️", "🖱️", "📱", "⚙️", "🛠️", "💾", "📁", "🖥️", "📡", "🔌", "💡"],
        "Action": ["🚀", "⭐", "⚡", "🎯", "🔥", "💥", "✨", "🎪", "🎨", "📸", "🔦", "🧲"],
        "Communication": ["💬", "📧", "📞", "📮", "📬", "📭", "📪", "📫", "✉️", "📨", "📩", "📤"],
        "Gaming": ["🎮", "🕹️", "🎲", "🎰", "🎳", "🎯", "🎪", "🏆", "🥇", "🥈", "🥉", "👾"],
        "Symbols": ["❤️", "💚", "💙", "💜", "🧡", "💛", "🖤", "🤍", "🤎", "❓", "❗", "⚠️"],
    }
    
    def __init__(
        self,
        parent: ctk.CTk,
        button_index: int,
        mode: int,
        current_config: Optional[Dict[str, str]],
        on_save: Callable[[Dict[str, str]], None],
        on_clear: Optional[Callable[[], None]] = None
    ):
        """Initialiseer de wizard dialog."""
        self.on_save = on_save
        self.on_clear = on_clear
        self.button_index = button_index
        self.mode = mode
        self.current_config = current_config or {}
        
        # Wizard state
        self.current_step = 0
        self.total_steps = 3
        
        # Stored values
        self.selected_icon = self.current_config.get('icon', '🎮')
        self.selected_label = self.current_config.get('label', '')
        self.selected_hotkey = self.current_config.get('hotkey', '')
        self.selected_hotkey_type = 'custom'  # 'custom' or 'media'
        
        # Detect if current config is media
        if self.selected_hotkey:
            is_media = any(mc['hotkey'] == self.selected_hotkey for mc in self.MEDIA_CONTROLS)
            if is_media:
                self.selected_hotkey_type = 'media'
        
        # Maak toplevel dialog
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(f"Configure Button #{button_index + 1} - Step 1/3")
        self.dialog.geometry("700x650")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - 350
        y = (self.dialog.winfo_screenheight() // 2) - 325
        self.dialog.geometry(f"700x650+{x}+{y}")
        
        # Main container
        self.main_container = ctk.CTkFrame(self.dialog, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create wizard UI
        self._create_progress_bar()
        self._create_content_area()
        self._create_navigation_buttons()
        
        # Show first step
        self._show_step(0)
    
    def _create_progress_bar(self):
        """Maak de wizard progress indicator."""
        progress_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=("gray85", "gray20"),
            corner_radius=12,
            height=100
        )
        progress_frame.pack(fill="x", pady=(0, 15))
        progress_frame.pack_propagate(False)
        
        # Title
        self.step_title = ctk.CTkLabel(
            progress_frame,
            text=f"Step 1 of {self.total_steps}: Choose Icon & Label",
            font=("Roboto", 20, "bold")
        )
        self.step_title.pack(pady=(15, 5))
        
        # Subtitle
        self.step_subtitle = ctk.CTkLabel(
            progress_frame,
            text=f"Button #{self.button_index + 1} - Mode {self.mode + 1}",
            font=("Roboto", 13),
            text_color="gray"
        )
        self.step_subtitle.pack(pady=(0, 10))
        
        # Progress dots
        dots_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        dots_frame.pack(pady=(0, 10))
        
        self.progress_dots = []
        for i in range(self.total_steps):
            dot = ctk.CTkLabel(
                dots_frame,
                text="●",
                font=("Roboto", 24),
                text_color="gray50",
                width=30
            )
            dot.pack(side="left", padx=5)
            self.progress_dots.append(dot)
    
    def _create_content_area(self):
        """Maak het content gebied waar steps worden getoond."""
        self.content_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=("gray90", "gray17"),
            corner_radius=12
        )
        self.content_frame.pack(fill="both", expand=True, pady=(0, 15))
    
    def _create_navigation_buttons(self):
        """Maak de navigatie buttons."""
        nav_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        nav_frame.pack(fill="x")
        
        # Back button (links)
        self.back_button = ctk.CTkButton(
            nav_frame,
            text="⬅️ Back",
            command=self._go_back,
            height=55,
            width=150,
            font=("Roboto", 15, "bold"),
            fg_color="gray",
            hover_color="gray30"
        )
        self.back_button.pack(side="left")
        self.back_button.configure(state="disabled")  # Disabled op step 1
        
        # Cancel button (midden)
        cancel_button = ctk.CTkButton(
            nav_frame,
            text="❌ Cancel",
            command=self.dialog.destroy,
            height=55,
            width=120,
            font=("Roboto", 14),
            fg_color="red",
            hover_color="darkred"
        )
        cancel_button.pack(side="left", padx=10)
        
        # Next/Finish button (rechts)
        self.next_button = ctk.CTkButton(
            nav_frame,
            text="Next ➡️",
            command=self._go_next,
            height=55,
            font=("Roboto", 16, "bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.next_button.pack(side="right", fill="x", expand=True)
    
    def _update_progress_ui(self):
        """Update de progress indicator."""
        # Update title
        titles = [
            f"Step 1 of {self.total_steps}: Choose Icon & Label",
            f"Step 2 of {self.total_steps}: Configure Hotkey",
            f"Step 3 of {self.total_steps}: Preview & Confirm"
        ]
        self.step_title.configure(text=titles[self.current_step])
        
        # Update dots
        for i, dot in enumerate(self.progress_dots):
            if i < self.current_step:
                dot.configure(text_color="green")  # Completed
            elif i == self.current_step:
                dot.configure(text_color=("blue", "lightblue"))  # Current
            else:
                dot.configure(text_color="gray50")  # Not yet
        
        # Update buttons
        if self.current_step == 0:
            self.back_button.configure(state="disabled")
        else:
            self.back_button.configure(state="normal")
        
        if self.current_step == self.total_steps - 1:
            self.next_button.configure(text="💾 SAVE & FINISH")
        else:
            self.next_button.configure(text="Next ➡️")
    
    def _show_step(self, step: int):
        """Toon een specifieke wizard step."""
        # Clear content area
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Show appropriate step
        if step == 0:
            self._show_step_icon_label()
        elif step == 1:
            self._show_step_hotkey()
        elif step == 2:
            self._show_step_preview()
        
        self._update_progress_ui()
    
    # ========================================================================
    # STEP 1: ICON & LABEL
    # ========================================================================
    
    def _show_step_icon_label(self):
        """Step 1: Icon en label kiezen."""
        # Scrollable container
        scroll_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color="transparent"
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Instructie
        ctk.CTkLabel(
            scroll_frame,
            text="Customize how your button looks:",
            font=("Roboto", 15, "bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 15))
        
        # Icon sectie
        icon_section = ctk.CTkFrame(scroll_frame, fg_color=("gray85", "gray20"), corner_radius=10)
        icon_section.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            icon_section,
            text="1️⃣ Choose an Icon",
            font=("Roboto", 16, "bold"),
            anchor="w"
        ).pack(padx=15, pady=(15, 10), anchor="w")
        
        # Current icon display + manual entry
        icon_row = ctk.CTkFrame(icon_section, fg_color="transparent")
        icon_row.pack(fill="x", padx=15, pady=(0, 10))
        
        # Large icon preview
        self.icon_preview = ctk.CTkLabel(
            icon_row,
            text=self.selected_icon,
            font=("Segoe UI Emoji", 50),
            width=90,
            height=90,
            fg_color=("gray75", "gray30"),
            corner_radius=10
        )
        self.icon_preview.pack(side="left", padx=(0, 15))
        
        # Icon entry
        entry_col = ctk.CTkFrame(icon_row, fg_color="transparent")
        entry_col.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(
            entry_col,
            text="Or type any emoji:",
            font=("Roboto", 12),
            text_color="gray",
            anchor="w"
        ).pack(fill="x")
        
        self.icon_entry = ctk.CTkEntry(
            entry_col,
            height=50,
            placeholder_text="🎮",
            font=("Segoe UI Emoji", 24),
            justify="center"
        )
        self.icon_entry.insert(0, self.selected_icon)
        self.icon_entry.bind("<KeyRelease>", lambda e: self._update_icon_preview())
        self.icon_entry.pack(fill="x", pady=(5, 0))
        
        # Emoji picker met categorieën
        ctk.CTkLabel(
            icon_section,
            text="Quick pick from categories:",
            font=("Roboto", 12),
            text_color="gray",
            anchor="w"
        ).pack(padx=15, pady=(10, 5), anchor="w")
        
        # Emoji categories
        for category, emojis in self.EMOJI_CATEGORIES.items():
            cat_frame = ctk.CTkFrame(icon_section, fg_color="transparent")
            cat_frame.pack(fill="x", padx=15, pady=3)
            
            # Category label
            ctk.CTkLabel(
                cat_frame,
                text=f"{category}:",
                font=("Roboto", 11, "bold"),
                width=100,
                anchor="w"
            ).pack(side="left", padx=(0, 10))
            
            # Emoji buttons
            emoji_container = ctk.CTkFrame(cat_frame, fg_color="transparent")
            emoji_container.pack(side="left", fill="x", expand=True)
            
            for emoji in emojis[:12]:  # Limit per row
                btn = ctk.CTkButton(
                    emoji_container,
                    text=emoji,
                    width=38,
                    height=38,
                    font=("Segoe UI Emoji", 18),
                    fg_color="transparent",
                    hover_color=("gray75", "gray30"),
                    command=lambda e=emoji: self._set_icon(e)
                )
                btn.pack(side="left", padx=1)
        
        # Spacer
        ctk.CTkFrame(scroll_frame, height=5, fg_color="transparent").pack()
        
        # Label sectie
        label_section = ctk.CTkFrame(scroll_frame, fg_color=("gray85", "gray20"), corner_radius=10)
        label_section.pack(fill="x")
        
        ctk.CTkLabel(
            label_section,
            text="2️⃣ Enter a Label",
            font=("Roboto", 16, "bold"),
            anchor="w"
        ).pack(padx=15, pady=(15, 10), anchor="w")
        
        ctk.CTkLabel(
            label_section,
            text="This will appear on your button",
            font=("Roboto", 11),
            text_color="gray",
            anchor="w"
        ).pack(padx=15, pady=(0, 10), anchor="w")
        
        self.label_entry = ctk.CTkEntry(
            label_section,
            height=55,
            placeholder_text="e.g., Discord Mute, OBS Record, Spotify Pause...",
            font=("Roboto", 15)
        )
        self.label_entry.insert(0, self.selected_label)
        self.label_entry.pack(fill="x", padx=15, pady=(0, 15))
    
    def _set_icon(self, emoji: str):
        """Set selected emoji."""
        self.icon_entry.delete(0, "end")
        self.icon_entry.insert(0, emoji)
        self._update_icon_preview()
    
    def _update_icon_preview(self):
        """Update icon preview."""
        icon = self.icon_entry.get() or "🎮"
        self.icon_preview.configure(text=icon)
    
    # ========================================================================
    # STEP 2: HOTKEY
    # ========================================================================
    
    def _show_step_hotkey(self):
        """Step 2: Hotkey configureren."""
        # Save step 1 values
        self.selected_icon = self.icon_entry.get().strip() or '🎮'
        self.selected_label = self.label_entry.get().strip() or 'Unnamed'
        
        # Scrollable container
        scroll_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color="transparent"
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Instructie
        ctk.CTkLabel(
            scroll_frame,
            text="Choose what happens when you press this button:",
            font=("Roboto", 15, "bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 15))
        
        # Type selector
        type_frame = ctk.CTkFrame(scroll_frame, fg_color=("gray85", "gray20"), corner_radius=10)
        type_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            type_frame,
            text="Select Action Type:",
            font=("Roboto", 14, "bold"),
            anchor="w"
        ).pack(padx=15, pady=(15, 10), anchor="w")
        
        self.hotkey_type_var = ctk.StringVar(value=self.selected_hotkey_type)
        
        # Radio buttons voor type
        type_options = ctk.CTkFrame(type_frame, fg_color="transparent")
        type_options.pack(fill="x", padx=15, pady=(0, 15))
        
        media_radio = ctk.CTkRadioButton(
            type_options,
            text="🎵 Media Control (Play, Pause, Next, etc.)",
            variable=self.hotkey_type_var,
            value="media",
            font=("Roboto", 13),
            command=self._on_hotkey_type_change
        )
        media_radio.pack(anchor="w", pady=5)
        
        custom_radio = ctk.CTkRadioButton(
            type_options,
            text="⌨️ Custom Keyboard Shortcut",
            variable=self.hotkey_type_var,
            value="custom",
            font=("Roboto", 13),
            command=self._on_hotkey_type_change
        )
        custom_radio.pack(anchor="w", pady=5)
        
        # Content area (changes based on type)
        self.hotkey_content_frame = ctk.CTkFrame(
            scroll_frame,
            fg_color=("gray85", "gray20"),
            corner_radius=10
        )
        self.hotkey_content_frame.pack(fill="x")
        
        # Show appropriate content
        self._update_hotkey_content()
    
    def _on_hotkey_type_change(self):
        """Handle hotkey type change."""
        self._update_hotkey_content()
    
    def _update_hotkey_content(self):
        """Update hotkey content based on selected type."""
        # Clear content
        for widget in self.hotkey_content_frame.winfo_children():
            widget.destroy()
        
        hotkey_type = self.hotkey_type_var.get()
        
        if hotkey_type == "media":
            self._show_media_controls()
        else:
            self._show_custom_hotkey()
    
    def _show_media_controls(self):
        """Show media control options."""
        ctk.CTkLabel(
            self.hotkey_content_frame,
            text="Choose a Media Control:",
            font=("Roboto", 14, "bold"),
            anchor="w"
        ).pack(padx=15, pady=(15, 10), anchor="w")
        
        self.media_var = ctk.StringVar(value=self.selected_hotkey if self.selected_hotkey_type == 'media' else "")
        
        # Large buttons voor elke media control
        for mc in self.MEDIA_CONTROLS:
            btn_frame = ctk.CTkFrame(
                self.hotkey_content_frame,
                fg_color=("gray75", "gray25"),
                corner_radius=8
            )
            btn_frame.pack(fill="x", padx=15, pady=5)
            
            radio = ctk.CTkRadioButton(
                btn_frame,
                text="",
                variable=self.media_var,
                value=mc['hotkey'],
                width=20
            )
            radio.pack(side="left", padx=10)
            
            # Icon + text
            content = ctk.CTkFrame(btn_frame, fg_color="transparent")
            content.pack(side="left", fill="x", expand=True, pady=10)
            
            ctk.CTkLabel(
                content,
                text=f"{mc['icon']} {mc['name']}",
                font=("Roboto", 15, "bold"),
                anchor="w"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                content,
                text=f"Key: {mc['hotkey']}",
                font=("Courier", 11),
                text_color="gray",
                anchor="w"
            ).pack(anchor="w")
        
        ctk.CTkFrame(self.hotkey_content_frame, height=15, fg_color="transparent").pack()
    
    def _show_custom_hotkey(self):
        """Show custom hotkey builder."""
        ctk.CTkLabel(
            self.hotkey_content_frame,
            text="Build Your Keyboard Shortcut:",
            font=("Roboto", 14, "bold"),
            anchor="w"
        ).pack(padx=15, pady=(15, 10), anchor="w")
        
        # Modifiers
        mods_frame = ctk.CTkFrame(self.hotkey_content_frame, fg_color="transparent")
        mods_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            mods_frame,
            text="Modifiers (optional):",
            font=("Roboto", 12, "bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 8))
        
        # Parse current hotkey for modifiers
        current_parts = self.selected_hotkey.split('+') if self.selected_hotkey_type == 'custom' else []
        
        self.modifier_vars = {}
        modifiers_container = ctk.CTkFrame(mods_frame, fg_color="transparent")
        modifiers_container.pack(fill="x")
        
        for mod in ['ctrl', 'shift', 'alt', 'win']:
            var = ctk.BooleanVar(value=(mod in current_parts))
            self.modifier_vars[mod] = var
            
            cb = ctk.CTkCheckBox(
                modifiers_container,
                text=mod.upper(),
                variable=var,
                font=("Roboto", 13, "bold"),
                width=120,
                command=self._update_hotkey_preview
            )
            cb.pack(side="left", padx=5)
        
        # Main key
        key_frame = ctk.CTkFrame(self.hotkey_content_frame, fg_color="transparent")
        key_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            key_frame,
            text="Main Key (required):",
            font=("Roboto", 12, "bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 8))
        
        # Get current main key
        current_key = ""
        if self.selected_hotkey_type == 'custom' and current_parts:
            # Last part is the main key
            possible_key = current_parts[-1]
            if possible_key not in ['ctrl', 'shift', 'alt', 'win']:
                current_key = possible_key
        
        self.key_entry = ctk.CTkEntry(
            key_frame,
            height=50,
            placeholder_text="e.g., m, f1, space, enter...",
            font=("Roboto", 14)
        )
        self.key_entry.insert(0, current_key)
        self.key_entry.bind("<KeyRelease>", lambda e: self._update_hotkey_preview())
        self.key_entry.pack(fill="x")
        
        # Live preview
        preview_frame = ctk.CTkFrame(self.hotkey_content_frame, fg_color=("gray70", "gray30"), corner_radius=8)
        preview_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            preview_frame,
            text="Preview:",
            font=("Roboto", 11),
            text_color="gray"
        ).pack(pady=(10, 5))
        
        self.hotkey_preview_label = ctk.CTkLabel(
            preview_frame,
            text=self.selected_hotkey if self.selected_hotkey_type == 'custom' else "ctrl+shift+m",
            font=("Courier", 18, "bold"),
            text_color=("green", "lightgreen")
        )
        self.hotkey_preview_label.pack(pady=(0, 10))
        
        self._update_hotkey_preview()
        
        # Help text
        help_frame = ctk.CTkFrame(self.hotkey_content_frame, fg_color=("gray70", "gray30"), corner_radius=8)
        help_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            help_frame,
            text=HOTKEY_INFO_TEXT,
            font=("Courier", 10),
            justify="left",
            anchor="w"
        ).pack(padx=10, pady=10, anchor="w")
    
    def _update_hotkey_preview(self):
        """Update hotkey preview."""
        parts = []
        for name, var in self.modifier_vars.items():
            if var.get():
                parts.append(name)
        
        key = self.key_entry.get().strip().lower()
        if key:
            parts.append(key)
        
        hotkey = "+".join(parts) if parts else "add a main key..."
        self.hotkey_preview_label.configure(text=hotkey)
    
    # ========================================================================
    # STEP 3: PREVIEW & CONFIRM
    # ========================================================================
    
    def _show_step_preview(self):
        """Step 3: Preview en bevestigen."""
        # Save step 2 values
        if self.hotkey_type_var.get() == "media":
            self.selected_hotkey = self.media_var.get()
            self.selected_hotkey_type = 'media'
        else:
            parts = []
            for name, var in self.modifier_vars.items():
                if var.get():
                    parts.append(name)
            
            key = self.key_entry.get().strip().lower()
            if key:
                parts.append(key)
            
            self.selected_hotkey = "+".join(parts)
            self.selected_hotkey_type = 'custom'
        
        # Scrollable container
        scroll_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color="transparent"
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Success message
        ctk.CTkLabel(
            scroll_frame,
            text="✅ Configuration Complete!",
            font=("Roboto", 20, "bold"),
            text_color=("green", "lightgreen")
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(
            scroll_frame,
            text="Review your button configuration below:",
            font=("Roboto", 13),
            text_color="gray"
        ).pack(pady=(0, 20))
        
        # Large button preview
        preview_container = ctk.CTkFrame(
            scroll_frame,
            fg_color=("gray85", "gray20"),
            corner_radius=15
        )
        preview_container.pack(pady=(0, 20))
        
        # Mock button (groot!)
        mock_button = ctk.CTkFrame(
            preview_container,
            width=280,
            height=280,
            corner_radius=20,
            fg_color=(COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK),
            border_width=4,
            border_color="green"
        )
        mock_button.pack(padx=30, pady=30)
        mock_button.pack_propagate(False)
        
        # Button number badge
        num_badge = ctk.CTkLabel(
            mock_button,
            text=f"#{self.button_index + 1}",
            font=("Roboto", 18, "bold"),
            fg_color=("gray70", "gray30"),
            corner_radius=10,
            width=60,
            height=40
        )
        num_badge.place(x=12, y=12)
        
        # Icon (groot!)
        ctk.CTkLabel(
            mock_button,
            text=self.selected_icon,
            font=("Segoe UI Emoji", 70)
        ).place(relx=0.5, rely=0.38, anchor="center")
        
        # Label
        ctk.CTkLabel(
            mock_button,
            text=self.selected_label,
            font=("Roboto", 14, "bold"),
            wraplength=240
        ).place(relx=0.5, rely=0.68, anchor="center")
        
        # Hotkey
        ctk.CTkLabel(
            mock_button,
            text=self.selected_hotkey[:28] if self.selected_hotkey else "",
            font=("Courier", 11, "bold"),
            fg_color=("gray70", "gray30"),
            corner_radius=6,
            height=32,
            width=240
        ).place(relx=0.5, rely=0.88, anchor="center")
        
        # Details below preview
        details_frame = ctk.CTkFrame(
            scroll_frame,
            fg_color=("gray85", "gray20"),
            corner_radius=10
        )
        details_frame.pack(fill="x")
        
        ctk.CTkLabel(
            details_frame,
            text="📋 Configuration Summary",
            font=("Roboto", 16, "bold")
        ).pack(pady=(15, 10))
        
        # Details grid
        details = [
            ("Button:", f"#{self.button_index + 1}"),
            ("Mode:", f"Mode {self.mode + 1}"),
            ("Icon:", self.selected_icon),
            ("Label:", self.selected_label),
            ("Hotkey:", self.selected_hotkey),
            ("Type:", "Media Control" if self.selected_hotkey_type == 'media' else "Custom Shortcut")
        ]
        
        for label, value in details:
            row = ctk.CTkFrame(details_frame, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)
            
            ctk.CTkLabel(
                row,
                text=label,
                font=("Roboto", 12, "bold"),
                width=100,
                anchor="w"
            ).pack(side="left")
            
            ctk.CTkLabel(
                row,
                text=value,
                font=("Roboto", 12),
                anchor="w"
            ).pack(side="left", fill="x", expand=True)
        
        ctk.CTkFrame(details_frame, height=15, fg_color="transparent").pack()
        
        # Optional: Clear button
        if self.current_config and self.on_clear:
            ctk.CTkFrame(scroll_frame, height=10, fg_color="transparent").pack()
            
            clear_btn = ctk.CTkButton(
                scroll_frame,
                text="🗑️ Clear This Button",
                command=self._handle_clear,
                height=50,
                font=("Roboto", 13, "bold"),
                fg_color="red",
                hover_color="darkred"
            )
            clear_btn.pack(fill="x")
    
    # ========================================================================
    # NAVIGATION
    # ========================================================================
    
    def _go_back(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self._show_step(self.current_step)
    
    def _go_next(self):
        """Go to next step or save."""
        if self.current_step == self.total_steps - 1:
            # Last step - save
            self._handle_save()
        else:
            # Validate current step
            if self.current_step == 0:
                # Step 1: Icon & label
                icon = self.icon_entry.get().strip()
                label = self.label_entry.get().strip()
                
                if not icon:
                    self._show_error("❌ Please choose an icon!")
                    return
                
                if not label:
                    self._show_error("❌ Please enter a label!")
                    return
            
            elif self.current_step == 1:
                # Step 2: Hotkey
                if self.hotkey_type_var.get() == "media":
                    if not self.media_var.get():
                        self._show_error("❌ Please select a media control!")
                        return
                else:
                    key = self.key_entry.get().strip()
                    if not key:
                        self._show_error("❌ Please enter a main key!")
                        return
            
            # Go to next step
            self.current_step += 1
            self._show_step(self.current_step)
    
    def _handle_save(self):
        """Save configuration."""
        new_config = {
            'icon': self.selected_icon,
            'label': self.selected_label,
            'hotkey': self.selected_hotkey
        }
        
        if self.on_save:
            self.on_save(new_config)
        
        self._show_success("✅ Configuration saved!")
        self.dialog.after(600, self.dialog.destroy)
    
    def _handle_clear(self):
        """Clear button configuration."""
        if self.on_clear:
            self.on_clear()
        self.dialog.destroy()
    
    def _show_error(self, message: str):
        """Show error message."""
        error = ctk.CTkLabel(
            self.dialog,
            text=message,
            font=("Roboto", 16, "bold"),
            text_color="white",
            fg_color="red",
            corner_radius=10,
            height=60,
            width=350
        )
        error.place(relx=0.5, rely=0.5, anchor="center")
        self.dialog.after(2000, error.destroy)
    
    def _show_success(self, message: str):
        """Show success message."""
        success = ctk.CTkLabel(
            self.dialog,
            text=message,
            font=("Roboto", 16, "bold"),
            text_color="white",
            fg_color="green",
            corner_radius=10,
            height=60,
            width=350
        )
        success.place(relx=0.5, rely=0.5, anchor="center")


# ============================================================================
# SERIAL PORT DIALOG (unchanged from original)
# ============================================================================

class SerialPortDialog:
    """Dialog voor het selecteren van een seriële poort."""
    
    def __init__(
        self,
        parent: ctk.CTk,
        ports: List[Tuple[str, str]],
        on_connect: Callable[[str], None]
    ):
        """Initialiseer de serial port dialog."""
        self.ports = ports
        self.on_connect = on_connect
        
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Select Device")
        self.dialog.geometry("450x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        ctk.CTkLabel(
            self.dialog,
            text="🔌 Select Serial Port:",
            font=("Roboto", 18, "bold")
        ).pack(pady=20)
        
        self.port_var = ctk.StringVar(value=ports[0][0] if ports else "")
        
        for device, description in ports:
            ctk.CTkRadioButton(
                self.dialog,
                text=f"{device} - {description}",
                variable=self.port_var,
                value=device,
                font=("Roboto", 12)
            ).pack(pady=8, padx=20, anchor="w")
        
        ctk.CTkButton(
            self.dialog,
            text="Connect",
            command=self._handle_connect,
            height=50,
            font=("Roboto", 14, "bold")
        ).pack(pady=30)
    
    def _handle_connect(self) -> None:
        """Handle connect."""
        selected_port = self.port_var.get()
        if selected_port and self.on_connect:
            self.on_connect(selected_port)
        self.dialog.destroy()
