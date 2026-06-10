# Banao (DIY Macropad Controller & Daemon)

Banao is an open-source, highly responsive GUI companion application and background daemon for DIY custom macropads. 

Built using **GTK 4** and **Libadwaita**, Banao is designed for modern Linux desktops (specifically optimized for **Fedora 44 / GNOME Shell on Wayland**) to manage profiles, text macros, keyboard shortcuts, and dynamic audio routing directly from physical controls.

---

## Architecture & How It Works

```mermaid
graph TD
    subgraph Hardware (Arduino Leonardo)
        Keypresses[Direct Pins 5-15] -->|Serial /dev/ttyACM0| SerialReader
        Pot1[Pot 1 - Master Volume] -->|Analog A0| SerialReader
        Pot2[Pot 2 - App Volume] -->|Analog A1| SerialReader
    end

    subgraph Host Daemon (GTK 4 Process)
        SerialReader[Serial Reader Thread] -->|Raw Values| CoreEngine[Banao Core Engine]
        ActiveWin[Active Window Tracker] -->|App Class Context| CoreEngine
        CoreEngine -->|Map App Context| ProfileEngine[Profile & Key-Bindings Engine]
        ProfileEngine -->|Inject Keycodes| Evdev[evdev /dev/uinput Injector]
        ProfileEngine -->|PulseAudio API| PipeWire[PipeWire/PulseAudio Audio Controller]
        CoreEngine -.->|Communication Pipe| TrayHelper
    end

    subgraph UI & System (Separate Processes)
        GUI[GTK4 Libadwaita Config Window]
        TrayHelper[GTK3 AyatanaAppIndicator Subprocess]
    end

    GUI ---|Inter-process GLib Window Activation| CoreEngine
    TrayHelper ---|Top System Panel Indicator| CoreEngine
```

---

## Key Features

- **Decoupled Architecture**: High-speed Serial monitoring and Pulse/PipeWire audio tracking run on background threads, separating hardware latency from the GUI.
- **Dynamic Profile Switching**: Automatically detects the active focused application under GNOME Wayland and switches key bindings contextually.
- **Dual Potentiometer Mapping**:
  - **Potentiometer 1**: Tied to system Master Volume.
  - **Potentiometer 2**: Tied to the active audio output stream (e.g. Spotify, Firefox, VLC) of the currently focused application, falling back dynamically to Global settings.
- **Background Execution**: Closing the Libadwaita window merely hides it, keeping the background listener active.
- **System Tray Coordination**: Integrates a decoupled GTK3 helper process running `AyatanaAppIndicator3` to bypass PyGObject namespace clashes with GTK4.
- **Auto-Start Support**: Automatically generates desktop entries to launch hidden in the system tray (`--hidden` flag) on system login.

---

## Hardware Setup (Arduino Leonardo)

This macropad layout uses **direct pin connections** (no matrix) to eliminate button ghosting. 

- **Microcontroller**: Arduino Leonardo (or ATmega32U4 Pro Micro)
- **Direct Buttons**: Configured with `INPUT_PULLUP`. Connect buttons directly between ground (`GND`) and the following IO pins:
  - `5, 6, 7, 8, 9, 10, 14, 15`
- **Rotary Encoder**:
  - CW/CCW Pin: Pin `11` and `12`
  - Encoder Button: Pin `4`
- **Potentiometers**:
  - **Pot 1 (Master Volume)**: Analog Pin `A0`
  - **Pot 2 (Application Volume)**: Analog Pin `A1`
  - *Note: Firmware maps reversed direction scaling `(1023.0 - val) / 1023.0` to match standard clockwise increasing potentiometer mounts.*

The firmware source is available at `firmware/banao01_firmware/banao01_firmware.ino`.

---

## Software Dependencies

To run and build Banao on **Fedora 44 (GNOME)**, install the following:

### 1. Build & Core System Dependencies
```bash
sudo dnf install -y \
  meson \
  ninja-build \
  python3-devel \
  libadwaita-devel \
  gtk4-devel \
  libayatana-appindicator-gtk3
```

### 2. Python Dependencies
Ensure GObject introspection and other dependencies are present:
```bash
sudo dnf install -y \
  python3-gobject \
  python3-evdev \
  python3-serial \
  python3-pulsectl
```

### 3. GNOME System Tray Extension
GNOME Shell does not show tray icons natively. To display the status indicator in the top panel, install the AppIndicator extension:
```bash
sudo dnf install -y gnome-shell-extension-appindicator
```
> [!IMPORTANT]
> Because you are on Wayland, you **must log out and log back in** to reload GNOME Shell and detect this extension. After logging back in, enable it with:
> ```bash
> gnome-extensions enable appindicatorsupport@rgcjonas.gmail.com
> ```

### 4. uinput Permissions (For Keyboard Injection)
The daemon writes keystrokes via `/dev/uinput`. To run it without root permissions, you need to add your user to the `input` group and write a udev rule:
```bash
# Add yourself to the input and uucp (serial access) groups
sudo usermod -aG input,uucp $USER

# Set up udev rules for uinput access
echo 'KERNEL=="uinput", GROUP="input", MODE="0660", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/80-uinput.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```
*Note: You may need to restart your computer for group assignment changes to take effect.*

---

## Compilation, Installation & Run

We compile and deploy locally into your home prefix `~/.local` so it shows up in your application launchers (like AppEditor or Gnome Shell Application Menu) without cluttering system directories.

```bash
# 1. Clone the repository
git clone https://github.com/dietro/banao.git
cd banao

# 2. Configure the build
meson setup builddir --prefix=$HOME/.local

# 3. Compile resources
meson compile -C builddir

# 4. Install the package locally
meson install -C builddir
```

### How to Run
- **Standard execution** (Opens config GUI):
  ```bash
  banao
  ```
- **Daemon mode** (Starts hidden in the system tray directly):
  ```bash
  banao --hidden
  ```
- **Auto-start**: On the first launch, Banao will automatically create a startup entry at `~/.config/autostart/org.dietro.banao.desktop` to start background monitoring on login.

---

## Customization Guide

### Customizing Hardware Pins & Serial Mapping
If you choose to use a matrix layout or change buttons, modify:
1. **Firmware**: Open `firmware/banao01_firmware/banao01_firmware.ino` and modify the button/analog reads.
2. **Serial Reader**: Edit `src/core/serial_reader.py` to parse custom serial output codes.
3. **Engine Bindings**: Update key identifiers (e.g. `B1` to `B8`) in `src/core/engine.py` to match your button naming.

### Customizing Audio Backend
Banao uses `pulsectl` (PulseAudio / Pipewire interface) inside `src/adapters/linux.py` under the `LinuxAudioController` class. 
- To map Potentiometer 2 to specific channels or groups (e.g. specific game audio or discord rather than the active focused app stream), edit the active stream extraction code inside `LinuxAudioController.get_active_stream()`.
