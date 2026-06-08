# platform_factory.py
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

import sys
from .platform_base import BaseInputInjector, BaseAudioController, BaseActiveWindowDetector


class MockInputInjector(BaseInputInjector):
    """Fallback Mock Input Injector for unsupported operating systems."""
    def press_combo(self, keys):
        print(f"[MockInput] Injected combo: {keys}")
    def type_string(self, text):
        print(f"[MockInput] Typed text: {text}")
    def close(self):
        pass


class MockAudioController(BaseAudioController):
    """Fallback Mock Audio Controller for unsupported operating systems."""
    def __init__(self):
        self._master = 0.5
        self._apps = {}
    def get_master_volume(self):
        return self._master
    def set_master_volume(self, volume):
        self._master = volume
        print(f"[MockAudio] Master volume set to {volume:.2f}")
    def get_app_volume(self, app_name):
        return self._apps.get(app_name, 0.5)
    def set_app_volume(self, app_name, volume):
        self._apps[app_name] = volume
        print(f"[MockAudio] App {app_name} volume set to {volume:.2f}")


class MockActiveWindowDetector(BaseActiveWindowDetector):
    """Fallback Mock Active Window Detector for unsupported operating systems."""
    def get_active_window_class(self):
        return "global"


def get_input_injector() -> BaseInputInjector:
    """Returns the input injector matching the current platform."""
    if sys.platform == 'linux':
        try:
            from .platform_linux import LinuxInputInjector
            return LinuxInputInjector()
        except Exception as e:
            print(f"[Factory] Warning: Failed to load Linux Input Injector: {e}")
    elif sys.platform == 'win32':
        # Developer placeholder:
        # from .platform_windows import WindowsInputInjector
        # return WindowsInputInjector()
        print("[Factory] Windows platform detected. Please implement platform_windows.py wrappers.")

    return MockInputInjector()


def get_audio_controller() -> BaseAudioController:
    """Returns the audio controller matching the current platform."""
    if sys.platform == 'linux':
        try:
            from .platform_linux import LinuxAudioController
            return LinuxAudioController()
        except Exception as e:
            print(f"[Factory] Warning: Failed to load Linux Audio Controller: {e}")
    elif sys.platform == 'win32':
        # Developer placeholder:
        # from .platform_windows import WindowsAudioController
        # return WindowsAudioController()
        print("[Factory] Windows platform detected. Please implement platform_windows.py wrappers.")

    return MockAudioController()


def get_active_window_detector() -> BaseActiveWindowDetector:
    """Returns the active window detector matching the current platform."""
    if sys.platform == 'linux':
        try:
            from .platform_linux import LinuxActiveWindowDetector
            return LinuxActiveWindowDetector()
        except Exception as e:
            print(f"[Factory] Warning: Failed to load Linux Active Window Detector: {e}")
    elif sys.platform == 'win32':
        # Developer placeholder:
        # from .platform_windows import WindowsActiveWindowDetector
        # return WindowsActiveWindowDetector()
        print("[Factory] Windows platform detected. Please implement platform_windows.py wrappers.")

    return MockActiveWindowDetector()
