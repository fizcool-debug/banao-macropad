# window.py
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

import json
import re
from gi.repository import Adw, Gtk, Gdk, GLib, Gio

# Custom CSS data for premium techwear/speculative hardware layout aesthetic
CSS_STYLING = """
.hardware-card {
    background-color: #171c26;
    border: 1px solid #2c354a;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.dial-container {
    background: #0f121a;
    border: 1px solid #232a3b;
    border-radius: 12px;
    padding: 16px;
    box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.6);
}

.dial-title {
    font-size: 10px;
    font-weight: 800;
    color: #a0aec0;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.keycap-button {
    background: linear-gradient(135deg, #252d3e, #131722);
    border: 1px solid #36425c;
    border-radius: 10px;
    padding: 10px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    transition: all 0.2s ease-in-out;
}

.keycap-button:hover {
    border-color: #00f2fe;
    box-shadow: 0 0 12px rgba(0, 242, 254, 0.4);
}

.keycap-button.selected-keycap {
    border-color: #00f2fe;
    background: linear-gradient(135deg, #1b3a57, #0b1a29);
    box-shadow: 0 0 16px rgba(0, 242, 254, 0.7);
}

.keycap-button.hardware-pressed {
    background: #0d3a1f;
    border-color: #38bdf8;
    color: #4ade80;
    box-shadow: 0 0 20px rgba(74, 222, 128, 0.8);
    transform: scale(0.95);
}

.circular.keycap-button {
    border-radius: 9999px;
}

.neon-cyan {
    color: #00f2fe;
    text-shadow: 0 0 8px rgba(0, 242, 254, 0.6);
}

.neon-amber {
    color: #fbbf24;
    text-shadow: 0 0 8px rgba(251, 191, 36, 0.6);
}

.neon-green {
    color: #4ade80;
    text-shadow: 0 0 8px rgba(74, 222, 128, 0.6);
}

/* Custom styles for LevelBars */
levelbar.pot-level-master block.filled {
    background-color: #00f2fe;
    box-shadow: 0 0 8px rgba(0, 242, 254, 0.8);
    border-radius: 3px;
}

levelbar.pot-level-app block.filled {
    background-color: #fbbf24;
    box-shadow: 0 0 8px rgba(251, 191, 36, 0.8);
    border-radius: 3px;
}

levelbar block.empty {
    background-color: #1a202c;
    border-radius: 3px;
}
"""


def parse_user_shortcut(text):
    """Parses a friendly string like 'Ctrl+Alt+T' or 'ctrl,alt,t'
    and returns a list of evdev key names like ['KEY_LEFTCTRL', 'KEY_LEFTALT', 'KEY_T'].
    """
    if not text:
        return []
    normalized = text.replace("+", ",").replace(" ", ",")
    parts = [p.strip().upper() for p in normalized.split(",") if p.strip()]
    
    mapping = {
        "CTRL": "KEY_LEFTCTRL", "LCTRL": "KEY_LEFTCTRL", "RCTRL": "KEY_RIGHTCTRL", "CONTROL": "KEY_LEFTCTRL",
        "ALT": "KEY_LEFTALT", "LALT": "KEY_LEFTALT", "RALT": "KEY_RIGHTALT",
        "SHIFT": "KEY_LEFTSHIFT", "LSHIFT": "KEY_LEFTSHIFT", "RSHIFT": "KEY_RIGHTSHIFT",
        "SUPER": "KEY_LEFTMETA", "META": "KEY_LEFTMETA", "WIN": "KEY_LEFTMETA", "WINDOWS": "KEY_LEFTMETA",
        "CMD": "KEY_LEFTMETA", "COMMAND": "KEY_LEFTMETA",
        "ENTER": "KEY_ENTER", "RETURN": "KEY_ENTER",
        "ESC": "KEY_ESC", "ESCAPE": "KEY_ESC",
        "TAB": "KEY_TAB", "SPACE": "KEY_SPACE",
        "BACKSPACE": "KEY_BACKSPACE", "DEL": "KEY_DELETE", "DELETE": "KEY_DELETE",
        "UP": "KEY_UP", "DOWN": "KEY_DOWN", "LEFT": "KEY_LEFT", "RIGHT": "KEY_RIGHT",
        "PGUP": "KEY_PAGEUP", "PAGEUP": "KEY_PAGEUP", "PGDN": "KEY_PAGEDOWN", "PAGEDOWN": "KEY_PAGEDOWN",
        "HOME": "KEY_HOME", "END": "KEY_END", "INSERT": "KEY_INSERT",
        "MUTE": "KEY_MUTE", "VOLUP": "KEY_VOLUMEUP", "VOLDOWN": "KEY_VOLUMEDOWN",
        "PLAY": "KEY_PLAYPAUSE", "PAUSE": "KEY_PLAYPAUSE", "PLAYPAUSE": "KEY_PLAYPAUSE",
        "NEXT": "KEY_NEXTSONG", "PREV": "KEY_PREVIOUSSONG",
    }
    
    result = []
    for part in parts:
        if part in mapping:
            result.append(mapping[part])
        elif part.startswith("KEY_"):
            result.append(part)
        else:
            result.append(f"KEY_{part}")
    return result


