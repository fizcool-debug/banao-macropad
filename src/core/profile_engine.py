# profile_engine.py
#
# Copyright 2026 Bhawesh Kumar
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import json
from gi.repository import GLib

class ProfileEngine:
    """Manages application-specific profiles mapping hardware events to actions."""
    
    def __init__(self):
        # Determine standard XDG config directory
        config_dir = os.path.join(GLib.get_user_config_dir(), "banao")
        os.makedirs(config_dir, exist_ok=True)
        self.profile_path = os.path.join(config_dir, "profiles.json")
        
        self.profiles = {}
        self.load_profiles()

    def get_default_profiles(self):
        """Generates standard default profiles for first-run initialization."""
        return {
            "Global": {
                "name": "Global Default",
                "app_class": "",
                "bindings": {
                    "B1": {"type": "shortcut", "value": ["KEY_LEFTMETA"], "label": "Show Activities"},
                    "B2": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_LEFTALT", "KEY_T"], "label": "Open Terminal"},
                    "B3": {"type": "shortcut", "value": ["KEY_LEFTMETA", "KEY_D"], "label": "Show Desktop"},
                    "B4": {"type": "shortcut", "value": ["KEY_PLAYPAUSE"], "label": "Play/Pause"},
                    "B5": {"type": "shortcut", "value": ["KEY_PREVIOUSSONG"], "label": "Prev Track"},
                    "B6": {"type": "shortcut", "value": ["KEY_NEXTSONG"], "label": "Next Track"},
                    "B7": {"type": "shortcut", "value": ["KEY_MUTE"], "label": "Mute Audio"},
                    "B8": {"type": "shortcut", "value": ["KEY_LEFTMETA", "KEY_L"], "label": "Lock Screen"},
                    "EB": {"type": "shortcut", "value": ["KEY_PLAYPAUSE"], "label": "Encoder Play/Pause"},
                    "E1_CW": {"type": "shortcut", "value": ["KEY_VOLUMEUP"], "label": "Volume Up"},
                    "E1_CCW": {"type": "shortcut", "value": ["KEY_VOLUMEDOWN"], "label": "Volume Down"}
                }
            },
            "Inkscape": {
                "name": "Inkscape Editor",
                "app_class": "inkscape",
                "bindings": {
                    "B1": {"type": "shortcut", "value": ["KEY_S"], "label": "Select Tool"},
                    "B2": {"type": "shortcut", "value": ["KEY_N"], "label": "Node Tool"},
                    "B3": {"type": "shortcut", "value": ["KEY_F4"], "label": "Rectangle Tool"},
                    "B4": {"type": "shortcut", "value": ["KEY_F5"], "label": "Ellipse Tool"},
                    "B5": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_SHIFT", "KEY_A"], "label": "Align & Distribute"},
                    "B6": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_SHIFT", "KEY_F"], "label": "Fill & Stroke"},
                    "B7": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_D"], "label": "Duplicate Element"},
                    "B8": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_G"], "label": "Group Items"},
                    "EB": {"type": "shortcut", "value": ["KEY_ESC"], "label": "Deselect All"},
                    "E1_CW": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_EQUAL"], "label": "Zoom In"},
                    "E1_CCW": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_MINUS"], "label": "Zoom Out"}
                }
            },
            "Chrome": {
                "name": "Google Chrome",
                "app_class": "google-chrome",
                "bindings": {
                    "B1": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_T"], "label": "New Tab"},
                    "B2": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_W"], "label": "Close Tab"},
                    "B3": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_SHIFT", "KEY_T"], "label": "Reopen Tab"},
                    "B4": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_PAGEDOWN"], "label": "Next Tab"},
                    "B5": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_PAGEUP"], "label": "Prev Tab"},
                    "B6": {"type": "shortcut", "value": ["KEY_LEFTALT", "KEY_LEFT"], "label": "Go Back"},
                    "B7": {"type": "shortcut", "value": ["KEY_LEFTALT", "KEY_RIGHT"], "label": "Go Forward"},
                    "B8": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_R"], "label": "Reload Page"},
                    "EB": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_F"], "label": "Find in Page"},
                    "E1_CW": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_EQUAL"], "label": "Zoom In"},
                    "E1_CCW": {"type": "shortcut", "value": ["KEY_LEFTCTRL", "KEY_MINUS"], "label": "Zoom Out"}
                }
            }
        }

    def load_profiles(self):
        """Loads profiles from the JSON configuration file."""
        if not os.path.exists(self.profile_path):
            self.profiles = self.get_default_profiles()
            self.save_profiles()
        else:
            try:
                with open(self.profile_path, 'r') as f:
                    self.profiles = json.load(f)
            except Exception as e:
                print(f"[Profiles] Failed to load config file: {e}. Resetting to default.")
                self.profiles = self.get_default_profiles()

    def save_profiles(self):
        """Saves current profiles back to the JSON configuration file."""
        try:
            with open(self.profile_path, 'w') as f:
                json.dump(self.profiles, f, indent=4)
        except Exception as e:
            print(f"[Profiles] Failed to write config file: {e}")

    def get_profile_for_app(self, app_class):
        """Returns the first profile matching the active application's wm_class.
        
        Args:
            app_class: The application name or window class under active focus.
            
        Returns:
            Tuple (profile_key, profile_dict)
        """
        if not app_class:
            return "Global", self.profiles["Global"]
            
        app_class_lower = app_class.lower()
        for key, profile in self.profiles.items():
            mapped_class = profile.get("app_class", "")
            if mapped_class and mapped_class.lower() == app_class_lower:
                return key, profile
                
        # Return fallback Global profile
        return "Global", self.profiles["Global"]

    def update_binding(self, profile_name, control_id, action_type, val, label=""):
        """Updates or sets a control binding inside a profile.
        
        Args:
            profile_name: Name of the profile (e.g. 'Global', 'Chrome').
            control_id: Control ID name (e.g. 'B1', 'EB', 'E1_CW').
            action_type: Type of action ('shortcut', 'text', 'none').
            val: Action value (list of key strings, or text string, or None).
            label: Custom user-facing display label for the binding.
        """
        if profile_name not in self.profiles:
            raise KeyError(f"Profile '{profile_name}' does not exist.")
            
        bindings = self.profiles[profile_name].setdefault("bindings", {})
        bindings[control_id] = {
            "type": action_type,
            "value": val,
            "label": label
        }
        self.save_profiles()

    def add_profile(self, name, app_class=""):
        """Creates a new empty application profile.
        
        Args:
            name: Human readable profile identifier.
            app_class: Focused application window class target.
        """
        if name in self.profiles:
            raise ValueError(f"Profile '{name}' already exists.")
            
        # Copy bindings structure from Global as template
        global_bindings = self.profiles["Global"]["bindings"]
        new_bindings = {}
        for k, v in global_bindings.items():
            new_bindings[k] = v.copy()
            
        self.profiles[name] = {
            "name": name,
            "app_class": app_class,
            "bindings": new_bindings
        }
        self.save_profiles()

    def delete_profile(self, name):
        """Deletes a profile from configuration. 'Global' profile cannot be deleted."""
        if name == "Global":
            raise ValueError("The 'Global' default profile cannot be deleted.")
        if name in self.profiles:
            del self.profiles[name]
            self.save_profiles()
