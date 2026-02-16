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
        is_master_volume: bool = False,
        slider_name: str = None
    ):
        """
        Initialiseer een nieuwe slider widget.
        
        Args:
            parent: Parent frame waar de slider in komt
            index: Slider nummer (0-3: 0-2 voor apps, 3 voor master)
            available_apps: List van beschikbare app namen (leeg voor master)
            on_app_change: Callback (slider_index, app_list) bij wijziging
            is_master_volume: True als dit de master volume slider is
            slider_name: Custom naam voor de slider (optioneel)
        """
        self.index = index
        self.on_app_change = on_app_change
        self.is_master_volume = is_master_volume
        self.assigned_apps = []
        
        # Sla slider naam op
        if slider_name:
            self.slider_name = slider_name
        elif is_master_volume:
            self.slider_name = "Master Volume"
        else:
            self.slider_name = f"Slider {index + 1}"
        
        # Maak container frame met subtiele gradient
        self.frame = ctk.CTkFrame(
            parent,
            corner_radius=15,
            fg_color=(COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK),
            border_width=2,
            border_color=("gray75", "gray30")  # Subtiele border
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
        
        # Icon + Title links (klikbaar voor rename)
        self.header_label = ctk.CTkLabel(
            header_row,
            text=f"{self.slider_name}",
            font=("Roboto", 16, "bold"),
            text_color="orange",
            cursor="hand2"
        )
        self.header_label.pack(side="left")
        
        # Bind right-click voor rename
        self.header_label.bind("<Button-3>", lambda e: self._show_rename_dialog())
        
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
        
        # Progress bar onder header (full width, mooier gestyled)
        self.progress_bar = ctk.CTkProgressBar(
            self.frame,
            height=12,
            corner_radius=6,
            progress_color="#3B82F6",  # Zelfde blauwe accent
            fg_color=("gray85", "gray20")
        )
        self.progress_bar.set(0.5)
        self.progress_bar.pack(pady=(5, 10), padx=15, fill="x")
        
        # Dummy vars voor compatibiliteit
        self.apps_container = None
        self.empty_label = None
        self.available_apps = []
        self.app_var = None
        self.app_menu = None
    
    def _create_app_slider_layout(self, available_apps: List[str]):
        """Maak compacte app slider layout - horizontaal."""
        # Header (klikbaar voor rename)
        self.header_label = ctk.CTkLabel(
            self.frame,
            text=f"{self.slider_name}",
            font=("Roboto", 16, "bold"),
            cursor="hand2"
        )
        self.header_label.pack(pady=(12, 8))
        
        # Bind right-click voor rename
        self.header_label.bind("<Button-3>", lambda e: self._show_rename_dialog())
        
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
        
        # Maak menu options met display namen
        menu_options = ["Selecteer..."] + [self._get_app_display_name(app) for app in available_apps]
        
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
            height=10,
            corner_radius=5,
            progress_color="#3B82F6",  # Moderne blauwe accent
            fg_color=("gray85", "gray20")
        )
        self.progress_bar.set(0.5)
        self.progress_bar.pack(pady=5)
    
    def _handle_app_select(self, selected_display_name: str):
        """Handle app selectie uit dropdown."""
        if selected_display_name == "Selecteer...":
            return
        
        # Vertaal display naam terug naar originele app naam
        app_name = None
        for original in self.available_apps:
            if self._get_app_display_name(original) == selected_display_name:
                app_name = original
                break
        
        if app_name is None:
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
        
        # Haal display naam op
        display_name = self._get_app_display_name(app_name)
        
        # App tag frame (compact)
        tag_frame = ctk.CTkFrame(
            self.apps_container,
            fg_color=("gray80", "gray25"),
            corner_radius=5,
            height=30
        )
        tag_frame.pack(fill="x", pady=2, padx=3)
        tag_frame.pack_propagate(False)
        
        # App name label (klikbaar voor rename)
        app_label = ctk.CTkLabel(
            tag_frame,
            text=display_name,
            font=("Roboto", 12),
            anchor="w",
            cursor="hand2"
        )
        app_label.pack(side="left", padx=8, fill="x", expand=True)
        
        # Bind right-click voor rename
        app_label.bind("<Button-3>", lambda e: self._show_app_rename_dialog(app_name, app_label))
        
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
        """Update de visuele volume weergave met smooth animation."""
        volume = max(0.0, min(1.0, volume))
        
        # Cancel any ongoing animation
        if hasattr(self, '_animation_id') and self._animation_id:
            try:
                self.frame.after_cancel(self._animation_id)
            except:
                pass
            self._animation_id = None
        
        # Direct set voor snelle respons
        self.progress_bar.set(volume)
        
        # Update percentage label
        percentage = int(volume * 100)
        self.volume_label.configure(text=f"{percentage}%")
    
    def update_available_apps(self, apps: List[str]):
        """Update de lijst van beschikbare apps in de dropdown."""
        if self.is_master_volume or self.app_menu is None:
            return
        
        self.available_apps = apps
        # Gebruik display namen in dropdown
        menu_options = ["Selecteer..."] + [self._get_app_display_name(app) for app in apps]
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
    
    def _show_rename_dialog(self):
        """Toon dialog om slider naam te wijzigen."""
        # Import hier om circular import te voorkomen
        import customtkinter as ctk
        
        # Maak dialog window
        dialog = ctk.CTkToplevel()
        dialog.title(f"Rename {self.slider_name}")
        dialog.geometry("450x220")
        dialog.grab_set()
        
        # Center on screen
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (220 // 2)
        dialog.geometry(f"450x220+{x}+{y}")
        
        ctk.CTkLabel(
            dialog,
            text=f"✏️ Rename {self.slider_name}",
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
            placeholder_text="e.g. Gaming Audio, Music, Discord...",
            font=("Roboto", 14)
        )
        name_entry.insert(0, self.slider_name)
        name_entry.pack(pady=10)
        name_entry.focus()
        
        # Select all text
        name_entry.select_range(0, 'end')
        
        def save_name():
            new_name = name_entry.get().strip()
            if new_name and len(new_name) <= 30:
                self.slider_name = new_name
                self.header_label.configure(text=new_name)
                
                # Callback naar main window om op te slaan
                if hasattr(self, 'on_rename_callback') and self.on_rename_callback:
                    self.on_rename_callback(self.index, new_name)
                
                dialog.destroy()
            elif len(new_name) > 30:
                error_label = ctk.CTkLabel(
                    dialog,
                    text="❌ Naam te lang! (max 30 karakters)",
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
    
    def set_rename_callback(self, callback: Callable[[int, str], None]):
        """Stel callback in voor rename event."""
        self.on_rename_callback = callback
    
    def _show_app_rename_dialog(self, original_app_name: str, label_widget):
        """Toon dialog om app display naam te wijzigen."""
        import customtkinter as ctk
        
        # Haal huidige display naam op (of gebruik origineel)
        current_display = self._get_app_display_name(original_app_name)
        
        # Maak dialog
        dialog = ctk.CTkToplevel()
        dialog.title(f"Rename {original_app_name}")
        dialog.geometry("450x240")
        dialog.grab_set()
        
        # Center on screen
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (240 // 2)
        dialog.geometry(f"450x240+{x}+{y}")
        
        ctk.CTkLabel(
            dialog,
            text=f"✏️ Rename App",
            font=("Roboto", 20, "bold")
        ).pack(pady=15)
        
        ctk.CTkLabel(
            dialog,
            text=f"Original: {original_app_name}",
            font=("Roboto", 11),
            text_color="gray"
        ).pack(pady=(0, 5))
        
        ctk.CTkLabel(
            dialog,
            text="Display name:",
            font=("Roboto", 12),
            text_color="gray"
        ).pack(pady=(0, 5))
        
        # Name entry
        name_entry = ctk.CTkEntry(
            dialog,
            width=350,
            height=45,
            placeholder_text="e.g. Guild Wars 2, Discord, Spotify...",
            font=("Roboto", 14)
        )
        name_entry.insert(0, current_display)
        name_entry.pack(pady=10)
        name_entry.focus()
        name_entry.select_range(0, 'end')
        
        def save_name():
            new_name = name_entry.get().strip()
            if new_name and len(new_name) <= 40:
                # Sla mapping op
                self._set_app_display_name(original_app_name, new_name)
                
                # Update label
                label_widget.configure(text=new_name)
                
                # Callback naar main window om mapping op te slaan
                if hasattr(self, 'on_app_rename_callback') and self.on_app_rename_callback:
                    self.on_app_rename_callback(original_app_name, new_name)
                
                dialog.destroy()
            elif len(new_name) > 40:
                error_label = ctk.CTkLabel(
                    dialog,
                    text="❌ Naam te lang! (max 40 karakters)",
                    font=("Roboto", 11, "bold"),
                    text_color="red"
                )
                error_label.pack(pady=5)
                dialog.after(2000, error_label.destroy)
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            width=130,
            height=40,
            font=("Roboto", 13)
        ).pack(side="left", padx=10)
        
        # Reset button
        def reset_name():
            name_entry.delete(0, 'end')
            name_entry.insert(0, original_app_name)
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 Reset",
            command=reset_name,
            width=130,
            height=40,
            font=("Roboto", 13),
            fg_color="orange",
            hover_color="darkorange"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Save",
            command=save_name,
            width=130,
            height=40,
            font=("Roboto", 13, "bold"),
            fg_color="green",
            hover_color="darkgreen"
        ).pack(side="right", padx=10)
        
        # Enter key to save
        name_entry.bind("<Return>", lambda e: save_name())
    
    def set_app_rename_callback(self, callback: Callable[[str, str], None]):
        """Stel callback in voor app rename event."""
        self.on_app_rename_callback = callback
    
    def _get_app_display_name(self, original_name: str) -> str:
        """Haal display naam op voor een app (of origineel als geen mapping)."""
        if not hasattr(self, 'app_name_mapping'):
            self.app_name_mapping = {}
        return self.app_name_mapping.get(original_name, original_name)
    
    def _set_app_display_name(self, original_name: str, display_name: str):
        """Stel display naam in voor een app."""
        if not hasattr(self, 'app_name_mapping'):
            self.app_name_mapping = {}
        self.app_name_mapping[original_name] = display_name
    
    def set_app_name_mappings(self, mappings: dict):
        """Stel alle app naam mappings in (bij laden config)."""
        self.app_name_mapping = mappings.copy()
        
        # Update dropdown menu als die bestaat
        if self.app_menu is not None and hasattr(self, 'available_apps'):
            menu_options = ["Selecteer..."] + [self._get_app_display_name(app) for app in self.available_apps]
            self.app_menu.configure(values=menu_options)
        
        # Update alle bestaande labels
        if self.apps_container and not self.is_master_volume:
            for widget in self.apps_container.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    # Dit is een tag frame
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkLabel):
                            # Dit is de app naam label
                            current_text = child.cget("text")
                            # Check of dit een originele app naam is
                            if current_text in mappings:
                                child.configure(text=mappings[current_text])
                            break