def to_friendly_shortcut(keys_list):
    if not keys_list:
        return ""
    
    rev_mapping = {
        "KEY_LEFTCTRL": "Ctrl", "KEY_RIGHTCTRL": "Ctrl",
        "KEY_LEFTALT": "Alt", "KEY_RIGHTALT": "Alt",
        "KEY_LEFTSHIFT": "Shift", "KEY_RIGHTSHIFT": "Shift",
        "KEY_LEFTMETA": "Super",
        "KEY_ENTER": "Enter", "KEY_ESC": "Esc", "KEY_TAB": "Tab", "KEY_SPACE": "Space",
        "KEY_BACKSPACE": "Backspace", "KEY_DELETE": "Delete",
        "KEY_UP": "Up", "KEY_DOWN": "Down", "KEY_LEFT": "Left", "KEY_RIGHT": "Right",
        "KEY_PAGEUP": "PgUp", "KEY_PAGEDOWN": "PgDn", "KEY_HOME": "Home", "KEY_END": "End",
        "KEY_VOLUMEUP": "Vol+", "KEY_VOLUMEDOWN": "Vol-", "KEY_MUTE": "Mute",
        "KEY_PLAYPAUSE": "Play/Pause", "KEY_NEXTSONG": "Next", "KEY_PREVIOUSSONG": "Prev"
    }
    
    friendly_parts = []
    for key in keys_list:
        if key in rev_mapping:
            friendly_parts.append(rev_mapping[key])
        elif key.startswith("KEY_"):
            friendly_parts.append(key[4:].title())
        else:
            friendly_parts.append(str(key))
            
    return "+".join(friendly_parts)


