"""
Slider Widget Component - Drag & Drop Version

Apps slepen vanuit de app pool naar een slider, of tussen sliders onderling.
Geen dropdown menu's meer nodig.

File: slider_widget.py
"""

import sys
from pathlib import Path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

import tkinter as tk
import customtkinter as ctk
from typing import Callable, List, Optional

from constants import (
    COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK,
    COLOR_BUTTON_HOVER_LIGHT, COLOR_BUTTON_HOVER_DARK
)

# ============================================================================
# Globale drag-state (gedeeld tussen alle SliderWidgets en de AppPool)
# ============================================================================

class _DragState:
    """Singleton die bijhoudt welke app er gesleept wordt en waar vandaan."""
    app_name: Optional[str] = None          # bijv. "Discord.exe"
    source_slider: Optional[object] = None  # SliderWidget of None (= pool)
    ghost_label: Optional[tk.Label] = None  # zwevend label tijdens drag

_drag = _DragState()


# ============================================================================
# AppPool  – gedeeld paneel met alle beschikbare apps (boven de sliders)
# ============================================================================

class AppPool:
    """
    Paneel met alle beschikbare audio-apps als sleepbare pills.

    Apps die al aan een slider toegewezen zijn worden grijs/doorzichtig
    weergegeven zodat de gebruiker ziet dat ze 'in gebruik' zijn (maar nog
    steeds versleept kunnen worden naar een andere slider).

    Args:
        parent:          CTk-parent widget
        available_apps:  lijst van app-namen (bijv. ["Discord.exe", ...])
        slider_widgets:  lijst van SliderWidget-instanties (wordt later ingevuld
                         via set_sliders())
    """

    PILL_BG_IDLE   = ("#dce8fb", "#1e3a5f")   # lichtblauw / donkerblauw
    PILL_BG_USED   = ("#d0d0d0", "#3a3a3a")   # grijs = al in gebruik
    PILL_FG        = ("#1a1a1a", "#e8e8e8")

    def __init__(self, parent: ctk.CTkFrame, available_apps: List[str]):
        self.available_apps = list(available_apps)
        self._sliders: List["SliderWidget"] = []
        self._pills: dict[str, ctk.CTkFrame] = {}   # app_name -> frame

        # Outer card
        self.frame = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=(COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK),
            border_width=2,
            border_color=("gray75", "gray30")
        )
        # Geen pack() hier — parent (main_window) plaatst dit frame via grid

        # Titel
        ctk.CTkLabel(
            self.frame,
            text="🎧  Beschikbare apps  —  sleep naar een slider",
            font=("Roboto", 12, "bold"),
            anchor="w"
        ).pack(padx=12, pady=(8, 4), anchor="w")

        # Scrollable rij met pills
        self._pill_container = ctk.CTkScrollableFrame(
            self.frame,
            height=44,
            fg_color=("gray88", "gray18"),
            orientation="horizontal"
        )
        self._pill_container.pack(fill="x", padx=10, pady=(0, 8))

        self._empty_label = ctk.CTkLabel(
            self._pill_container,
            text="Geen audio-apps gevonden",
            text_color="gray",
            font=("Roboto", 11)
        )
        self._empty_label.pack(pady=12)

        self._build_pills()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_sliders(self, sliders: List["SliderWidget"]):
        """Koppel de slider-instanties zodat de pool weet wat 'in gebruik' is."""
        self._sliders = sliders

    def update_available_apps(self, apps: List[str]):
        """Vervang de app-lijst en herbouw alle pills."""
        self.available_apps = list(apps)
        self._build_pills()

    def refresh_used_state(self):
        """Grijst pills in die al aan een slider zijn toegewezen."""
        used = set()
        for sl in self._sliders:
            if not sl.is_master_volume:
                used.update(sl.assigned_apps)

        mode = ctk.get_appearance_mode()
        idx = 0 if mode == "Light" else 1

        for app, pill in self._pills.items():
            if app in used:
                pill.configure(fg_color=self.PILL_BG_USED[idx])
                for child in pill.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        child.configure(text_color="gray")
            else:
                pill.configure(fg_color=self.PILL_BG_IDLE[idx])
                for child in pill.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        child.configure(text_color=self.PILL_FG[idx])

    # ------------------------------------------------------------------
    # Intern
    # ------------------------------------------------------------------

    def _build_pills(self):
        """(Her)bouw alle app-pills in de container."""
        for w in self._pill_container.winfo_children():
            w.destroy()
        self._pills.clear()

        if not self.available_apps:
            self._empty_label = ctk.CTkLabel(
                self._pill_container,
                text="Geen audio-apps gevonden",
                text_color="gray",
                font=("Roboto", 11)
            )
            self._empty_label.pack(pady=12)
            return

        for app in self.available_apps:
            self._create_pill(app)

        self.refresh_used_state()

    def _create_pill(self, app_name: str):
        """Maak één sleepbare pill voor een app."""
        mode = ctk.get_appearance_mode()
        idx = 0 if mode == "Light" else 1

        pill = ctk.CTkFrame(
            self._pill_container,
            corner_radius=20,
            fg_color=self.PILL_BG_IDLE[idx],
            height=34
        )
        pill.pack(side="left", padx=4, pady=6)

        lbl = ctk.CTkLabel(
            pill,
            text=app_name,
            font=("Roboto", 12),
            text_color=self.PILL_FG[idx],
            cursor="hand2"
        )
        lbl.pack(padx=12, pady=4)

        self._pills[app_name] = pill

        # Bind drag events op zowel pill als label
        for widget in (pill, lbl):
            widget.bind("<ButtonPress-1>",   lambda e, a=app_name: self._on_drag_start(e, a))
            widget.bind("<B1-Motion>",        self._on_drag_motion)
            widget.bind("<ButtonRelease-1>",  self._on_drag_end)

    def _on_drag_start(self, event, app_name: str):
        _drag.app_name = app_name
        _drag.source_slider = None          # komt uit de pool, niet uit een slider

        root = event.widget.winfo_toplevel()
        _drag.ghost_label = tk.Label(
            root,
            text=f"  {app_name}  ",
            bg="#3B82F6",
            fg="white",
            font=("Roboto", 11, "bold"),
            relief="flat",
            bd=0,
            padx=6, pady=3
        )
        _drag.ghost_label.place(x=event.x_root - root.winfo_rootx(),
                                y=event.y_root - root.winfo_rooty())

        # Highlight alle drop-zones
        for sl in self._sliders:
            if not sl.is_master_volume:
                sl._set_drop_highlight(True)

    def _on_drag_motion(self, event):
        if _drag.ghost_label:
            root = event.widget.winfo_toplevel()
            _drag.ghost_label.place(x=event.x_root - root.winfo_rootx() + 8,
                                    y=event.y_root - root.winfo_rooty() + 8)

    def _on_drag_end(self, event):
        if _drag.ghost_label:
            _drag.ghost_label.destroy()
            _drag.ghost_label = None

        # Verwijder highlights
        for sl in self._sliders:
            if not sl.is_master_volume:
                sl._set_drop_highlight(False)

        # ── Hit-test: welke slider zit onder de muis? ──
        # Tkinter stuurt ButtonRelease altijd naar het widget dat de drag begon,
        # dus we moeten zelf uitzoeken waar de cursor nu is.
        app = _drag.app_name
        source = _drag.source_slider

        if app:
            rx, ry = event.x_root, event.y_root
            target = None
            for sl in self._sliders:
                if sl.is_master_volume:
                    continue
                try:
                    fx = sl.apps_container.winfo_rootx()
                    fy = sl.apps_container.winfo_rooty()
                    fw = sl.apps_container.winfo_width()
                    fh = sl.apps_container.winfo_height()
                    # Vergroot het trefgebied met de volledige slider-card
                    fx2 = sl.frame.winfo_rootx()
                    fy2 = sl.frame.winfo_rooty()
                    fw2 = sl.frame.winfo_width()
                    fh2 = sl.frame.winfo_height()
                    if fx2 <= rx <= fx2 + fw2 and fy2 <= ry <= fy2 + fh2:
                        target = sl
                        break
                except Exception:
                    pass

            if target is not None and app not in target.assigned_apps:
                if source is not None and source is not target:
                    source._internal_remove(app)
                target.assigned_apps.append(app)
                target._create_app_tag(app)
                target._notify()

        _drag.app_name = None
        _drag.source_slider = None
        self.refresh_used_state()


