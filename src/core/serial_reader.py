# serial_reader.py
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
import serial

class SerialReader(threading.Thread):
    """Monitors serial input from Arduino on a separate thread, auto-reconnecting on disconnect."""
    
    def __init__(self, port="/dev/ttyACM0", baudrate=115200, callback=None):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self.running = False
        self.serial_conn = None
        self.daemon = True # ensure thread dies when main app exits

    def run(self):
        self.running = True
        print(f"[Serial] Starting serial reader thread on {self.port} at {self.baudrate} baud...")
        
        while self.running:
            if self.serial_conn is None or not self.serial_conn.is_open:
                try:
                    # Attempt connection with a short timeout to prevent blocking during reconnects
                    self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1.0)
                    print(f"[Serial] Connected to macropad on {self.port}!")
                except (serial.SerialException, OSError) as e:
                    # Wait and retry connection
                    time.sleep(2.0)
                    continue
            
            try:
                line = self.serial_conn.readline()
                if line:
                    decoded = line.decode('utf-8', errors='ignore').strip()
                    if decoded:
                        parsed = self.parse_packet(decoded)
                        if parsed and self.callback:
                            self.callback(parsed)
            except (serial.SerialException, OSError) as e:
                print(f"[Serial] Connection lost: {e}. Attempting to reconnect...")
                self.close_serial()
                time.sleep(2.0)
            except Exception as e:
                print(f"[Serial] Error reading serial data: {e}")
                time.sleep(0.1)

        self.close_serial()

    def parse_packet(self, line):
        """Parses the raw line packet.
        
        Example packet: P1:512|P2:1023|B1:0|B2:1|B3:0|B4:0|B5:0|B6:0|B7:0|B8:0|E1:CW|EB:0
        """
        # Quick validation
        if "P1:" not in line or "P2:" not in line:
            return None
            
        parts = line.split('|')
        data = {}
        for part in parts:
            if ':' in part:
                key, val = part.split(':', 1)
                # Convert to integer if it is digital state or analog level
                if key == "E1":
                    data[key] = val  # e.g. 'CW', 'CCW', or 'NONE'
                else:
                    try:
                        data[key] = int(val)
                    except ValueError:
                        data[key] = val
        return data

    def close_serial(self):
        """Safely closes the serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except Exception:
                pass
        self.serial_conn = None

    def stop(self):
        """Stops the reader thread loop."""
        self.running = False
        self.close_serial()
