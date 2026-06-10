# src/ui/tray_helper.py
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
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, AyatanaAppIndicator3, GLib
import threading

def read_stdin():
    try:
        for line in sys.stdin:
            line = line.strip()
            if line == "QUIT":
                GLib.idle_add(Gtk.main_quit)
                break
    except Exception:
        pass
    GLib.idle_add(Gtk.main_quit)

def main():
    icon_name = "org.dietro.banao"
    if len(sys.argv) > 1:
        icon_name = sys.argv[1]
        
    indicator = AyatanaAppIndicator3.Indicator.new(
        "banao-indicator",
        icon_name,
        AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS
    )
    indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
    
    menu = Gtk.Menu()
    
    item_open = Gtk.MenuItem(label="Open Banao")
    item_open.connect("activate", lambda w: print("SHOW", flush=True))
    menu.append(item_open)
    
    item_sep = Gtk.SeparatorMenuItem()
    menu.append(item_sep)
    
    item_quit = Gtk.MenuItem(label="Quit")
    item_quit.connect("activate", lambda w: print("QUIT", flush=True))
    menu.append(item_quit)
    
    menu.show_all()
    indicator.set_menu(menu)
    
    t = threading.Thread(target=read_stdin, daemon=True)
    t.start()
    
    print("TRAY_READY", flush=True)
    Gtk.main()

if __name__ == "__main__":
    main()