# ============================================================================
# SliderWidget
# ============================================================================

class SliderWidget:
    """
    Audio slider widget met drag-and-drop ondersteuning.

    Apps kunnen gesleept worden:
      - Van de AppPool  → naar deze slider (toevoegen)
      - Van deze slider → naar een andere slider (verplaatsen)
      - Van deze slider → terug naar de AppPool (verwijderen)

    Master-volume slider heeft geen app-lijst en is niet als drop-zone bruikbaar.
    """

    # Kleur voor drop-zone highlight
    _DROP_BORDER = "#3B82F6"
    _NORMAL_BORDER = ("gray75", "gray30")

    def __init__(
        self,
        parent: ctk.CTkFrame,
        index: int,
        available_apps: List[str],
        on_app_change: Callable[[int, List[str]], None],
        is_master_volume: bool = False,
        slider_name: str = None
    ):
        self.index = index
        self.on_app_change = on_app_change
        self.is_master_volume = is_master_volume
        self.assigned_apps: List[str] = []
        self.available_apps = list(available_apps)
        self._app_pool: Optional[AppPool] = None   # wordt ingesteld via set_pool()

        # Initialiseer alle widget-attributen zodat callbacks veilig zijn
        # ongeacht of ze vóór of na de layout-opbouw worden aangeroepen
        self.apps_container = None
        self.empty_label = None
        self.app_menu = None
        self.app_var = None
        self.progress_bar = None
        self.volume_label = None
        self.header_label = None
        self.on_rename_callback = None
        self.on_app_rename_callback = None

        self.slider_name = (
            slider_name if slider_name
            else ("Master Volume" if is_master_volume else f"Slider {index + 1}")
        )

        # Naam-mapping (origineel → display)
        self.app_name_mapping: dict = {}

        # Outer card
        self.frame = ctk.CTkFrame(
            parent,
            corner_radius=15,
            fg_color=(COLOR_BUTTON_NORMAL_LIGHT, COLOR_BUTTON_NORMAL_DARK),
            border_width=2,
            border_color=self._NORMAL_BORDER
        )
        # Geen pack() hier — main_window plaatst dit frame via grid

        if is_master_volume:
            self._create_master_volume_layout()
        else:
            self._create_app_slider_layout()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_pool(self, pool: AppPool):
        """Koppel de AppPool zodat de slider de pool kan verversen."""
        self._app_pool = pool

    def update_available_apps(self, apps: List[str]):
        """Update de lijst van bekende apps (voor naam-lookups)."""
        self.available_apps = list(apps)

    def get_assigned_apps(self) -> List[str]:
        return self.assigned_apps.copy()

    def set_assigned_apps(self, apps: List[str]):
        """Stel de app-lijst in (bij laden config)."""
        if self.is_master_volume or self.apps_container is None:
            return
        for w in self.apps_container.winfo_children():
            w.destroy()
        self.empty_label = None
        self.assigned_apps = list(apps)
        if apps:
            for app in apps:
                self._create_app_tag(app)
        else:
            self._show_empty_state()

    def update_volume_display(self, volume: float):
        volume = max(0.0, min(1.0, volume))
        if hasattr(self, '_animation_id') and self._animation_id:
            try:
                self.frame.after_cancel(self._animation_id)
            except Exception:
                pass
            self._animation_id = None
        self.progress_bar.set(volume)
        self.volume_label.configure(text=f"{int(volume * 100)}%")

    def get_frame(self) -> ctk.CTkFrame:
        return self.frame

    def set_rename_callback(self, callback: Callable[[int, str], None]):
        self.on_rename_callback = callback

    def set_app_rename_callback(self, callback: Callable[[str, str], None]):
        self.on_app_rename_callback = callback

    def set_app_name_mappings(self, mappings: dict):
        self.app_name_mapping = mappings.copy()
        # Update bestaande tags
        if self.apps_container and not self.is_master_volume:
            for widget in self.apps_container.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkLabel):
                            txt = child.cget("text")
                            if txt in mappings:
                                child.configure(text=mappings[txt])
                            break

    # ------------------------------------------------------------------
    # Drag & drop (drop-zone kant)
    # ------------------------------------------------------------------

    def _set_drop_highlight(self, active: bool):
        """Geef visuele feedback dat dit een geldige drop-zone is."""
        if active:
            self.frame.configure(border_color=self._DROP_BORDER, border_width=3)
        else:
            self.frame.configure(border_color=self._NORMAL_BORDER, border_width=2)

    # ------------------------------------------------------------------
    # Drag starten vanuit een bestaande tag (verplaatsen)
    # ------------------------------------------------------------------

    def _start_tag_drag(self, event, app_name: str, tag_frame: ctk.CTkFrame):
        """Start een drag vanuit een bestaande app-tag."""
        _drag.app_name = app_name
        _drag.source_slider = self

        root = event.widget.winfo_toplevel()
        _drag.ghost_label = tk.Label(
            root,
            text=f"  {self._get_app_display_name(app_name)}  ",
            bg="#3B82F6",
            fg="white",
            font=("Roboto", 11, "bold"),
            relief="flat",
            bd=0,
            padx=6, pady=3
        )
        _drag.ghost_label.place(x=event.x_root - root.winfo_rootx(),
                                y=event.y_root - root.winfo_rooty())

        # Highlight alle andere sliders als drop-zone
        if self._app_pool:
            for sl in self._app_pool._sliders:
                if sl is not self and not sl.is_master_volume:
                    sl._set_drop_highlight(True)

    def _tag_drag_motion(self, event):
        if _drag.ghost_label:
            root = event.widget.winfo_toplevel()
            _drag.ghost_label.place(x=event.x_root - root.winfo_rootx() + 8,
                                    y=event.y_root - root.winfo_rooty() + 8)

    def _tag_drag_end(self, event, app_name: str, tag_frame: ctk.CTkFrame):
        """Verwerk het loslaten van een tag-drag."""
        if _drag.ghost_label:
            _drag.ghost_label.destroy()
            _drag.ghost_label = None

        # Verwijder highlights
        if self._app_pool:
            for sl in self._app_pool._sliders:
                sl._set_drop_highlight(False)

        # ── Hit-test: welke slider zit onder de muis? ──
        app = _drag.app_name
        source = _drag.source_slider  # == self

        if app and self._app_pool:
            rx, ry = event.x_root, event.y_root
            target = None
            for sl in self._app_pool._sliders:
                if sl.is_master_volume or sl is self:
                    continue
                try:
                    fx2 = sl.frame.winfo_rootx()
                    fy2 = sl.frame.winfo_rooty()
                    fw2 = sl.frame.winfo_width()
                    fh2 = sl.frame.winfo_height()
                    if fx2 <= rx <= fx2 + fw2 and fy2 <= ry <= fy2 + fh2:
                        target = sl
                        break
                except Exception:
                    pass

            if target is not None and app not in target.assigned_apps:
                # Verplaatsen naar andere slider
                self._internal_remove(app)
                target.assigned_apps.append(app)
                target._create_app_tag(app)
                target._notify()
            # Als target is None: app blijft in dezelfde slider (drop buiten alles)

        _drag.app_name = None
        _drag.source_slider = None

        if self._app_pool:
            self._app_pool.refresh_used_state()

    # ------------------------------------------------------------------
    # Intern helpers
    # ------------------------------------------------------------------

    def _internal_remove(self, app_name: str):
        """Verwijder app intern (aangeroepen door doel-slider na drop)."""
        if app_name not in self.assigned_apps:
            return
        self.assigned_apps.remove(app_name)
        # Verwijder de bijbehorende tag widget
        if self.apps_container:
            for widget in self.apps_container.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    # Identificeer via opgeslagen metadata
                    stored = getattr(widget, "_app_name", None)
                    if stored == app_name:
                        widget.destroy()
                        break
        self._update_empty_state()
        self._notify()

    def _notify(self):
        if self.on_app_change:
            self.on_app_change(self.index, self.assigned_apps)

    def _get_app_display_name(self, original: str) -> str:
        return self.app_name_mapping.get(original, original)

    def _set_app_display_name(self, original: str, display: str):
        self.app_name_mapping[original] = display

    # ------------------------------------------------------------------
    # Layout: master volume
    # ------------------------------------------------------------------

    def _create_master_volume_layout(self):
        self.frame.columnconfigure(0, weight=1)

        header_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))

        self.header_label = ctk.CTkLabel(
            header_row,
            text=self.slider_name,
            font=("Roboto", 17, "bold"),
            text_color="orange",
            cursor="hand2"
        )
        self.header_label.pack(side="left")
        self.header_label.bind("<Button-3>", lambda e: self._show_rename_dialog())

        self.volume_label = ctk.CTkLabel(
            header_row,
            text="50%",
            font=("Roboto", 16, "bold"),
            text_color="orange"
        )
        self.volume_label.pack(side="right")

        ctk.CTkLabel(
            header_row,
            text="Volume:",
            font=("Roboto", 13),
            text_color="gray"
        ).pack(side="right", padx=(0, 5))

        self.progress_bar = ctk.CTkProgressBar(
            self.frame,
            height=12,
            corner_radius=6,
            progress_color="#3B82F6",
            fg_color=("gray85", "gray20")
        )
        self.progress_bar.set(0.5)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))

    # ------------------------------------------------------------------
    # Layout: app slider (met drop-zone)
    # ------------------------------------------------------------------

    def _create_app_slider_layout(self):
        # Het frame zelf gebruikt grid zodat de apps_container kan groeien
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)   # rij 2 = apps_container

        # Rij 0: Header + volume in één lijn
        top_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))

        self.header_label = ctk.CTkLabel(
            top_row,
            text=self.slider_name,
            font=("Roboto", 17, "bold"),
            cursor="hand2"
        )
        self.header_label.pack(side="left")
        self.header_label.bind("<Button-3>", lambda e: self._show_rename_dialog())

        self.volume_label = ctk.CTkLabel(
            top_row,
            text="50%",
            font=("Roboto", 16, "bold")
        )
        self.volume_label.pack(side="right")

        ctk.CTkLabel(
            top_row,
            text="Volume:",
            font=("Roboto", 13),
            text_color="gray"
        ).pack(side="right", padx=(0, 5))

        # Rij 1: Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.frame,
            height=10,
            corner_radius=5,
            progress_color="#3B82F6",
            fg_color=("gray85", "gray20")
        )
        self.progress_bar.set(0.5)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))

        # Rij 2: Drop-zone — groeit mee met venster (weight=1)
        # padx en pady zorgen dat de container NIET tegen de randen zit
        self.apps_container = ctk.CTkFrame(
            self.frame,
            fg_color=("gray83", "gray22"),
            corner_radius=10
        )
        self.apps_container.grid(row=2, column=0, sticky="nsew", padx=16, pady=(6, 14))

        self.empty_label = None
        self._show_empty_state()

    # ------------------------------------------------------------------
    # App-tag aanmaken
    # ------------------------------------------------------------------

    def _create_app_tag(self, app_name: str):
        if self.is_master_volume or self.apps_container is None:
            return

        # Verberg empty state
        self._hide_empty_state()

        display = self._get_app_display_name(app_name)

        tag_frame = ctk.CTkFrame(
            self.apps_container,
            fg_color=("gray74", "gray30"),
            corner_radius=8,
            height=36
        )
        tag_frame.pack(fill="x", pady=3, padx=6)
        tag_frame.pack_propagate(False)

        # Sla app-naam op als attribuut voor identificatie bij drag
        tag_frame._app_name = app_name

        # Grip-icoon (visuele hint dat je kunt slepen)
        grip = ctk.CTkLabel(
            tag_frame,
            text="⠿",
            font=("Roboto", 14),
            text_color="gray",
            cursor="fleur",
            width=22
        )
        grip.pack(side="left", padx=(8, 2))

        # App-naam label (rechtsclick = rename)
        app_label = ctk.CTkLabel(
            tag_frame,
            text=display,
            font=("Roboto", 13),
            anchor="w",
            cursor="fleur"
        )
        app_label.pack(side="left", fill="x", expand=True, padx=4)
        app_label.bind("<Button-3>",
                       lambda e: self._show_app_rename_dialog(app_name, app_label))

        # Remove-knop
        remove_btn = ctk.CTkButton(
            tag_frame,
            text="✕",
            width=28, height=28,
            fg_color="red",
            hover_color="darkred",
            font=("Roboto", 12, "bold"),
            command=lambda: self._remove_app(app_name, tag_frame)
        )
        remove_btn.pack(side="right", padx=5, pady=4)

        # Bind drag-events op grip en label
        for widget in (grip, app_label, tag_frame):
            widget.bind("<ButtonPress-1>",
                        lambda e, a=app_name, tf=tag_frame: self._start_tag_drag(e, a, tf))
            widget.bind("<B1-Motion>", self._tag_drag_motion)
            widget.bind("<ButtonRelease-1>",
                        lambda e, a=app_name, tf=tag_frame: self._tag_drag_end(e, a, tf))



    def _remove_app(self, app_name: str, tag_frame: ctk.CTkFrame):
        if app_name in self.assigned_apps:
            self.assigned_apps.remove(app_name)
            tag_frame.destroy()
            self._update_empty_state()
            self._notify()
            if self._app_pool:
                self._app_pool.refresh_used_state()

    # ------------------------------------------------------------------
    # Empty-state helpers
    # ------------------------------------------------------------------

    def _show_empty_state(self):
        if self.apps_container is None:
            return
        if self.empty_label is None or not self.empty_label.winfo_exists():
            self.empty_label = ctk.CTkLabel(
                self.apps_container,
                text="Sleep hier een app naartoe",
                text_color="gray",
                font=("Roboto", 13),
                justify="center"
            )
            self.empty_label.pack(expand=True)

    def _hide_empty_state(self):
        try:
            if self.empty_label and self.empty_label.winfo_exists():
                self.empty_label.pack_forget()
        except Exception:
            pass

    def _update_empty_state(self):
        if self.is_master_volume or self.apps_container is None:
            return
        if len(self.assigned_apps) == 0:
            self._show_empty_state()

    # ------------------------------------------------------------------
    # Rename dialogs (ongewijzigd t.o.v. origineel)
    # ------------------------------------------------------------------

    def _show_rename_dialog(self):
        dialog = ctk.CTkToplevel()
        dialog.title(f"Rename {self.slider_name}")
        dialog.geometry("450x220")
        dialog.grab_set()
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 110
        dialog.geometry(f"450x220+{x}+{y}")

        ctk.CTkLabel(dialog, text=f"✏️ Rename {self.slider_name}",
                     font=("Roboto", 20, "bold")).pack(pady=20)
        ctk.CTkLabel(dialog, text="Enter new name:",
                     font=("Roboto", 12), text_color="gray").pack(pady=(0, 5))

        entry = ctk.CTkEntry(dialog, width=350, height=45,
                             placeholder_text="e.g. Gaming Audio, Music, Discord...",
                             font=("Roboto", 14))
        entry.insert(0, self.slider_name)
        entry.pack(pady=10)
        entry.focus()
        entry.select_range(0, "end")

        def save():
            new_name = entry.get().strip()
            if 0 < len(new_name) <= 30:
                self.slider_name = new_name
                self.header_label.configure(text=new_name)
                if hasattr(self, "on_rename_callback") and self.on_rename_callback:
                    self.on_rename_callback(self.index, new_name)
                dialog.destroy()
            elif len(new_name) > 30:
                err = ctk.CTkLabel(dialog, text="❌ Naam te lang! (max 30 tekens)",
                                   font=("Roboto", 11, "bold"), text_color="red")
                err.pack(pady=5)
                dialog.after(2000, err.destroy)

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(pady=20)
        ctk.CTkButton(btn_row, text="Cancel", command=dialog.destroy,
                      width=150, height=40).pack(side="left", padx=10)
        ctk.CTkButton(btn_row, text="💾 Save Name", command=save,
                      width=150, height=40, fg_color="green",
                      hover_color="darkgreen").pack(side="right", padx=10)
        entry.bind("<Return>", lambda e: save())

    def _show_app_rename_dialog(self, original_app_name: str, label_widget):
        current_display = self._get_app_display_name(original_app_name)

        dialog = ctk.CTkToplevel()
        dialog.title(f"Rename {original_app_name}")
        dialog.geometry("450x240")
        dialog.grab_set()
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 120
        dialog.geometry(f"450x240+{x}+{y}")

        ctk.CTkLabel(dialog, text="✏️ Rename App",
                     font=("Roboto", 20, "bold")).pack(pady=15)
        ctk.CTkLabel(dialog, text=f"Original: {original_app_name}",
                     font=("Roboto", 11), text_color="gray").pack(pady=(0, 5))
        ctk.CTkLabel(dialog, text="Display name:",
                     font=("Roboto", 12), text_color="gray").pack(pady=(0, 5))

        entry = ctk.CTkEntry(dialog, width=350, height=45,
                             placeholder_text="e.g. Guild Wars 2, Discord...",
                             font=("Roboto", 14))
        entry.insert(0, current_display)
        entry.pack(pady=10)
        entry.focus()
        entry.select_range(0, "end")

        def save():
            new_name = entry.get().strip()
            if 0 < len(new_name) <= 40:
                self._set_app_display_name(original_app_name, new_name)
                label_widget.configure(text=new_name)
                if hasattr(self, "on_app_rename_callback") and self.on_app_rename_callback:
                    self.on_app_rename_callback(original_app_name, new_name)
                dialog.destroy()
            elif len(new_name) > 40:
                err = ctk.CTkLabel(dialog, text="❌ Naam te lang! (max 40 tekens)",
                                   font=("Roboto", 11, "bold"), text_color="red")
                err.pack(pady=5)
                dialog.after(2000, err.destroy)

        def reset():
            entry.delete(0, "end")
            entry.insert(0, original_app_name)

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(pady=15)
        ctk.CTkButton(btn_row, text="Cancel", command=dialog.destroy,
                      width=130, height=40).pack(side="left", padx=10)
        ctk.CTkButton(btn_row, text="🔄 Reset", command=reset,
                      width=130, height=40, fg_color="orange",
                      hover_color="darkorange").pack(side="left", padx=10)
        ctk.CTkButton(btn_row, text="💾 Save", command=save,
                      width=130, height=40, fg_color="green",
                      hover_color="darkgreen").pack(side="right", padx=10)
        entry.bind("<Return>", lambda e: save())
