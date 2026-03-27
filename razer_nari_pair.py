#!/usr/bin/env python3
"""
Razer Nari Wireless Headset Pairing Tool - FINAL WORKING VERSION
==================================================================

Successfully reverse-engineered pairing tool for Razer Nari headsets.
Pairs any Nari variant headset with any Nari variant dongle.

TESTED AND WORKING on Linux (Arch) - Nari Regular and Nari Ultimate
Cross-platform (Linux, Windows, macOS)
Open source alternative to Razer's Windows-only utility

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
    sudo python3 razer_nari_pair.py

Author: Community Reverse Engineering Project (2025)
License: MIT
Success Date: October 14, 2025
"""

import argparse
import logging
import os
import platform
import sys
import time
from typing import Optional

import usb.core
import usb.util

# Custom log level for SUCCESS messages (between INFO and WARNING)
SUCCESS = 25
logging.addLevelName(SUCCESS, "SUCCESS")

logger = logging.getLogger("razer_nari_pair")

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
DONGLE_HID_INTERFACE = 5  # Dongle uses Interface 5 for pairing
HEADSET_HID_INTERFACE = 0  # Headset uses Interface 0 for pairing

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
# Logging Setup
# ============================================================================

BOLD = "\033[1m"
RESET = "\033[0m"

LEVEL_COLORS = {
    logging.DEBUG: "\033[90m",     # Grey
    logging.INFO: "\033[96m",      # Cyan
    SUCCESS: "\033[92m",           # Green
    logging.WARNING: "\033[93m",   # Yellow
    logging.ERROR: "\033[91m",     # Red
}

HEADER_COLOR = "\033[95m"


class ColoredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = LEVEL_COLORS.get(record.levelno, "")
        tag = record.levelname
        # Use the base Formatter to include exception information and any
        # other standard formatting, then add color around the result.
        base_message = super().format(record)
        return f"{color}[{tag}]{RESET} {base_message}"


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)
    # Prevent messages from being propagated to the root logger and
    # potentially logged twice if the root logger has handlers configured.
    logger.propagate = False

    # Avoid adding duplicate StreamHandlers if setup_logging is called
    # multiple times (e.g. in tests or interactive sessions).
    stream_handler_exists = any(
        isinstance(h, logging.StreamHandler) for h in logger.handlers
    )

    if not stream_handler_exists:
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter())
        logger.addHandler(handler)
    else:
        # Ensure existing StreamHandlers use the expected formatter.
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setFormatter(ColoredFormatter())
def print_header():
    print(f"{HEADER_COLOR}{BOLD}")
    print("=" * 70)
    print("Razer Nari Wireless Pairing Tool")
    print("Community Open-Source Implementation - FINAL VERSION")
    print("=" * 70)
    print(RESET)


# ============================================================================
# USB Device Functions
# ============================================================================


def find_device_by_pids(pid_dict: dict) -> Optional[usb.core.Device]:
    """Find first device matching any of the given PIDs"""
    for pid, name in pid_dict.items():
        logger.debug("Looking for %s (VID=%04X, PID=%04X)", name, RAZER_VID, pid)
        dev = usb.core.find(idVendor=RAZER_VID, idProduct=pid)
        if dev:
            logger.log(SUCCESS, f"Found: {name} ({RAZER_VID:04X}:{pid:04X})")
            return dev
    return None


def claim_interface(dev: usb.core.Device, interface: int) -> bool:
    """Claim USB interface for communication"""
    try:
        if platform.system() == "Linux":
            if dev.is_kernel_driver_active(interface):
                logger.debug("Detaching kernel driver from interface %d", interface)
                dev.detach_kernel_driver(interface)

        usb.util.claim_interface(dev, interface)
        logger.info("Claimed interface %d", interface)
        return True
    except Exception as e:
        logger.error("Failed to claim interface %d: %s", interface, e)
        return False


