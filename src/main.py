# main.py
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
import os
import subprocess
import threading
import gi

from gettext import gettext as _

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw, GLib
from .ui import BanaoWindow


class BanaoApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='org.dietro.banao',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
                         resource_base_path='/org/dietro/banao')
        self.create_action('quit', self.on_quit, ['<control>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)
        self.engine = None
        self.win = None
        self.tray_process = None

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        # Instantiate and start the BanaoEngine on activation
        if not self.engine:
            from .adapters import factory
            from .core.engine import BanaoEngine
            
            # Retrieve decoupled OS adapters
            input_injector = factory.get_input_injector()
            audio_controller = factory.get_audio_controller()
            window_detector = factory.get_active_window_detector()
            
            # Inject dependencies into core engine
            self.engine = BanaoEngine(input_injector, audio_controller, window_detector)
            self.engine.start()

        # Start tray helper if not already running
        if not self.tray_process:
            self._start_tray_helper()

        if not self.win:
            self.win = BanaoWindow(application=self)
        self.win.present()

    def _start_tray_helper(self):
        # Resolve tray_helper.py location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        tray_helper_path = os.path.join(current_dir, 'ui', 'tray_helper.py')
        
        # Resolve icon path
        icon_path = 'org.dietro.banao'
        
        # 1. Try directory relative to main.py for development
        dev_icon_path = os.path.abspath(os.path.join(current_dir, '..', 'data', 'icons', 'hicolor', '256x256', 'apps', 'org.dietro.banao.png'))
        if os.path.exists(dev_icon_path):
            icon_path = dev_icon_path
        else:
            # 2. Try relative to package directory if installed
            # Search under ~/.local/share/icons and /usr/share/icons
            search_dirs = [
                os.path.expanduser('~/.local/share/icons'),
                '/usr/share/icons',
                '/usr/local/share/icons',
            ]
            for sdir in search_dirs:
                ipath = os.path.join(sdir, 'hicolor', '256x256', 'apps', 'org.dietro.banao.png')
                if os.path.exists(ipath):
                    icon_path = ipath
                    break
        
        print(f"[Main] Spawning tray helper with icon {icon_path} from {tray_helper_path}", flush=True)
        try:
            self.tray_process = subprocess.Popen(
                [sys.executable, tray_helper_path, icon_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            threading.Thread(target=self._read_tray_stdout, daemon=True).start()
        except Exception as e:
            print(f"[Main] Failed to start tray helper: {e}", flush=True)

    def _read_tray_stdout(self):
        try:
            for line in self.tray_process.stdout:
                line = line.strip()
                if line == "SHOW":
                    GLib.idle_add(self._present_window)
                elif line == "QUIT":
                    GLib.idle_add(self.quit)
        except Exception as e:
            print(f"[Main] Error reading from tray helper: {e}", flush=True)

    def _present_window(self):
        if self.win:
            self.win.present()

    def do_shutdown(self):
        """Called when the application is shutting down. Clean up background threads."""
        if hasattr(self, 'engine') and self.engine:
            self.engine.stop()
        if hasattr(self, 'tray_process') and self.tray_process:
            try:
                self.tray_process.stdin.write("QUIT\n")
                self.tray_process.stdin.flush()
                self.tray_process.terminate()
                self.tray_process.wait(timeout=1)
            except Exception:
                pass
        Adw.Application.do_shutdown(self)

    def on_quit(self, *args):
        self.quit()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(application_name='Banao',
                                application_icon='org.dietro.banao',
                                developer_name='Bhawesh Kumar',
                                version='0.1.0',
                                # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
                                translator_credits = _('translator-credits'),
                                developers=['Bhawesh Kumar'],
                                copyright='© 2026 Bhawesh Kumar')
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        print('app.preferences action activated')

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = BanaoApplication()
    return app.run(sys.argv)
