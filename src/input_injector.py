# input_injector.py
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
import evdev
from evdev import UInput, ecodes as e

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


class InputInjector:
    """Creates a virtual keyboard using uinput and injects keystrokes at the kernel level."""

    def __init__(self, device_name="Banao01 Virtual Keyboard"):
        # We enable all standard keys and common modifier keys
        capabilities = {
            e.EV_KEY: [
                # Include standard keys
                k for k, v in e.KEY.items() if k < 0x200
            ]
        }
        try:
            self.ui = UInput(capabilities, name=device_name)
            # Give the system a brief moment to register the new device node
            time.sleep(0.1)
        except Exception as err:
            raise PermissionError(
                f"Failed to initialize uinput virtual keyboard: {err}. "
                "Ensure that your user is added to the 'input' group, the udev rules "
                "for '/dev/uinput' are correctly configured, and you have logged "
                "out and back in to apply group changes."
            )

    def close(self):
        """Clean up the uinput device."""
        if hasattr(self, 'ui') and self.ui:
            self.ui.close()

    def press_combo(self, keys):
        """Presses and releases a combination of keys (e.g., Ctrl+Shift+Alt+T).

        Args:
            keys: A list of key identifiers. Each item can be an integer keycode
                  (e.g., evdev.ecodes.KEY_LEFTCTRL) or a string key name
                  (e.g., 'KEY_LEFTCTRL', 'KEY_T', 'Ctrl', 'Shift', 'Alt', 'Super').
        """
        resolved_keys = []
        for key in keys:
            if isinstance(key, str):
                # Standardize common modifier short names
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
                    # Look up directly in evdev.ecodes
                    # Prepend KEY_ if it's missing (e.g., 'T' -> 'KEY_T')
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
            self.ui.write(e.EV_KEY, code, 1)  # 1 = Key Down
        self.ui.syn()

        # Brief delay to satisfy OS key-event handler thresholds
        time.sleep(0.015)

        # 2. Release all keys in reverse order
        for code in reversed(resolved_keys):
            self.ui.write(e.EV_KEY, code, 0)  # 0 = Key Up
        self.ui.syn()

    def type_string(self, text):
        """Types a string of text character-by-character.

        Args:
            text: String to type.
        """
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
            else:
                # Fallback for unmapped characters (just print a space or ignore)
                pass
        # Final sync just to be safe
        self.ui.syn()


# Example usage
if __name__ == "__main__":
    try:
        print("Initializing Virtual Keyboard...")
        injector = InputInjector()
        print("Virtual keyboard registered successfully!")

        # Test: Press Ctrl+Shift+Alt+T
        print("Testing keyboard injection: Ctrl+Shift+Alt+T in 3 seconds...")
        time.sleep(3)
        injector.press_combo(["KEY_LEFTCTRL", "KEY_LEFTSHIFT", "KEY_LEFTALT", "KEY_T"])
        print("Key combination sent.")

        # Test: Type string
        print("Testing text typing...")
        time.sleep(1)
        injector.type_string("git status\n")
        print("Typed: 'git status'")

        injector.close()
    except PermissionError as ex:
        print(ex)
    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")