@Gtk.Template(resource_path='/org/dietro/banao/window.ui')
class BanaoWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'BanaoWindow'

    # Template widgets
    split_view = Gtk.Template.Child()
    profile_list_box = Gtk.Template.Child()
    auto_switch = Gtk.Template.Child()
    add_profile_btn = Gtk.Template.Child()
    active_profile_header_label = Gtk.Template.Child()
    pot1_level = Gtk.Template.Child()
    pot1_val_label = Gtk.Template.Child()
    pot2_level = Gtk.Template.Child()
    pot2_val_label = Gtk.Template.Child()
    encoder_btn = Gtk.Template.Child()
    encoder_ccw_btn = Gtk.Template.Child()
    encoder_cw_btn = Gtk.Template.Child()
    button_grid = Gtk.Template.Child()
    config_panel_title = Gtk.Template.Child()
    form_box = Gtk.Template.Child()
    label_entry = Gtk.Template.Child()
    action_type_dropdown = Gtk.Template.Child()
    shortcut_config_box = Gtk.Template.Child()
    shortcut_entry = Gtk.Template.Child()
    cheatsheet_btn = Gtk.Template.Child()
    text_config_box = Gtk.Template.Child()
    text_entry = Gtk.Template.Child()
    save_binding_btn = Gtk.Template.Child()
    focused_app_status_label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Load theme stylesheet
        self._load_custom_css()
        
        # Force system dark mode preference for Libadwaita cohesive rendering
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.PREFER_DARK)
        
        # Retrieve Core Engine from App singleton
        self.app = self.get_application()
        self.engine = self.app.engine
        
        # State tracking
        self.selected_control_id = None
        self.grid_buttons = {}
        
        # Set window base CSS class
        self.add_css_class("banao-window")
        
        # Initialize components
        self._setup_action_type_dropdown()
        self._setup_hardware_grid()
        self._setup_event_handlers()
        
        # Sync auto switch switch UI state
        self.auto_switch.set_active(self.engine.auto_profile_switching)
        
        # Initial populate
        self._populate_profile_sidebar()
        self._load_active_profile_config()
        
        # Register core engine callbacks (marshaled to UI thread context via GLib.idle_add)
        self.engine.register_callback("state_updated", self._on_hardware_state_updated)
        self.engine.register_callback("profile_changed", self._on_hardware_profile_changed)
        self.engine.register_callback("window_changed", self._on_hardware_window_changed)

    def _load_custom_css(self):
        """Injects custom CSS provider into the display context."""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS_STYLING.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _setup_action_type_dropdown(self):
        """Constructs and populates the dropdown model."""
        string_list = Gtk.StringList.new(["Keyboard Shortcut", "Text Macro", "None"])
        self.action_type_dropdown.set_model(string_list)

    def _setup_hardware_grid(self):
        """Programmatically instantiates the 3x3 switch grid on the card visualizer."""
        # Row, Col, and Button ID matching the physical grid coordinates
        # Bottom-left (Row 2, Col 0) is omitted for encoder dial space
        grid_layout = [
            (0, 0, "B1"), (0, 1, "B2"), (0, 2, "B3"),
            (1, 0, "B4"), (1, 1, "B5"), (1, 2, "B6"),
            (2, 1, "B7"), (2, 2, "B8")
        ]
        
        for row, col, btn_id in grid_layout:
            btn = Gtk.Button()
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            box.set_valign(Gtk.Align.CENTER)
            box.set_halign(Gtk.Align.CENTER)
            
            # Switch label (e.g. B1)
            lbl_id = Gtk.Label(label=btn_id)
            lbl_id.add_css_class("caption")
            lbl_id.add_css_class("neon-cyan")
            
            # Binding value description
            lbl_binding = Gtk.Label(label="None")
            lbl_binding.add_css_class("caption")
            lbl_binding.add_css_class("dim-label")
            lbl_binding.set_ellipsize(3) # End ellipsize
            lbl_binding.set_max_width_chars(10)
            
            box.append(lbl_id)
            box.append(lbl_binding)
            btn.set_child(box)
            
            btn.set_size_request(85, 85)
            btn.add_css_class("keycap-button")
            
            # Attach to GtkGrid (col, row, width, height)
            self.button_grid.attach(btn, col, row, 1, 1)
            
            # Store widgets for updates
            self.grid_buttons[btn_id] = {
                "button": btn,
                "label": lbl_binding
            }
            
            # Connect binding click editor
            btn.connect("clicked", self._on_control_selected_clicked, btn_id)

    def _setup_event_handlers(self):
        """Binds signals for UI controls."""
        self.connect("close-request", self._on_close_request)
        self.profile_list_box.connect("row-selected", self._on_sidebar_profile_selected)
        self.add_profile_btn.connect("clicked", self._on_add_profile_btn_clicked)
        self.action_type_dropdown.connect("notify::selected", self._on_action_type_changed)
        self.save_binding_btn.connect("clicked", self._on_save_binding_clicked)
        self.auto_switch.connect("notify::active", self._on_auto_switch_toggled)
        
        # Connect dials to config
        self.encoder_btn.connect("clicked", self._on_control_selected_clicked, "EB")
        self.encoder_ccw_btn.connect("clicked", self._on_control_selected_clicked, "E1_CCW")
        self.encoder_cw_btn.connect("clicked", self._on_control_selected_clicked, "E1_CW")
        
        # Connect cheatsheet button
        self.cheatsheet_btn.connect("clicked", self._on_cheatsheet_clicked)

    def _on_close_request(self, window):
        self.hide()
        return True

    def _on_cheatsheet_clicked(self, button):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Keycode Cheatsheet",
            body="Below are common codes you can use for keyboard shortcuts:\n\n"
                 "• Media Actions:\n"
                 "  KEY_PLAYPAUSE (Play/Pause)\n"
                 "  KEY_NEXTSONG (Next Track)\n"
                 "  KEY_PREVIOUSSONG (Previous Track)\n"
                 "  KEY_MUTE (Mute Audio)\n"
                 "  KEY_VOLUMEUP (Volume Up)\n"
                 "  KEY_VOLUMEDOWN (Volume Down)\n\n"
                 "• Modifier Keys:\n"
                 "  KEY_LEFTCTRL, KEY_LEFTALT, KEY_LEFTSHIFT, KEY_LEFTMETA (Super/Win)\n\n"
                 "• Common Keys:\n"
                 "  KEY_ENTER, KEY_ESC, KEY_TAB, KEY_SPACE, KEY_BACKSPACE, KEY_DELETE\n\n"
                 "• Navigation & Arrows:\n"
                 "  KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_PAGEUP, KEY_PAGEDOWN\n\n"
                 "• Standard Letters & Numbers:\n"
                 "  KEY_A to KEY_Z, KEY_0 to KEY_9\n\n"
                 "Note: Key combos should be separated by commas (e.g., KEY_LEFTCTRL, KEY_T)."
        )
        dialog.add_response("close", "Close")
        dialog.set_default_response("close")
        dialog.set_close_response("close")
        dialog.present()

    def _on_auto_switch_toggled(self, switch, pspec):
        active = switch.get_active()
        self.engine.auto_profile_switching = active
        print(f"[UI] Auto profile switching toggled: {active}")

    # --- Profile Sidebar List Management ---

    def _populate_profile_sidebar(self):
        """Clears and rebuilds the profiles list inside the navigation sidebar."""
        # Clean current rows
        while True:
            row = self.profile_list_box.get_row_at_index(0)
            if not row:
                break
            self.profile_list_box.remove(row)
            
        profiles = self.engine.profile_engine.profiles
        for name, data in profiles.items():
            row = Adw.ActionRow.new()
            row.set_title(name)
            app_class = data.get("app_class", "")
            if app_class:
                row.set_subtitle(f"Target: {app_class}")
            else:
                row.set_subtitle("Global defaults")
                
            # Allow deletion of non-fallback profiles
            if name != "Global":
                del_btn = Gtk.Button.new_from_icon_name("user-trash-symbolic")
                del_btn.add_css_class("flat")
                del_btn.set_valign(Gtk.Align.CENTER)
                del_btn.connect("clicked", self._on_delete_profile_clicked, name)
                row.add_suffix(del_btn)
                
            self.profile_list_box.append(row)

    def _on_sidebar_profile_selected(self, list_box, row):
        if not row:
            return
        profile_name = row.get_title()
        
        # Load local profile state
        self.engine.active_profile_name = profile_name
        self.engine.active_profile = self.engine.profile_engine.profiles[profile_name]
        self._load_active_profile_config()

    def _on_add_profile_btn_clicked(self, btn):
        """Displays selection dialog of installed apps to create a new profile."""
        def on_app_selected(name, app_class):
            if name:
                try:
                    self.engine.profile_engine.add_profile(name, app_class)
                    self._populate_profile_sidebar()
                except Exception as e:
                    print(f"Error adding profile: {e}")
                    
        dialog = AppSelectionDialog(self, on_app_selected)
        dialog.present()

    def _on_delete_profile_clicked(self, btn, name):
        try:
            self.engine.profile_engine.delete_profile(name)
            # If deleted the currently viewed profile, return to Global
            if self.engine.active_profile_name == name:
                self.engine.active_profile_name = "Global"
                self.engine.active_profile = self.engine.profile_engine.profiles["Global"]
            self._populate_profile_sidebar()
            self._load_active_profile_config()
        except Exception as e:
            print(f"Error deleting profile: {e}")

    # --- Config Form Rendering and Actions ---

    def _load_active_profile_config(self):
        """Updates the window title, status bars, and reload visual keycap labels."""
        profile_name = self.engine.active_profile_name
        self.active_profile_header_label.set_label(f"Profile: {profile_name}")
        
        # Reload grid button subtitles
        bindings = self.engine.active_profile.get("bindings", {})
        
        # Reset and reload button labels
        for btn_id, refs in self.grid_buttons.items():
            binding = bindings.get(btn_id)
            if binding and binding.get("type") != "none":
                refs["label"].set_label(binding.get("label") or binding.get("type"))
                refs["label"].remove_css_class("dim-label")
                refs["label"].add_css_class("neon-green")
            else:
                refs["label"].set_label("None")
                refs["label"].remove_css_class("neon-green")
                refs["label"].add_css_class("dim-label")
                
        # Close binding editor panel if open
        self.form_box.set_sensitive(False)
        self.config_panel_title.set_label("Select a key to configure")
        self.selected_control_id = None
        
        # Clear selected visual state
        for ref in self.grid_buttons.values():
            ref["button"].remove_css_class("selected-keycap")
        self.encoder_btn.remove_css_class("selected-keycap")
        self.encoder_ccw_btn.remove_css_class("selected-keycap")
        self.encoder_cw_btn.remove_css_class("selected-keycap")

    def _on_control_selected_clicked(self, btn, control_id):
        """Pulls up the binding configuration editor for the selected hardware control."""
        self.selected_control_id = control_id
        
        friendly_names = {
            "EB": "Encoder Push (EB)",
            "E1_CW": "Encoder Rotate CW (↻)",
            "E1_CCW": "Encoder Rotate CCW (↺)",
        }
        friendly_name = f"Button {control_id}" if control_id.startswith("B") else friendly_names.get(control_id, control_id)
        self.config_panel_title.set_label(f"Configure {friendly_name}")
        self.form_box.set_sensitive(True)
        
        # Clear selected class from all keycap buttons
        for ref in self.grid_buttons.values():
            ref["button"].remove_css_class("selected-keycap")
        self.encoder_btn.remove_css_class("selected-keycap")
        self.encoder_ccw_btn.remove_css_class("selected-keycap")
        self.encoder_cw_btn.remove_css_class("selected-keycap")
        
        # Add selected class to the clicked button
        if control_id in self.grid_buttons:
            self.grid_buttons[control_id]["button"].add_css_class("selected-keycap")
        elif control_id == "EB":
            self.encoder_btn.add_css_class("selected-keycap")
        elif control_id == "E1_CCW":
            self.encoder_ccw_btn.add_css_class("selected-keycap")
        elif control_id == "E1_CW":
            self.encoder_cw_btn.add_css_class("selected-keycap")
        
        # Retrieve current binding values
        bindings = self.engine.active_profile.get("bindings", {})
        binding = bindings.get(control_id, {"type": "none", "value": None, "label": ""})
        
        # Load form elements
        self.label_entry.set_text(binding.get("label", ""))
        
        btype = binding.get("type", "none")
        val = binding.get("value")
        
        if btype == "shortcut":
            self.action_type_dropdown.set_selected(0)
            self.shortcut_entry.set_text(to_friendly_shortcut(val) if val else "")
            self.text_entry.set_text("")
        elif btype == "text":
            self.action_type_dropdown.set_selected(1)
            self.text_entry.set_text(val if val else "")
            self.shortcut_entry.set_text("")
        else:
            self.action_type_dropdown.set_selected(2)
            self.shortcut_entry.set_text("")
            self.text_entry.set_text("")
            
        self._update_form_visibility(btype)

    def _on_action_type_changed(self, dropdown, spec):
        """Adjusts visibility fields dynamically based on the dropdown selection."""
        idx = dropdown.get_selected()
        if idx == 0:
            self._update_form_visibility("shortcut")
        elif idx == 1:
            self._update_form_visibility("text")
        else:
            self._update_form_visibility("none")

    def _update_form_visibility(self, action_type):
        self.shortcut_config_box.set_visible(action_type == "shortcut")
        self.text_config_box.set_visible(action_type == "text")

    def _on_save_binding_clicked(self, btn):
        """Saves configured values back to the active profile JSON mapping."""
        if not self.selected_control_id:
            return
            
        label = self.label_entry.get_text().strip()
        idx = self.action_type_dropdown.get_selected()
        
        action_type = "none"
        val = None
        
        if idx == 0:
            action_type = "shortcut"
            raw_val = self.shortcut_entry.get_text().strip()
            # Convert friendly/raw string to list of keys
            val = parse_user_shortcut(raw_val)
        elif idx == 1:
            action_type = "text"
            val = self.text_entry.get_text() # keep escaping like \n
            
        # Auto-generate a descriptive label if left blank
        if not label:
            if action_type == "shortcut" and val:
                label = to_friendly_shortcut(val)
            elif action_type == "text" and val:
                label = val[:12] + "..." if len(val) > 12 else val
            else:
                label = ""

        # Update config in engine
        profile_name = self.engine.active_profile_name
        self.engine.profile_engine.update_binding(
            profile_name, 
            self.selected_control_id, 
            action_type, 
            val, 
            label
        )
        
        # Reload GUI
        self._load_active_profile_config()

    # --- Core Engine Callbacks (Marshaled to Main GLib loop context) ---

    def _on_hardware_state_updated(self, packet):
        GLib.idle_add(self._update_ui_hardware_state, packet)

    def _on_hardware_profile_changed(self, profile_name, profile_data):
        GLib.idle_add(self._update_ui_active_profile, profile_name, profile_data)

    def _on_hardware_window_changed(self, window_class):
        GLib.idle_add(self._update_ui_focused_window, window_class)

    def _update_ui_hardware_state(self, packet):
        """Updates UI visual states (slider volume progress, keypress highlights)."""
        # 1. Update Master Volume level (P1)
        if "P1" in packet:
            val_p1 = packet["P1"]
            pct_p1 = ((1023.0 - val_p1) / 1023.0) * 100.0
            self.pot1_level.set_value(pct_p1)
            self.pot1_val_label.set_label(f"{int(pct_p1)}%")
            
        # 2. Update Active App Volume level (P2)
        if "P2" in packet:
            val_p2 = packet["P2"]
            pct_p2 = ((1023.0 - val_p2) / 1023.0) * 100.0
            self.pot2_level.set_value(pct_p2)
            self.pot2_val_label.set_label(f"{int(pct_p2)}%")
            
        # 3. Update mechanical switches highlights (B1-B8)
        for i in range(1, 9):
            btn_id = f"B{i}"
            if btn_id in packet:
                state = packet[btn_id]
                ref = self.grid_buttons.get(btn_id)
                if ref:
                    if state == 1:
                        ref["button"].add_css_class("hardware-pressed")
                    else:
                        ref["button"].remove_css_class("hardware-pressed")
                        
        # 4. Update encoder button highlight (EB)
        if "EB" in packet:
            eb_state = packet["EB"]
            if eb_state == 1:
                self.encoder_btn.add_css_class("hardware-pressed")
            else:
                self.encoder_btn.remove_css_class("hardware-pressed")

        # 5. Handle transient Encoder rotates (E1)
        if "E1" in packet:
            rot_dir = packet["E1"]
            if rot_dir == "CW":
                self.encoder_cw_btn.add_css_class("hardware-pressed")
                GLib.timeout_add(150, lambda: self.encoder_cw_btn.remove_css_class("hardware-pressed") or False)
            elif rot_dir == "CCW":
                self.encoder_ccw_btn.add_css_class("hardware-pressed")
                GLib.timeout_add(150, lambda: self.encoder_ccw_btn.remove_css_class("hardware-pressed") or False)

    def _update_ui_active_profile(self, profile_name, profile_data):
        """Handles profile changes pushed by active window focus changes."""
        # Find row in sidebar listbox and select it
        i = 0
        while True:
            row = self.profile_list_box.get_row_at_index(i)
            if not row:
                break
            if row.get_title() == profile_name:
                self.profile_list_box.select_row(row)
                break
            i += 1
        
        # Load local configuration mapping
        self.active_profile_header_label.set_label(f"Profile: {profile_name}")
        self._load_active_profile_config()

    def _update_ui_focused_window(self, window_class):
        """Updates bottom window status bar."""
        self.focused_app_status_label.set_label(f"Focused Application: {window_class}")