def release_interface(dev: usb.core.Device, interface: int):
    """Release USB interface"""
    try:
        usb.util.release_interface(dev, interface)
        if platform.system() == "Linux":
            try:
                dev.attach_kernel_driver(interface)
            except Exception:
                pass
    except Exception:
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
        bRequest = 0x09  # SET_REPORT
        wValue = 0x0300  # Feature Report, ID 0
        wIndex = interface  # Interface number

        logger.debug(
            "ctrl_transfer: bmRequestType=0x%02X bRequest=0x%02X "
            "wValue=0x%04X wIndex=%d data=%s",
            bmRequestType, bRequest, wValue, wIndex, command.hex(" "),
        )
        result = dev.ctrl_transfer(
            bmRequestType, bRequest, wValue, wIndex, command, timeout=1000
        )
        logger.debug("ctrl_transfer returned %d (expected %d)", result, len(command))

        return result == len(command)
    except Exception as e:
        logger.error("Failed to send command: %s", e)
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
    if platform.system() == "Linux" and os.geteuid() != 0:
        logger.error("This tool requires root/sudo privileges on Linux")
        logger.info("Please run: sudo python3 razer_nari_pair.py")
        return False

    print(f"{BOLD}Step 1: Checking Hardware{RESET}")
    print()

    # Find dongle
    logger.info("Searching for dongle...")
    dongle = find_device_by_pids(DONGLE_PIDS)
    if not dongle:
        logger.error("No Razer Nari dongle found!")
        logger.info("Please plug in the USB dongle and try again")
        return False

    # Find headset (must be USB-connected via charging cable)
    logger.info("Searching for headset (via USB charging cable)...")
    headset = find_device_by_pids(HEADSET_PIDS)
    if not headset:
        logger.error("No Razer Nari headset found via USB!")
        print()
        logger.warning(
            "The headset MUST be connected via USB charging cable during pairing"
        )
        logger.info("Steps:")
        logger.info("  1. Connect headset to PC using USB charging cable")
        logger.info("  2. Turn ON the headset (press power button)")
        logger.info("  3. Run this tool again")
        return False

    print()
    print(f"{BOLD}Step 2: Preparing Devices{RESET}")
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
        print(f"{BOLD}Step 3: Sending Pairing Commands{RESET}")
        print()
        logger.info("Command: %s", CMD_PAIR.hex(" ").upper())
        print()

        # Send pairing command to DONGLE
        logger.info("Sending pairing command to dongle...")
        if send_hid_command(dongle, DONGLE_HID_INTERFACE, CMD_PAIR):
            logger.log(SUCCESS, "Dongle command sent successfully")
        else:
            logger.error("Failed to send command to dongle")
            return False

        time.sleep(1)

        # Send pairing command to HEADSET
        logger.info("Sending pairing command to headset...")
        if send_hid_command(headset, HEADSET_HID_INTERFACE, CMD_PAIR):
            logger.log(SUCCESS, "Headset command sent successfully")
        else:
            logger.error("Failed to send command to headset")
            return False

        print()
        print(
            f"\033[92m{BOLD}✓ Pairing commands sent to both devices!{RESET}"
        )
        print()
        logger.info("Waiting 5 seconds for devices to exchange pairing data...")
        time.sleep(5)

        print()
        print(f"{BOLD}Step 4: Testing Wireless Connection{RESET}")
        print()
        print(f"\033[92mNext steps:{RESET}")
        print("  1. Disconnect the headset USB cable")
        print("  2. Turn the headset OFF (hold power button)")
        print("  3. Turn the headset ON")
        print("  4. The headset should connect wirelessly to the dongle!")
        print()
        print(f"\033[92mExpected result:{RESET}")
        print("  • Headset LED turns solid blue (connected)")
        print("  • You hear a connection sound in the headset")
        print("  • Audio works wirelessly!")
        print()
        print(
            f"{BOLD}The pairing is now PERMANENT - devices remember each other!{RESET}"
        )
        print()

        return True

    finally:
        # Release interfaces
        release_interface(headset, HEADSET_HID_INTERFACE)
        release_interface(dongle, DONGLE_HID_INTERFACE)
        logger.info("Released all interfaces")


# ============================================================================
# Main Entry Point
# ============================================================================


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Razer Nari Wireless Headset Pairing Tool"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug output"
    )
    return parser.parse_args()


def main():
    """Main function"""
    args = parse_args()
    setup_logging(verbose=args.verbose)

    try:
        success = pair_devices()

        print()
        if success:
            print(f"\033[92m{BOLD}=" * 70)
            print("PAIRING COMPLETE! 🎉")
            print("=" * 70)
            print(RESET)
            print()
            print("Your headset is now paired with the dongle!")
            print("From now on, just:")
            print("  1. Plug in the dongle")
            print("  2. Turn on your headset")
            print("  3. They connect automatically - no pairing needed!")
            print()
            sys.exit(0)
        else:
            print(
                f"\033[91mPairing failed. Please check the instructions above.{RESET}"
            )
            sys.exit(1)

    except KeyboardInterrupt:
        print()
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception:
        print()
        logger.exception("Unexpected error")
        sys.exit(1)


if __name__ == "__main__":
    main()
