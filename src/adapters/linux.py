# linux.py
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
import time
import json
import subprocess
import pulsectl
import evdev
from evdev import UInput, ecodes as e
import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib

from .base import BaseInputInjector, BaseAudioController, BaseActiveWindowDetector

# Character-to-keycode mapping for keyboard simulation
_CHAR_TO_KEY = {
    'a': (e.KEY_A, False), 'b': (e.KEY_B, False), 'c': (e.KEY_C, False), 'd': (e.KEY_D, False),
    'e': (e.KEY_E, False), 'f': (e.KEY_F, False), 'g': (e.KEY_G, False), 'h': (e.KEY_H, False),
    'i': (e.KEY_I, False), 'j': (e.KEY_J, False), 'k': (e.KEY_K, False), 'l': (e.KEY_L, False),
    'm': (e.KEY_M, False), 'n': (e.KEY_N, False), 'o': (e.KEY_O, False), 'p': (e.KEY_P, False),
    'q': (e.KEY_Q, False), 'r': (e.KEY_R, False), 's': (e.KEY_S, False), 't': (e.KEY_T, False),
    'u': (e.KEY_U, False), 'v': (e.KEY_V, False), 'w': (e.KEY_W, False), 'x': (e.KEY_X, False),
    'y': (e.KEY_Y, False), 'z': (e.KEY_Z, False),
    'A': (e.KEY_A, True), 'B': (e.KEY_B, True), 'C': (e.KEY_C, True), 'D': (e.KEY_D, True),
    'E': (e.KEY_E, True), 'F': (e.KEY_F, True), 'G': (e.KEY_G, True), 'H': (e.KEY_H, True),
    'I': (e.KEY_I, True), 'J': (e.KEY_J, True), 'K': (e.KEY_K, True), 'L': (e.KEY_L, True),
    'M': (e.KEY_M, True), 'N': (e.KEY_N, True), 'O': (e.KEY_O, True), 'P': (e.KEY_P, True),
    'Q': (e.KEY_Q, True), 'R': (e.KEY_R, True), 'S': (e.KEY_S, True), 'T': (e.KEY_T, True),
    'U': (e.KEY_U, True), 'V': (e.KEY_V, True), 'W': (e.KEY_W, True), 'X': (e.KEY_X, True),
    'Y': (e.KEY_Y, True), 'Z': (e.KEY_Z, True),
    '1': (e.KEY_1, False), '2': (e.KEY_2, False), '3': (e.KEY_3, False), '4': (e.KEY_4, False),
    '5': (e.KEY_5, False), '6': (e.KEY_6, False), '7': (e.KEY_7, False), '8': (e.KEY_8, False),
    '9': (e.KEY_9, False), '0': (e.KEY_0, False),
    '!': (e.KEY_1, True), '@': (e.KEY_2, True), '#': (e.KEY_3, True), '$': (e.KEY_4, True),
    '%': (e.KEY_5, True), '^': (e.KEY_6, True), '&': (e.KEY_7, True), '*': (e.KEY_8, True),
    '(': (e.KEY_9, True), ')': (e.KEY_0, True),
    ' ': (e.KEY_SPACE, False), '\n': (e.KEY_ENTER, False), '\t': (e.KEY_TAB, False),
    '-': (e.KEY_MINUS, False), '_': (e.KEY_MINUS, True), '=': (e.KEY_EQUAL, False), '+': (e.KEY_EQUAL, True),
    '[': (e.KEY_LEFTBRACE, False), ']': (e.KEY_RIGHTBRACE, False), '{': (e.KEY_LEFTBRACE, True), '}': (e.KEY_RIGHTBRACE, True),
    ';': (e.KEY_SEMICOLON, False), ':': (e.KEY_SEMICOLON, True), "'": (e.KEY_APOSTROPHE, False), '"': (e.KEY_APOSTROPHE, True),
    ',': (e.KEY_COMMA, False), '<': (e.KEY_COMMA, True), '.': (e.KEY_DOT, False), '>': (e.KEY_DOT, True),
    '/': (e.KEY_SLASH, False), '?': (e.KEY_SLASH, True), '\\': (e.KEY_BACKSLASH, False), '|': (e.KEY_BACKSLASH, True),
    '`': (e.KEY_GRAVE, False), '~': (e.KEY_GRAVE, True)
}


