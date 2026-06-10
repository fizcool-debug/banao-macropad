# engine.py
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

import time
import threading
from .profile_engine import ProfileEngine
from .serial_reader import SerialReader

class BanaoEngine:
    """Core platform-agnostic coordinator for the banao01 macropad.
    
    This class uses Dependency Injection to remain decoupled from operating system APIs
    and window managers. It receives input injector, audio, and window detection
    adapters at instantiation.
    """
    
    def __init__(self, input_injector, audio_controller, window_detector, serial_port="/dev/ttyACM0"):
        # OS abstraction injection
        self.input_injector = input_injector
        self.audio_controller = audio_controller
        self.window_detector = window_detector
        
        # Load configurations
        self.profile_engine = ProfileEngine()
        self.active_profile_name = "Global"
        self.active_profile = self.profile_engine.profiles["Global"]
        
        # Reader and polling threads
        self.serial_port = serial_port
        self.serial_reader = None
        self.window_thread = None
        self.running = False
        
        # State tracking
        self.last_state = {
            "P1": 0, "P2": 0,
            "B1": 0, "B2": 0, "B3": 0, "B4": 0,
            "B5": 0, "B6": 0, "B7": 0, "B8": 0,
            "EB": 0
        }
        self.focused_app_class = "Global"
        self.auto_profile_switching = True
        
        # Callback list for UI sync
        self.callbacks = {
            "state_updated": [],     # (current_state)
            "profile_changed": [],   # (profile_name, profile_dict)
            "window_changed": []     # (window_class)
        }

    def register_callback(self, event_name, cb):
        """Allows external UI to subscribe to engine events."""
        if event_name in self.callbacks:
            self.callbacks[event_name].append(cb)

    def _trigger_callbacks(self, event_name, *args):
        for cb in self.callbacks.get(event_name, []):
            try:
                cb(*args)
            except Exception as e:
                print(f"[Engine] Callback error in event '{event_name}': {e}")

    def start(self):
        """Starts background reader and active window polling loops."""
        self.running = True
        
        # Start serial connection reader
        self.serial_reader = SerialReader(
            port=self.serial_port, 
            callback=self._on_serial_packet
        )
        self.serial_reader.start()
        
        # Start active application polling thread (runs every 500ms)
        self.window_thread = threading.Thread(target=self._window_poll_loop, daemon=True)
        self.window_thread.start()

    def stop(self):
        """Stops background threads and cleans up interfaces."""
        self.running = False
        if self.serial_reader:
            self.serial_reader.stop()
            self.serial_reader.join(timeout=1.0)
        
        self.input_injector.close()
        print("[Engine] Core engine stopped successfully.")

    def _window_poll_loop(self):
        """Thread loop scanning active window focus to load profiles dynamically."""
        while self.running:
            try:
                app_class = self.window_detector.get_active_window_class()
                # Ignore focus events when our own Banao configurator window is active
                if app_class and any(x in app_class.lower() for x in ("banao", "org.dietro.banao", "org.fizcool.banao01")):
                    time.sleep(0.5)
                    continue

                if app_class != self.focused_app_class:
                    self.focused_app_class = app_class
                    self._trigger_callbacks("window_changed", app_class)
                    
                    # Update profile context (if auto-switching is enabled)
                    if self.auto_profile_switching:
                        prof_key, prof_data = self.profile_engine.get_profile_for_app(app_class)
                        if prof_key != self.active_profile_name:
                            self.active_profile_name = prof_key
                            self.active_profile = prof_data
                            self._trigger_callbacks("profile_changed", prof_key, prof_data)
            except Exception as e:
                print(f"[Engine] Window polling error: {e}")
                
            time.sleep(0.5)

    def _on_serial_packet(self, packet):
        """Callback received from serial reader thread when packet arrives."""
        # 1. Handle Potentiometer 1 (Master Volume)
        if "P1" in packet:
            val_p1 = packet["P1"]
            if val_p1 != self.last_state["P1"]:
                # Convert 0-1023 to 0.0-1.0 (reversed direction)
                vol = (1023.0 - val_p1) / 1023.0
                self.audio_controller.set_master_volume(vol)
                self.last_state["P1"] = val_p1
                
        # 2. Handle Potentiometer 2 (Focused App Volume)
        if "P2" in packet:
            val_p2 = packet["P2"]
            if val_p2 != self.last_state["P2"]:
                # Convert 0-1023 to 0.0-1.0 (reversed direction)
                vol = (1023.0 - val_p2) / 1023.0
                # Directly target the focused application window class
                # Fall back to currently active profile class if window focus is unknown (Wayland fallback)
                target_app = None
                if self.focused_app_class and self.focused_app_class != "Global":
                    target_app = self.focused_app_class
                elif self.active_profile:
                    target_app = self.active_profile.get("app_class")
                
                # If no specific application name is identified, fall back to "Global"
                # which will control the active/playing audio stream(s)
                if not target_app:
                    target_app = "Global"
                
                self.audio_controller.set_app_volume(target_app, vol)
                self.last_state["P2"] = val_p2

        # 3. Handle buttons B1 - B8 & EB (Encoder Button)
        buttons = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "EB"]
        for btn in buttons:
            if btn in packet:
                val = packet[btn]
                old_val = self.last_state[btn]
                if val != old_val:
                    # Transition: Pressed (0 -> 1)
                    if val == 1:
                        self._execute_binding(btn)
                    self.last_state[btn] = val

        # 4. Handle Encoder E1 Rotation
        if "E1" in packet:
            direction = packet["E1"]
            if direction == "CW":
                self._execute_binding("E1_CW")
            elif direction == "CCW":
                self._execute_binding("E1_CCW")

        # Notify UI of updated state
        self._trigger_callbacks("state_updated", packet)

    def _execute_binding(self, control_id):
        """Looks up the binding for the current profile and executes the injected input."""
        bindings = self.active_profile.get("bindings", {})
        binding = bindings.get(control_id)
        
        if not binding:
            # Fallback to Global if not defined in active profile
            global_bindings = self.profile_engine.profiles["Global"].get("bindings", {})
            binding = global_bindings.get(control_id)
            
        if not binding:
            return
            
        action_type = binding.get("type")
        val = binding.get("value")
        
        if action_type == "shortcut" and val:
            # val is a list of keys, e.g. ["KEY_LEFTCTRL", "KEY_T"]
            try:
                self.input_injector.press_combo(val)
            except Exception as e:
                print(f"[Engine] Shortcut injection failed for {val}: {e}")
        elif action_type == "text" and val:
            # val is a string
            try:
                self.input_injector.type_string(val)
            except Exception as e:
                print(f"[Engine] Text injection failed for {val}: {e}")
