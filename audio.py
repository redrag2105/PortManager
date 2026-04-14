import os
import sys
from pathlib import Path
from utils import get_settings

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', str(Path(__file__).resolve().parent))
    return os.path.join(base_path, relative_path)

# Suppress pygame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

class AudioEngine:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AudioEngine, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_audio()
        return cls._instance

    def _init_audio(self):
        settings = get_settings()
        self.sounds = {}
        self.volumes = settings.get("sounds", {}).get("volumes", {
            "splash": 0.2,
            "scroll": 0.1,
            "close": 0.3,
            "click": 1,
            "error": 0.3,
            "success": 0.4
        })
        self.is_muted = settings.get("sounds", {}).get("mute", False)
        
        try:
            # Initialize with small buffer to prevent latency
            pygame.mixer.init(buffer=512)
            
            # Load sounds prioritizing .ogg over .wav and .mp3 based on config keys
            for sound_name in self.volumes.keys():
                for ext in (".ogg", ".wav", ".mp3"):
                    if sound_name not in self.sounds:
                        raw_path = f"assets/{sound_name}{ext}"
                        filepath = resource_path(raw_path)
                        self._load_sound(sound_name, filepath)
        except Exception:
            pass

    def _load_sound(self, name, filepath):
        """Safely checks if file exists before loading so app doesn't crash."""
        if os.path.exists(filepath):
            try:
                snd = pygame.mixer.Sound(filepath)
                # Apply custom volumes
                snd.set_volume(self.volumes.get(name, 0.5) if not self.is_muted else 0.0)
                self.sounds[name] = snd
            except Exception:
                pass

    def set_volume(self, name, volume):
        """Set volume of a specific sound (0.0 to 1.0)."""
        self.volumes[name] = volume
        if name in self.sounds and not self.is_muted:
            self.sounds[name].set_volume(volume)

    def get_volume(self, name):
        """Get volume of a specific sound."""
        return self.volumes.get(name, 0.5)

    def set_mute(self, mute: bool):
        self.is_muted = mute
        for name, snd in self.sounds.items():
            snd.set_volume(0.0 if mute else self.volumes.get(name, 0.5))

    def play(self, name, loop=False):
        """Play a loaded sound."""
        if self.is_muted:
            return
        if name in self.sounds:
            try:
                self.sounds[name].play(loops=-1 if loop else 0)
            except Exception:
                pass

    def stop(self, name=None):
        """Stop a specific sound, or all sounds if no name is provided."""
        try:
            if name and name in self.sounds:
                self.sounds[name].stop()
            else:
                pygame.mixer.stop()
        except Exception:
            pass

# Global instance exporter
audio = AudioEngine()