class LinuxInputInjector(BaseInputInjector):
    """Linux implementation of virtual keyboard input injection using evdev."""
    
    def __init__(self, device_name="Banao01 Virtual Keyboard"):
        capabilities = {
            e.EV_KEY: [
                # Include standard keys
                k for k, v in e.KEY.items() if k < 0x200
            ]
        }
        try:
            self.ui = UInput(capabilities, name=device_name)
            time.sleep(0.1)
        except Exception as err:
            raise PermissionError(
                f"Failed to initialize uinput virtual keyboard: {err}. "
                "Ensure that your user is added to the 'input' group, the udev rules "
                "for '/dev/uinput' are correctly configured, and you have logged "
                "out and back in to apply group changes."
            )

    def press_combo(self, keys):
        resolved_keys = []
        for key in keys:
            if isinstance(key, str):
                normalized = key.upper()
                if normalized in ("CTRL", "LCTRL", "LEFTCTRL"):
                    code = e.KEY_LEFTCTRL
                elif normalized in ("SHIFT", "LSHIFT", "LEFTSHIFT"):
                    code = e.KEY_LEFTSHIFT
                elif normalized in ("ALT", "LALT", "LEFTALT"):
                    code = e.KEY_LEFTALT
                elif normalized in ("SUPER", "META", "WIN", "LOGO"):
                    code = e.KEY_LEFTMETA
                else:
                    if not normalized.startswith("KEY_"):
                        normalized = "KEY_" + normalized
                    code = getattr(e, normalized, None)
                
                if code is None:
                    raise ValueError(f"Unknown key identifier: {key}")
                resolved_keys.append(code)
            elif isinstance(key, int):
                resolved_keys.append(key)
            else:
                raise TypeError(f"Invalid key type: {type(key)}")

        # 1. Press all keys down in sequence
        for code in resolved_keys:
            self.ui.write(e.EV_KEY, code, 1)
        self.ui.syn()

        time.sleep(0.015)

        # 2. Release all keys in reverse order
        for code in reversed(resolved_keys):
            self.ui.write(e.EV_KEY, code, 0)
        self.ui.syn()

    def type_string(self, text):
        for char in text:
            if char in _CHAR_TO_KEY:
                code, shift_required = _CHAR_TO_KEY[char]
                
                if shift_required:
                    self.ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)
                    self.ui.syn()
                
                self.ui.write(e.EV_KEY, code, 1)
                self.ui.syn()
                time.sleep(0.005)
                
                self.ui.write(e.EV_KEY, code, 0)
                self.ui.syn()
                
                if shift_required:
                    self.ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
                    self.ui.syn()
                
                time.sleep(0.005)
        self.ui.syn()

    def close(self):
        if hasattr(self, 'ui') and self.ui:
            self.ui.close()


def _matches_app_name(candidate, target):
    if not candidate or not target:
        return False
    cand = candidate.lower()
    tgt = target.lower()
    
    # Direct or substring match
    if tgt in cand or cand in tgt:
        return True
        
    import re
    # Helper to strip common prefixes and suffixes
    def clean(s):
        s = s.replace("google-", "").replace("google", "").replace("org.gnome.", "")
        if s.endswith(".desktop"):
            s = s[:-8]
        s = re.sub(r'[^a-z0-9]', '', s)
        return s
        
    c_clean = clean(cand)
    t_clean = clean(tgt)
    if not c_clean or not t_clean:
        return False
    return t_clean in c_clean or c_clean in t_clean


import threading