class AppSelectionDialog(Gtk.Window):
    def __init__(self, parent_window, on_app_selected):
        super().__init__(
            title="Add Application Profile",
            transient_for=parent_window,
            modal=True,
            default_width=450,
            default_height=550
        )
        self.on_app_selected = on_app_selected
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        
        # Search Entry
        self.search_entry = Gtk.SearchEntry(placeholder_text="Search installed applications...")
        self.search_entry.connect("search-changed", self._on_search_changed)
        main_box.append(self.search_entry)
        
        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_propagate_natural_width(True)
        scrolled.set_min_content_height(400)
        
        # List box
        self.list_box = Gtk.ListBox()
        self.list_box.add_css_class("boxed-list")
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.set_activate_on_single_click(True)
        self.list_box.connect("row-activated", self._on_row_activated)
        scrolled.set_child(self.list_box)
        main_box.append(scrolled)
        
        self.set_child(main_box)
        
        # Fetch and filter apps
        self.all_apps = []
        for app in Gio.AppInfo.get_all():
            if app.should_show():
                self.all_apps.append(app)
                
        # Sort alphabetically
        self.all_apps.sort(key=lambda a: a.get_name().lower())
        
        self._populate_list("")

    def _populate_list(self, filter_text):
        # Clear existing
        while True:
            row = self.list_box.get_row_at_index(0)
            if not row:
                break
            self.list_box.remove(row)
            
        filter_text = filter_text.lower()
        for app in self.all_apps:
            name = app.get_name()
            app_id = app.get_id() or ""
            
            if filter_text and filter_text not in name.lower() and filter_text not in app_id.lower():
                continue
                
            row = Adw.ActionRow.new()
            row.set_title(name)
            
            window_class = app_id.replace(".desktop", "").lower()
            row.set_subtitle(f"Class: {window_class}")
            
            gicon = app.get_icon()
            if gicon:
                img = Gtk.Image.new_from_gicon(gicon)
                img.set_pixel_size(32)
                row.add_prefix(img)
            else:
                img = Gtk.Image.new_from_icon_name("application-x-executable")
                img.set_pixel_size(32)
                row.add_prefix(img)
                
            row.app_data = {
                "name": name,
                "class": window_class
            }
            self.list_box.append(row)

    def _on_search_changed(self, entry):
        self._populate_list(entry.get_text())

    def _on_row_activated(self, list_box, row):
        if row and hasattr(row, "app_data"):
            self.on_app_selected(row.app_data["name"], row.app_data["class"])
            self.destroy()
