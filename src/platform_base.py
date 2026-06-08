# platform_base.py
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

class BaseInputInjector:
    """Abstract interface for simulating keystrokes and executing macros."""

    def press_combo(self, keys):
        """Presses and releases a combination of keys (e.g. Ctrl+Shift+Alt+T).

        Args:
            keys: List of key name strings or keycodes.
        """
        raise NotImplementedError

    def type_string(self, text):
        """Types out a string of characters sequentially.

        Args:
            text: String to type.
        """
        raise NotImplementedError

    def close(self):
        """Cleans up system resources associated with input simulation."""
        pass


class BaseAudioController:
    """Abstract interface for system and application volume control."""

    def get_master_volume(self):
        """Gets current master volume.

        Returns:
            Float representing master volume (0.0 to 1.0).
        """
        raise NotImplementedError

    def set_master_volume(self, volume):
        """Sets the system master volume.

        Args:
            volume: Float representing master volume (0.0 to 1.0).
        """
        raise NotImplementedError

    def get_app_volume(self, app_name):
        """Gets volume for a specific application.

        Args:
            app_name: String name of application (e.g. 'chrome', 'spotify').

        Returns:
            Float volume (0.0 to 1.0) or None if app stream is not found.
        """
        raise NotImplementedError

    def set_app_volume(self, app_name, volume):
        """Sets volume for a specific application's audio stream.

        Args:
            app_name: String name of application.
            volume: Float representing stream volume (0.0 to 1.0).
        """
        raise NotImplementedError


class BaseActiveWindowDetector:
    """Abstract interface for detecting the active window under focus."""

    def get_active_window_class(self):
        """Retrieves the window class or application name of the active window.

        Returns:
            String representing the focused window's application class (e.g. 'chrome', 'inkscape').
        """
        raise NotImplementedError
