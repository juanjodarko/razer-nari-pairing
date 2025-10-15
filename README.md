# Razer Nari Wireless Pairing Tool

Open-source tool to pair Razer Nari headsets with their USB dongles on **Linux** - no Razer software required!

## What This Does

Pairs any Razer Nari headset variant with any Razer Nari dongle variant, bypassing Razer's artificial restrictions.

**Supported Hardware:**

- Razer Nari Ultimate **NOT TESTED** (likely works, needs verification)
- Razer Nari (Regular) **TESTED** (confirmed working)
- Razer Nari Essential **NOT TESTED** (likely works, needs verification)

**Note**: The pairing command was extracted from Razer's official utility which supports all Nari variants, and cross-model pairing has been confirmed working (Regular + Ultimate dongle). However, Ultimate and Essential models have not been directly tested yet. If you have these models, please test and report your results!

## Quick Start

### Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Requirements

1. **Python 3.7+**
2. **PyUSB library**:
   ```bash
   pip install pyusb
   ```
3. **USB charging cable** for your headset
4. **Root/sudo access** (for USB control)

### Pairing Process

1. **Connect both devices**:
   - Plug dongle into USB port
   - Connect headset via USB charging cable
   - Turn ON the headset (press power button)

2. **Run the pairing tool**:

   ```bash
   ./pair.sh
   ```

   Or directly:

   ```bash
   sudo python3 razer_nari_pair.py
   ```

3. **Follow on-screen instructions**:
   - Tool sends pairing commands to both devices
   - Devices exchange pairing data
   - Wait 5 seconds

4. **Test wireless connection**:
   - Disconnect headset USB cable
   - Turn headset OFF then ON
   - Headset should connect wirelessly!

### Expected Result

- Headset LED: **Solid blue then disappears** (connected)
- Sound: **Connection tone** in headset
- Audio: **Works wirelessly!**
- **Pairing is permanent** - they remember each other forever! (so far)

## What's Next?

After pairing your headset:

### Audio Configuration (Important!)

The Razer Nari has dual audio outputs (Game stereo + Chat mono). For best audio quality, you'll need proper audio profiles:

**For PulseAudio:**

- [razer-nari-pulseaudio-profile](https://github.com/imustafin/razer-nari-pulseaudio-profile) - Enables both Game and Chat outputs
- Arch Linux: Install from [AUR](https://aur.archlinux.org/packages/razer-nari-pulseaudio-profile/)
- Other distros: Run `install.sh` script or see [installation instructions](https://github.com/imustafin/razer-nari-pulseaudio-profile#installing)

**For PipeWire:**

- [razer-nari-pipewire-profile](https://github.com/mrquantumoff/razer-nari-pipewire-profile) - PipeWire-specific profile (archived but working)
- Arch Linux: Install from [AUR](https://aur.archlinux.org/packages/razer-nari-pipewire-profile/)
- Fedora: Binary package in releases
- Other distros: Clone and run install script
- **Alternative:** [razer-nari-pulseaudio-profile](https://github.com/imustafin/razer-nari-pulseaudio-profile) also works with PipeWire (use `install-pipewire.sh`)

After installing the profiles, set Game Output as default for best quality:

```bash
pactl set-default-sink alsa_output.usb-Razer_Razer_Nari_Ultimate-00.analog-game
```

**Note**: Additional tools (battery monitoring, audio testing) are under development and will be released in future versions.

## How It Works

This tool was created through reverse engineering of the Razer Nari pairing protocol:

- Analyzed the pairing process to understand the USB HID communication
- Identified the pairing command: `FF 19 00 40 00 00 00 00`
- Discovered that both devices (dongle AND headset) need the command
- Created an independent, open-source implementation

## Troubleshooting

### "No dongle found"

- Ensure dongle is plugged in
- Check `lsusb` shows device `1532:051a` (or 051c/051e)

### "No headset found"

- Headset MUST be connected via USB charging cable
- Turn ON the headset while USB-connected
- Check `lsusb` shows device `1532:051d` (or 051b/051f)

### "Permission denied"

- Run with `sudo`:
  ```bash
  sudo python3 razer_nari_pair.py
  ```

### Headset keeps blinking blue

- Means it's searching but not connected
- Try running the pairing tool again
- Make sure headset was ON when commands were sent

### No audio

- On Linux, check PulseAudio/PipeWire:
  ```bash
  pactl list sinks | grep Nari
  pactl set-default-sink alsa_output.usb-Razer_Razer_Nari_Ultimate-00.analog-game
  ```

## Technical Details

**Pairing Command:**

```
FF 19 00 40 00 00 00 00
│  │  │  │  └─ Padding
│  │  │  └─ PAIR command (0x40)
│  │  └─ Padding
│  └─ Report ID (0x18 + 1)
└─ Header marker
```

**Protocol:**

- Standard USB HID Feature Reports
- Control Transfer: `bmRequestType=0x21`, `bRequest=0x09` (SET_REPORT)
- Dongle: Interface 5
- Headset: Interface 0

Both devices must receive the pairing command to establish wireless connection.

## Project Structure

```
razer-nari-pairing/
├── razer_nari_pair.py       # Main pairing tool
├── pair.sh                  # Quick runner script
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── CONTRIBUTING.md          # Contribution guidelines
├── CODE_OF_CONDUCT.md       # Community guidelines
├── SECURITY.md              # Security policy
├── LICENSE                  # MIT License
```

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

**We need your help!** This is a community reverse engineering project - contributions are very welcome!

**Priority areas:**

- **Hardware testing** - Razer Nari Ultimate and Essential variants need testing
- **Bug reports** - Found an issue? Let us know!
- **Code contributions** - Bug fixes, features, platform support
- **Documentation** - Improvements, translations, troubleshooting tips

**See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines** on how to contribute, report issues, and submit pull requests.

Let's help others with "orphaned" Razer headsets get their devices working on Linux!

## Disclaimer

This tool is not affiliated with or endorsed by Razer Inc. Use at your own risk.

---

**Enjoy your wireless headset!**

_Made with reverse engineering, persistence, and a lot of USB packet analysis._
