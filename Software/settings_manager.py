"""
Settings manager for Whoa-Scope application.
Handles persistent storage of user preferences using Kivy's JsonStore.
Settings are stored in the OS-appropriate user data directory.
"""

import os
import glob
from kivy.storage.jsonstore import JsonStore
from kivy.app import App
from kivy.utils import platform


def get_fonts_directory():
    """Get the path to the fonts directory."""
    import sys
    # Try relative to current directory first
    fonts_dir = os.path.join(os.getcwd(), 'fonts')
    if os.path.isdir(fonts_dir):
        return fonts_dir
    # Try relative to script location (for frozen apps)
    if getattr(sys, 'frozen', False):
        fonts_dir = os.path.join(sys._MEIPASS, 'fonts')
        if os.path.isdir(fonts_dir):
            return fonts_dir
    return None


def scan_available_fonts():
    """
    Scan the ./fonts directory for available font files.
    Returns a dict mapping display names to font file paths.
    """
    fonts = {}
    fonts_dir = get_fonts_directory()
    
    if fonts_dir and os.path.isdir(fonts_dir):
        for ext in ['*.ttf', '*.otf', '*.TTF', '*.OTF']:
            for font_path in glob.glob(os.path.join(fonts_dir, ext)):
                # Extract display name from filename
                filename = os.path.basename(font_path)
                # Remove extension and clean up name
                name = os.path.splitext(filename)[0]
                # Make name more readable (replace dashes/underscores with spaces)
                display_name = name.replace('-', ' ').replace('_', ' ')
                # Remove common suffixes like "Regular", "VariableFont", etc.
                for suffix in ['Regular', 'VariableFont wdth,wght', 'VariableFont']:
                    display_name = display_name.replace(suffix, '').strip()
                fonts[display_name] = font_path
    
    return fonts


# Scan available fonts from ./fonts directory
AVAILABLE_FONTS = scan_available_fonts()

# Default settings - use first available font or 'Roboto' (Kivy default)
default_font = list(AVAILABLE_FONTS.keys())[0] if AVAILABLE_FONTS else 'Roboto'
DEFAULT_SETTINGS = {
    'font_name': default_font,
    'font_scale': 1.0,  # 100% scale factor for font sizes
    'launch_maximized': False,
}


def get_font_path(font_name):
    """Get the full path to a font file by its display name."""
    return AVAILABLE_FONTS.get(font_name, None)


class SettingsManager:
    """
    Manages application settings with persistent storage.
    Uses Kivy's JsonStore for cross-platform compatibility.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._store = None
        self._settings = DEFAULT_SETTINGS.copy()
    
    def _get_settings_path(self):
        """
        Get the path to the settings file in the appropriate OS directory.
        Uses platformdirs for cross-platform compatibility.
        """
        if platform == 'win':
            # Windows: %APPDATA%/WhoaScope/
            base_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
            settings_dir = os.path.join(base_dir, 'WhoaScope')
        elif platform == 'macosx':
            # macOS: ~/Library/Application Support/WhoaScope/
            settings_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'WhoaScope')
        elif platform == 'linux':
            # Linux: ~/.config/WhoaScope/ or $XDG_CONFIG_HOME/WhoaScope/
            xdg_config = os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))
            settings_dir = os.path.join(xdg_config, 'WhoaScope')
        else:
            # Fallback for other platforms (iOS, Android, etc.)
            settings_dir = os.path.join(os.path.expanduser('~'), '.whoascope')
        
        # Create directory if it doesn't exist
        os.makedirs(settings_dir, exist_ok=True)
        
        return os.path.join(settings_dir, 'settings.json')
    
    def initialize(self):
        """Initialize the settings store and load saved settings."""
        settings_path = self._get_settings_path()
        self._store = JsonStore(settings_path)
        self._load_settings()
    
    def _load_settings(self):
        """Load settings from the store."""
        if self._store is None:
            return
        
        for key, default_value in DEFAULT_SETTINGS.items():
            if self._store.exists(key):
                try:
                    stored = self._store.get(key)
                    self._settings[key] = stored.get('value', default_value)
                except Exception:
                    self._settings[key] = default_value
            else:
                self._settings[key] = default_value
    
    def _save_setting(self, key, value):
        """Save a single setting to the store."""
        if self._store is None:
            return
        self._store.put(key, value=value)
    
    def get(self, key, default=None):
        """Get a setting value."""
        return self._settings.get(key, default if default is not None else DEFAULT_SETTINGS.get(key))
    
    def set(self, key, value):
        """Set a setting value and persist it."""
        self._settings[key] = value
        self._save_setting(key, value)
    
    @property
    def font_name(self):
        return self.get('font_name')
    
    @font_name.setter
    def font_name(self, value):
        self.set('font_name', value)
    
    @property
    def font_scale(self):
        return self.get('font_scale')
    
    @font_scale.setter
    def font_scale(self, value):
        self.set('font_scale', value)
    
    @property
    def launch_maximized(self):
        return self.get('launch_maximized')
    
    @launch_maximized.setter
    def launch_maximized(self, value):
        self.set('launch_maximized', value)
    
    def get_settings_directory(self):
        """Return the directory where settings are stored."""
        return os.path.dirname(self._get_settings_path())


# Singleton instance
settings_manager = SettingsManager()
