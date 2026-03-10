"""
Update Dialog

Modern dialog for update notifications with:
- Version info and release notes
- Download and install options
- "Remind later" and "Skip this version"
"""

import customtkinter as ctk
from typing import Dict, Callable, Optional
from pathlib import Path
import threading


class UpdateDialog(ctk.CTkToplevel):
    """
    Update available dialog with modern UI.
    
    Features:
    - Version comparison
    - Release notes display
    - Download progress
    - Auto-install option
    """
    
    def __init__(
        self,
        parent,
        update_info: Dict,
        current_version: str,
        on_update: Optional[Callable] = None,
        on_dismiss: Optional[Callable] = None,
        on_skip: Optional[Callable] = None,
        check_interval_hours: float = 24.0
    ):
        """
        Initialize the update dialog.
        
        Args:
            parent: Parent window
            update_info: Dict with update information from UpdateManager
            current_version: Current installed version
            on_update: Callback for "Update Now" action
            on_dismiss: Callback for "Remind Me Later"
            on_skip: Callback for "Skip This Version"
            check_interval_hours: Hours until next reminder
        """
        super().__init__(parent)
        
        self.update_info = update_info
        self.current_version = current_version
        self.on_update = on_update
        self.on_dismiss = on_dismiss
        self.on_skip = on_skip
        self.check_interval_hours = check_interval_hours
        
        self.downloading = False
        self.download_thread = None
        
        # Window setup
        self.title("Update Available")
        self.geometry("600x900")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 300
        y = (self.winfo_screenheight() // 2) - 450
        self.geometry(f"600x900+{x}+{y}")
        
        # Titlebar icoon - exact zoals main_window
        try:
            from pathlib import Path
            import sys
            icon_path = Path(sys.executable).parent / "BOBicon.ico" if getattr(sys, 'frozen', False) else Path(__file__).parent / "BOBicon.ico"
            self.iconbitmap(str(icon_path))
        except Exception:
            pass
        
        # Build UI
        self._create_ui()
    
    def _create_ui(self):
        """Create the complete UI."""
        # Main container
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header with icon and title
        self._create_header(main)
        
        # Version info card
        self._create_version_card(main)
        
        # Release notes
        self._create_release_notes(main)
        
        # Download info
        self._create_download_info(main)
        
        # Progress bar (hidden until download starts)
        self._create_progress_section(main)
        
        # Action buttons
        self._create_buttons(main)
    
    def _create_header(self, parent):
        """Create header with icon and title."""
        header = ctk.CTkFrame(parent, fg_color=("gray85", "gray20"), corner_radius=12)
        header.pack(fill="x", pady=(0, 15))
        
        # Icon
        icon_label = ctk.CTkLabel(
            header,
            text="⬆️",
            font=("Segoe UI Emoji", 48)
        )
        icon_label.pack(pady=(15, 5))
        
        # Title
        title = ctk.CTkLabel(
            header,
            text="Update Available!",
            font=("Roboto", 24, "bold")
        )
        title.pack(pady=(0, 5))
        
        # Subtitle
        subtitle = ctk.CTkLabel(
            header,
            text="A new version of BOB is available",
            font=("Roboto", 12),
            text_color="gray"
        )
        subtitle.pack(pady=(0, 15))
    
    def _create_version_card(self, parent):
        """Create version comparison card."""
        card = ctk.CTkFrame(parent, fg_color=("gray85", "gray20"), corner_radius=12)
        card.pack(fill="x", pady=(0, 15))
        
        # Container for versions
        versions_frame = ctk.CTkFrame(card, fg_color="transparent")
        versions_frame.pack(fill="x", padx=20, pady=15)
        
        # Current version
        current_frame = ctk.CTkFrame(versions_frame, fg_color="transparent")
        current_frame.pack(side="left", expand=True, fill="x")
        
        ctk.CTkLabel(
            current_frame,
            text="Current Version",
            font=("Roboto", 11),
            text_color="gray"
        ).pack()
        
        ctk.CTkLabel(
            current_frame,
            text=f"v{self.current_version}",
            font=("Roboto Mono", 18, "bold")
        ).pack()
        
        # Arrow
        ctk.CTkLabel(
            versions_frame,
            text="→",
            font=("Roboto", 24),
            width=60
        ).pack(side="left")
        
        # New version
        new_frame = ctk.CTkFrame(versions_frame, fg_color="transparent")
        new_frame.pack(side="left", expand=True, fill="x")
        
        ctk.CTkLabel(
            new_frame,
            text="New Version",
            font=("Roboto", 11),
            text_color="gray"
        ).pack()
        
        ctk.CTkLabel(
            new_frame,
            text=f"v{self.update_info['version']}",
            font=("Roboto Mono", 18, "bold"),
            text_color=("#2e7d32", "#4caf50")  # Green accent
        ).pack()
        
        # Release name (if available)
        release_name = self.update_info.get('name', '')
        if release_name and release_name != self.update_info['version']:
            name_label = ctk.CTkLabel(
                card,
                text=f'"{release_name}"',
                font=("Roboto", 13, "italic"),
                text_color="gray"
            )
            name_label.pack(pady=(0, 10))
    
    def _create_release_notes(self, parent):
        """Create release notes section."""
        notes_frame = ctk.CTkFrame(parent, fg_color=("gray85", "gray20"), corner_radius=12)
        notes_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Header
        header = ctk.CTkLabel(
            notes_frame,
            text="📝 What's New",
            font=("Roboto", 14, "bold"),
            anchor="w"
        )
        header.pack(fill="x", padx=15, pady=(12, 8))
        
        # Scrollable text box for release notes
        release_notes = self.update_info.get('notes', 'No release notes available.')
        
        # Limit length for better display
        if len(release_notes) > 1000:
            release_notes = release_notes[:1000] + "\n\n[...Full release notes on GitHub...]"
        
        notes_text = ctk.CTkTextbox(
            notes_frame,
            height=200,
            font=("Roboto", 11),
            wrap="word"
        )
        notes_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        notes_text.insert("1.0", release_notes)
        notes_text.configure(state="disabled")  # Read-only
    
    def _create_download_info(self, parent):
        """Create download information section."""
        info_frame = ctk.CTkFrame(parent, fg_color=("gray85", "gray20"), corner_radius=12)
        info_frame.pack(fill="x", pady=(0, 15))
        
        # Download size
        size_mb = self.update_info.get('installer_size', 0) / 1024 / 1024
        
        info_text = f"📦 Download size: {size_mb:.1f} MB"
        
        # Published date
        published = self.update_info.get('published_at', '')
        if published:
            try:
                from datetime import datetime
                date_obj = datetime.fromisoformat(published.replace('Z', '+00:00'))
                date_str = date_obj.strftime('%B %d, %Y')
                info_text += f"  •  📅 Published: {date_str}"
            except:
                pass
        
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=("Roboto", 11),
            text_color="gray"
        ).pack(pady=12)
    
    def _create_progress_section(self, parent):
        """Create download progress section (hidden until download)."""
        self.progress_frame = ctk.CTkFrame(
            parent,
            fg_color=("gray85", "gray20"),
            corner_radius=12
        )
        # Pack later when needed
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Downloading...",
            font=("Roboto", 12)
        )
        self.progress_label.pack(pady=(15, 5))
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=500
        )
        self.progress_bar.pack(pady=(0, 5), padx=30)
        self.progress_bar.set(0)
        
        self.progress_percent = ctk.CTkLabel(
            self.progress_frame,
            text="0%",
            font=("Roboto Mono", 11),
            text_color="gray"
        )
        self.progress_percent.pack(pady=(0, 15))
    
    def _create_buttons(self, parent):
        """Create action buttons."""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(5, 0))
        
        # Update Now button (primary)
        self.update_button = ctk.CTkButton(
            button_frame,
            text="⬇️ Download & Install Now",
            command=self._handle_update,
            height=45,
            font=("Roboto", 14, "bold"),
            fg_color=("#2e7d32", "#2e7d32"),
            hover_color=("#1b5e20", "#1b5e20")
        )
        self.update_button.pack(fill="x", pady=(0, 8))
        
        # Secondary options
        secondary_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        secondary_frame.pack(fill="x")
        
        # GitHub button
        github_button = ctk.CTkButton(
            secondary_frame,
            text="🌐 View on GitHub",
            command=self._open_github,
            height=38,
            font=("Roboto", 12),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40")
        )
        github_button.pack(side="left", expand=True, fill="x", padx=(0, 4))
        
        # Remind Later button
        remind_button = ctk.CTkButton(
            secondary_frame,
            text="🔔 Remind Me Later",
            command=self._handle_dismiss,
            height=38,
            font=("Roboto", 12),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40")
        )
        remind_button.pack(side="left", expand=True, fill="x", padx=(2, 2))
        
        # Skip button
        skip_button = ctk.CTkButton(
            secondary_frame,
            text="⏭️ Skip This Version",
            command=self._handle_skip,
            height=38,
            font=("Roboto", 12),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40")
        )
        skip_button.pack(side="left", expand=True, fill="x", padx=(4, 0))
        
        # Info text about reminder timing (dynamic based on check interval)
        if self.check_interval_hours < 0.1:  # Less than 6 minutes
            minutes = int(self.check_interval_hours * 60)
            reminder_text = f"💡 Reminder: You'll be notified again in ~{minutes} minute{'s' if minutes != 1 else ''}"
        elif self.check_interval_hours < 2:  # Less than 2 hours
            hours = self.check_interval_hours
            reminder_text = f"💡 Reminder: You'll be notified again in ~{hours:.1f} hour{'s' if hours >= 2 else ''}"
        else:
            hours = int(self.check_interval_hours)
            reminder_text = f"💡 Reminder: You'll be notified again in ~{hours} hour{'s' if hours != 1 else ''}"
        
        info_text = ctk.CTkLabel(
            button_frame,
            text=reminder_text,
            font=("Roboto", 9),
            text_color="gray"
        )
        info_text.pack(pady=(8, 0))
    
    def _handle_update(self):
        """Handle update button click."""
        if self.on_update:
            self.on_update()
            self.destroy()
    
    def _handle_dismiss(self):
        """Handle remind later button."""
        if self.on_dismiss:
            self.on_dismiss()
        self.destroy()
    
    def _handle_skip(self):
        """Handle skip version button."""
        if self.on_skip:
            self.on_skip()
        self.destroy()
    
    def _open_github(self):
        """Open GitHub release page."""
        import webbrowser
        url = self.update_info.get('url')
        if url:
            webbrowser.open(url)
