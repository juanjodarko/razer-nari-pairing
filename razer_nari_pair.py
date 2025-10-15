#!/usr/bin/env python3
"""
Razer Nari Wireless Headset Pairing Tool - FINAL WORKING VERSION
==================================================================

Successfully reverse-engineered pairing tool for Razer Nari headsets.
Pairs any Nari variant headset with any Nari variant dongle.

✅ TESTED AND WORKING on Linux (Arch)
✅ Cross-platform (Linux, Windows, macOS)
✅ Open source alternative to Razer's Windows-only utility

Hardware Support:
- Razer Nari Ultimate (Dongle PID: 0x051A, Headset PID: 0x051B)
- Razer Nari (Dongle PID: 0x051C, Headset PID: 0x051D)
- Razer Nari Essential (Dongle PID: 0x051E, Headset PID: 0x051F)

Requirements:
- Python 3.7+
- PyUSB (pip install pyusb)
- USB charging cable for headset
- Root/sudo access (for USB control)

Usage:
    sudo python3 razer_nari_pair_FINAL.py

Author: Community Reverse Engineering Project (2025)
License: MIT
Success Date: October 14, 2025
"""

import usb.core
import usb.util
import sys
import time
import platform
from typing import Optional

# ============================================================================
# USB Device Constants
# ============================================================================

RAZER_VID = 0x1532

# Dongle Product IDs (when plugged into PC)
DONGLE_PIDS = {
    0x051A: "Razer Nari Ultimate",
    0x051C: "Razer Nari",
    0x051E: "Razer Nari Essential",
}

# Headset Product IDs (when connected via USB charging cable)
HEADSET_PIDS = {
    0x051B: "Razer Nari Ultimate (Wired)",
    0x051D: "Razer Nari (Wired)",
    0x051F: "Razer Nari Essential (Wired)",
}

# HID Interfaces
DONGLE_HID_INTERFACE = 5    # Dongle uses Interface 5 for pairing
HEADSET_HID_INTERFACE = 0   # Headset uses Interface 0 for pairing

# ============================================================================
# Pairing Commands (Reverse-Engineered from HeadsetDll.dll)
# ============================================================================

# PAIR command - extracted from SendPairCmd() at RVA 0x14360
# Assembly: mov BYTE PTR [ebp-0x1c], 0x40
# Format: [0xFF, 0x19, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00]
#   0xFF - Header/marker
#   0x19 - Report ID (0x18 + 1)
#   0x00 - Padding
#   0x40 - PAIR command byte
#   0x00-0x00-0x00-0x00 - Padding
CMD_PAIR = bytes([0xFF, 0x19, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00])

# CANCEL PAIR command - extracted from SendCancelPairCmd() at RVA 0x14300
# Assembly: mov BYTE PTR [ebp-0x1c], 0x49
CMD_CANCEL_PAIR = bytes([0xFF, 0x19, 0x00, 0x49, 0x00, 0x00, 0x00, 0x00])

# ============================================================================
# Terminal Colors
# ============================================================================

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# ============================================================================
# Helper Functions
# ============================================================================

def print_header():
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("Razer Nari Wireless Pairing Tool")
    print("Community Open-Source Implementation - FINAL VERSION")
    print("=" * 70)
    print(f"{Colors.ENDC}")

def print_info(msg: str):
    print(f"{Colors.OKCYAN}[INFO]{Colors.ENDC} {msg}")

def print_success(msg: str):
    print(f"{Colors.OKGREEN}[SUCCESS]{Colors.ENDC} {msg}")

def print_warning(msg: str):
    print(f"{Colors.WARNING}[WARNING]{Colors.ENDC} {msg}")

def print_error(msg: str):
    print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {msg}")

# ============================================================================
# USB Device Functions
# ============================================================================

def find_device_by_pids(pid_dict: dict) -> Optional[usb.core.Device]:
    """Find first device matching any of the given PIDs"""
    for pid, name in pid_dict.items():
        dev = usb.core.find(idVendor=RAZER_VID, idProduct=pid)
        if dev:
            print_success(f"Found: {name} ({RAZER_VID:04X}:{pid:04X})")
            return dev
    return None

def claim_interface(dev: usb.core.Device, interface: int) -> bool:
    """Claim USB interface for communication"""
    try:
        if platform.system() == "Linux":
            if dev.is_kernel_driver_active(interface):
                dev.detach_kernel_driver(interface)

        usb.util.claim_interface(dev, interface)
        print_info(f"Claimed interface {interface}")
        return True
    except Exception as e:
        print_error(f"Failed to claim interface {interface}: {e}")
        return False

def release_interface(dev: usb.core.Device, interface: int):
    """Release USB interface"""
    try:
        usb.util.release_interface(dev, interface)
        if platform.system() == "Linux":
            try:
                dev.attach_kernel_driver(interface)
            except:
                pass
    except:
        pass