class LinuxAudioController(BaseAudioController):
    """Linux implementation of audio control using PipeWire-Pulse/PulseAudio (pulsectl)."""
    
    def __init__(self):
        self._pulse = pulsectl.Pulse('banao-utility')
        self._lock = threading.Lock()

    def get_master_volume(self):
        with self._lock:
            try:
                sink = self._pulse.sink_default_get()
                return sink.volume.value_flat
            except Exception as e:
                print(f"[LinuxAudio] Error getting master volume: {e}")
                return 0.0

    def set_master_volume(self, volume):
        with self._lock:
            try:
                sink = self._pulse.sink_default_get()
                volume = max(0.0, min(1.0, volume))
                self._pulse.volume_set_all_chans(sink, volume)
            except Exception as e:
                print(f"[LinuxAudio] Error setting master volume: {e}")

    def _find_app_sink_inputs(self, app_name):
        sink_inputs = []
        
        # Special fallback for Global / unknown app_name:
        # We target all active (uncorked) sink inputs. If none are active, we return all.
        if not app_name or app_name == "Global":
            active_inputs = []
            all_inputs = []
            with self._lock:
                try:
                    for si in self._pulse.sink_input_list():
                        all_inputs.append(si)
                        if not getattr(si, 'corked', False):
                            active_inputs.append(si)
                except Exception as e:
                    print(f"[LinuxAudio] Error listing sink inputs for Global: {e}")
            return active_inputs if active_inputs else all_inputs

        with self._lock:
            try:
                for si in self._pulse.sink_input_list():
                    props = si.proplist
                    candidates = [
                        props.get('application.name'),
                        props.get('application.process.binary'),
                        props.get('media.name'),
                        props.get('window.x11.class'),
                        props.get('window.class'),
                        props.get('window.instance'),
                        props.get('application.id'),
                        props.get('pipewire.access.portal.app_id')
                    ]
                    
                    for cand in candidates:
                        if cand and _matches_app_name(cand, app_name):
                            sink_inputs.append(si)
                            break
            except Exception as e:
                print(f"[LinuxAudio] Error listing sink inputs: {e}")
        return sink_inputs

    def get_app_volume(self, app_name):
        inputs = self._find_app_sink_inputs(app_name)
        if inputs:
            return inputs[0].volume.value_flat
        return None

    def set_app_volume(self, app_name, volume):
        volume = max(0.0, min(1.0, volume))
        inputs = self._find_app_sink_inputs(app_name)
        for si in inputs:
            with self._lock:
                try:
                    self._pulse.volume_set_all_chans(si, volume)
                except Exception as e:
                    print(f"[LinuxAudio] Error setting volume for sink-input {si.index}: {e}")


class LinuxActiveWindowDetector(BaseActiveWindowDetector):
    """Linux implementation of focused window class detection supporting GNOME Wayland & X11 fallback."""
    
    def __init__(self):
        try:
            self._bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except Exception as e:
            print(f"[LinuxWindow] Failed to connect to Session DBus: {e}")
            self._bus = None

    def get_active_window_class(self):
        # 1. Attempt to query standard GNOME extensions for window tracking under Wayland
        if self._bus:
            # Heuristic A: "Focused Window D-Bus" extension
            win = self._query_focused_window_extension()
            if win:
                return win
                
            # Heuristic B: "Window Calls" extension
            win = self._query_window_calls_extension()
            if win:
                return win

        # 2. Fallback for X11 / XWayland sessions (using xprop)
        if 'DISPLAY' in os.environ:
            win = self._query_x11_active_window()
            if win:
                return win

        # 3. Final fallback: Return generic target
        return "Global"

    def _query_focused_window_extension(self):
        """Query the popular 'Focused Window D-Bus' GNOME Shell extension."""
        try:
            result = self._bus.call_sync(
                'org.gnome.Shell',
                '/org/gnome/shell/extensions/FocusedWindow',
                'org.gnome.shell.extensions.FocusedWindow',
                'Get',
                None,
                GLib.VariantType('(s)'),
                Gio.DBusCallFlags.NONE,
                100,
                None
            )
            raw_val = result.get_child_value(0).get_string()
            data = json.loads(raw_val)
            wm_class = data.get('wm_class') or data.get('class')
            if wm_class:
                return wm_class.lower()
        except Exception:
            pass
        return None

    def _query_window_calls_extension(self):
        """Query the 'Window Calls' GNOME Shell extension."""
        try:
            result = self._bus.call_sync(
                'org.gnome.Shell',
                '/org/gnome/Shell/Extensions/Windows',
                'org.gnome.Shell.Extensions.Windows',
                'GetActive',
                None,
                GLib.VariantType('(s)'),
                Gio.DBusCallFlags.NONE,
                100,
                None
            )
            raw_val = result.get_child_value(0).get_string()
            data = json.loads(raw_val)
            wm_class = data.get('class') or data.get('wm_class')
            if wm_class:
                return wm_class.lower()
        except Exception:
            pass
        return None

    def _query_x11_active_window(self):
        """Fetch active window class via xprop subprocess (X11 / XWayland)."""
        try:
            focus_cmd = ["xprop", "-root", "_NET_ACTIVE_WINDOW"]
            focus_output = subprocess.check_output(focus_cmd, stderr=subprocess.DEVNULL).decode('utf-8')
            if "window id #" in focus_output:
                win_id = focus_output.split("window id #")[1].strip().split()[0]
                
                class_cmd = ["xprop", "-id", win_id, "WM_CLASS"]
                class_output = subprocess.check_output(class_cmd, stderr=subprocess.DEVNULL).decode('utf-8')
                if " = " in class_output:
                    parts = class_output.split(" = ")[1].replace('"', '').split(', ')
                    if parts:
                        return parts[0].strip().lower()
        except Exception:
            pass
        return None