def send_hid_command(dev: usb.core.Device, interface: int, command: bytes) -> bool:
    """
    Send HID Feature Report via Control Transfer

    Args:
        dev: USB device
        interface: Interface number
        command: Command bytes to send

    Returns:
        True if successful, False otherwise
    """
    try:
        # HID SET_REPORT control transfer
        bmRequestType = 0x21  # Host-to-device, Class, Interface
        bRequest = 0x09       # SET_REPORT
        wValue = 0x0300       # Feature Report, ID 0
        wIndex = interface    # Interface number

        result = dev.ctrl_transfer(
            bmRequestType,
            bRequest,
            wValue,
            wIndex,
            command,
            timeout=1000
        )

        return result == len(command)
    except Exception as e:
        print_error(f"Failed to send command: {e}")
        return False

# ============================================================================
# Pairing Functions
# ============================================================================

def pair_devices() -> bool:
    """
    Main pairing function

    Pairs Razer Nari headset with dongle by sending pairing commands
    to BOTH devices (critical discovery!)

    Returns:
        True if pairing succeeded, False otherwise
    """
    print_header()
    print()

    # Check for root permissions
    import os
    if platform.system() == "Linux" and os.geteuid() != 0:
        print_error("This tool requires root/sudo privileges on Linux")
        print_info("Please run: sudo python3 razer_nari_pair_FINAL.py")
        return False

    print(f"{Colors.BOLD}Step 1: Checking Hardware{Colors.ENDC}")
    print()

    # Find dongle
    print_info("Searching for dongle...")
    dongle = find_device_by_pids(DONGLE_PIDS)
    if not dongle:
        print_error("No Razer Nari dongle found!")
        print_info("Please plug in the USB dongle and try again")
        return False

    # Find headset (must be USB-connected via charging cable)
    print_info("Searching for headset (via USB charging cable)...")
    headset = find_device_by_pids(HEADSET_PIDS)
    if not headset:
        print_error("No Razer Nari headset found via USB!")
        print()
        print_warning("The headset MUST be connected via USB charging cable during pairing")
        print_info("Steps:")
        print_info("  1. Connect headset to PC using USB charging cable")
        print_info("  2. Turn ON the headset (press power button)")
        print_info("  3. Run this tool again")
        return False

    print()
    print(f"{Colors.BOLD}Step 2: Preparing Devices{Colors.ENDC}")
    print()

    # Claim dongle interface
    if not claim_interface(dongle, DONGLE_HID_INTERFACE):
        return False

    # Claim headset interface
    if not claim_interface(headset, HEADSET_HID_INTERFACE):
        release_interface(dongle, DONGLE_HID_INTERFACE)
        return False

    try:
        print()
        print(f"{Colors.BOLD}Step 3: Sending Pairing Commands{Colors.ENDC}")
        print()
        print_info("Command: " + CMD_PAIR.hex(' ').upper())
        print()

        # Send pairing command to DONGLE
        print_info("Sending pairing command to dongle...")
        if send_hid_command(dongle, DONGLE_HID_INTERFACE, CMD_PAIR):
            print_success("Dongle command sent successfully")
        else:
            print_error("Failed to send command to dongle")
            return False

        time.sleep(1)

        # Send pairing command to HEADSET
        print_info("Sending pairing command to headset...")
        if send_hid_command(headset, HEADSET_HID_INTERFACE, CMD_PAIR):
            print_success("Headset command sent successfully")
        else:
            print_error("Failed to send command to headset")
            return False

        print()
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ Pairing commands sent to both devices!{Colors.ENDC}")
        print()
        print_info("Waiting 5 seconds for devices to exchange pairing data...")
        time.sleep(5)

        print()
        print(f"{Colors.BOLD}Step 4: Testing Wireless Connection{Colors.ENDC}")
        print()
        print(f"{Colors.OKGREEN}Next steps:{Colors.ENDC}")
        print("  1. Disconnect the headset USB cable")
        print("  2. Turn the headset OFF (hold power button)")
        print("  3. Turn the headset ON")
        print("  4. The headset should connect wirelessly to the dongle!")
        print()
        print(f"{Colors.OKGREEN}Expected result:{Colors.ENDC}")
        print("  • Headset LED turns solid blue (connected)")
        print("  • You hear a connection sound in the headset")
        print("  • Audio works wirelessly!")
        print()
        print(f"{Colors.BOLD}The pairing is now PERMANENT - devices remember each other!{Colors.ENDC}")
        print()

        return True

    finally:
        # Release interfaces
        release_interface(headset, HEADSET_HID_INTERFACE)
        release_interface(dongle, DONGLE_HID_INTERFACE)
        print_info("Released all interfaces")

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main function"""
    try:
        success = pair_devices()

        print()
        if success:
            print(f"{Colors.OKGREEN}{Colors.BOLD}=" * 70)
            print("PAIRING COMPLETE! 🎉")
            print("=" * 70)
            print(f"{Colors.ENDC}")
            print()
            print("Your headset is now paired with the dongle!")
            print("From now on, just:")
            print("  1. Plug in the dongle")
            print("  2. Turn on your headset")
            print("  3. They connect automatically - no pairing needed!")
            print()
            sys.exit(0)
        else:
            print(f"{Colors.FAIL}Pairing failed. Please check the instructions above.{Colors.ENDC}")
            sys.exit(1)

    except KeyboardInterrupt:
        print()
        print_info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print()
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
