"""Tests for razer_nari_pair — unit and integration."""

from unittest.mock import MagicMock, call, patch

import pytest

import razer_nari_pair
from razer_nari_pair import (
    CMD_PAIR,
    DONGLE_HID_INTERFACE,
    DONGLE_PIDS,
    HEADSET_HID_INTERFACE,
    HEADSET_PIDS,
    RAZER_VID,
    SUCCESS,
    ColoredFormatter,
    claim_interface,
    find_device_by_pids,
    pair_devices,
    parse_args,
    release_interface,
    send_hid_command,
    setup_logging,
)


# ============================================================================
# Constants
# ============================================================================


class TestConstants:
    def test_razer_vid(self):
        assert RAZER_VID == 0x1532

    def test_dongle_pids_are_correct(self):
        assert 0x051A in DONGLE_PIDS  # Ultimate
        assert 0x051C in DONGLE_PIDS  # Regular
        assert 0x051E in DONGLE_PIDS  # Essential

    def test_headset_pids_are_correct(self):
        assert 0x051B in HEADSET_PIDS  # Ultimate
        assert 0x051D in HEADSET_PIDS  # Regular
        assert 0x051F in HEADSET_PIDS  # Essential

    def test_dongle_headset_pids_are_paired(self):
        """Each dongle PID should be exactly 1 less than its headset PID."""
        for dongle_pid in DONGLE_PIDS:
            assert dongle_pid + 1 in HEADSET_PIDS

    def test_pair_command_format(self):
        assert CMD_PAIR == bytes([0xFF, 0x19, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00])
        assert len(CMD_PAIR) == 8

    def test_interfaces(self):
        assert DONGLE_HID_INTERFACE == 5
        assert HEADSET_HID_INTERFACE == 0

    def test_success_level(self):
        assert SUCCESS == 25


# ============================================================================
# Logging
# ============================================================================


class TestLogging:
    def test_setup_logging_default_level(self):
        razer_nari_pair.logger.handlers.clear()
        setup_logging(verbose=False)
        assert razer_nari_pair.logger.level == 20  # INFO

    def test_setup_logging_verbose(self):
        razer_nari_pair.logger.handlers.clear()
        setup_logging(verbose=True)
        assert razer_nari_pair.logger.level == 10  # DEBUG

    def test_setup_logging_no_duplicate_handlers(self):
        razer_nari_pair.logger.handlers.clear()
        setup_logging()
        setup_logging()
        handler_count = len(razer_nari_pair.logger.handlers)
        assert handler_count == 1

    def test_colored_formatter_info(self):
        import logging

        fmt = ColoredFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello", args=(), exc_info=None,
        )
        output = fmt.format(record)
        assert "[INFO]" in output
        assert "hello" in output

    def test_colored_formatter_error(self):
        import logging

        fmt = ColoredFormatter()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="bad", args=(), exc_info=None,
        )
        output = fmt.format(record)
        assert "[ERROR]" in output

    def test_colored_formatter_success(self):
        import logging

        fmt = ColoredFormatter()
        record = logging.LogRecord(
            name="test", level=SUCCESS, pathname="", lineno=0,
            msg="done", args=(), exc_info=None,
        )
        output = fmt.format(record)
        assert "[SUCCESS]" in output


# ============================================================================
# find_device_by_pids
# ============================================================================


class TestFindDeviceByPids:
    @patch("razer_nari_pair.usb.core.find")
    def test_returns_device_when_found(self, mock_find, mock_usb_device):
        dev = mock_usb_device()
        mock_find.return_value = dev

        result = find_device_by_pids({0x051C: "Razer Nari"})

        assert result is dev
        mock_find.assert_called_once_with(idVendor=RAZER_VID, idProduct=0x051C)

    @patch("razer_nari_pair.usb.core.find")
    def test_returns_none_when_not_found(self, mock_find):
        mock_find.return_value = None

        result = find_device_by_pids(DONGLE_PIDS)

        assert result is None
        assert mock_find.call_count == len(DONGLE_PIDS)

    @patch("razer_nari_pair.usb.core.find")
    def test_returns_first_match(self, mock_find, mock_usb_device):
        dev = mock_usb_device()
        # First PID not found, second PID found
        mock_find.side_effect = [None, dev]

        pids = {0x051A: "Ultimate", 0x051C: "Regular"}
        result = find_device_by_pids(pids)

        assert result is dev
        assert mock_find.call_count == 2

    @patch("razer_nari_pair.usb.core.find")
    def test_empty_pid_dict(self, mock_find):
        result = find_device_by_pids({})
        assert result is None
        mock_find.assert_not_called()


# ============================================================================
# claim_interface
# ============================================================================


class TestClaimInterface:
    @patch("razer_nari_pair.platform.system", return_value="Linux")
    @patch("razer_nari_pair.usb.util.claim_interface")
    def test_claims_successfully_linux(self, mock_claim, _mock_sys, mock_usb_device):
        dev = mock_usb_device()
        dev.is_kernel_driver_active.return_value = False

        assert claim_interface(dev, 5) is True
        mock_claim.assert_called_once_with(dev, 5)

    @patch("razer_nari_pair.platform.system", return_value="Linux")
    @patch("razer_nari_pair.usb.util.claim_interface")
    def test_detaches_kernel_driver_if_active(self, mock_claim, _mock_sys, mock_usb_device):
        dev = mock_usb_device()
        dev.is_kernel_driver_active.return_value = True

        assert claim_interface(dev, 5) is True
        dev.detach_kernel_driver.assert_called_once_with(5)

    @patch("razer_nari_pair.platform.system", return_value="Windows")
    @patch("razer_nari_pair.usb.util.claim_interface")
    def test_skips_kernel_driver_on_non_linux(self, mock_claim, _mock_sys, mock_usb_device):
        dev = mock_usb_device()

        assert claim_interface(dev, 5) is True
        dev.is_kernel_driver_active.assert_not_called()

    @patch("razer_nari_pair.platform.system", return_value="Linux")
    @patch("razer_nari_pair.usb.util.claim_interface", side_effect=Exception("busy"))
    def test_returns_false_on_error(self, mock_claim, _mock_sys, mock_usb_device):
        dev = mock_usb_device()
        dev.is_kernel_driver_active.return_value = False

        assert claim_interface(dev, 5) is False


# ============================================================================
# release_interface
# ============================================================================


class TestReleaseInterface:
    @patch("razer_nari_pair.platform.system", return_value="Linux")
    @patch("razer_nari_pair.usb.util.release_interface")
    def test_releases_and_reattaches_driver(self, mock_release, _mock_sys, mock_usb_device):
        dev = mock_usb_device()

        release_interface(dev, 5)

        mock_release.assert_called_once_with(dev, 5)
        dev.attach_kernel_driver.assert_called_once_with(5)

    @patch("razer_nari_pair.platform.system", return_value="Windows")
    @patch("razer_nari_pair.usb.util.release_interface")
    def test_skips_reattach_on_non_linux(self, mock_release, _mock_sys, mock_usb_device):
        dev = mock_usb_device()

        release_interface(dev, 5)

        mock_release.assert_called_once_with(dev, 5)
        dev.attach_kernel_driver.assert_not_called()

    @patch("razer_nari_pair.platform.system", return_value="Linux")
    @patch("razer_nari_pair.usb.util.release_interface", side_effect=Exception("fail"))
    def test_does_not_raise_on_error(self, mock_release, _mock_sys, mock_usb_device):
        dev = mock_usb_device()
        # Should not raise
        release_interface(dev, 5)

    @patch("razer_nari_pair.platform.system", return_value="Linux")
    @patch("razer_nari_pair.usb.util.release_interface")
    def test_does_not_raise_if_reattach_fails(self, mock_release, _mock_sys, mock_usb_device):
        dev = mock_usb_device()
        dev.attach_kernel_driver.side_effect = Exception("no driver")

        release_interface(dev, 5)  # should not raise


# ============================================================================
# send_hid_command
# ============================================================================


class TestSendHidCommand:
    def test_successful_transfer(self, mock_usb_device):
        dev = mock_usb_device()
        dev.ctrl_transfer.return_value = 8

        assert send_hid_command(dev, 5, CMD_PAIR) is True
        dev.ctrl_transfer.assert_called_once_with(
            0x21, 0x09, 0x0300, 5, CMD_PAIR, timeout=1000,
        )

    def test_partial_transfer_returns_false(self, mock_usb_device):
        dev = mock_usb_device()
        dev.ctrl_transfer.return_value = 4  # only 4 of 8 bytes sent

        assert send_hid_command(dev, 5, CMD_PAIR) is False

    def test_transfer_exception_returns_false(self, mock_usb_device):
        dev = mock_usb_device()
        dev.ctrl_transfer.side_effect = Exception("USB timeout")

        assert send_hid_command(dev, 5, CMD_PAIR) is False

    def test_uses_correct_hid_constants(self, mock_usb_device):
        dev = mock_usb_device()
        dev.ctrl_transfer.return_value = 8

        send_hid_command(dev, 0, CMD_PAIR)

        args = dev.ctrl_transfer.call_args
        assert args[0][0] == 0x21  # bmRequestType: Host-to-device, Class, Interface
        assert args[0][1] == 0x09  # bRequest: SET_REPORT
        assert args[0][2] == 0x0300  # wValue: Feature Report, ID 0
        assert args[0][3] == 0  # wIndex: interface number


# ============================================================================
# parse_args
# ============================================================================


class TestParseArgs:
    def test_default_args(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["razer_nari_pair.py"])
        args = parse_args()
        assert args.verbose is False

    def test_verbose_short(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["razer_nari_pair.py", "-v"])
        args = parse_args()
        assert args.verbose is True

    def test_verbose_long(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["razer_nari_pair.py", "--verbose"])
        args = parse_args()
        assert args.verbose is True


# ============================================================================
# pair_devices (integration)
# ============================================================================


class TestPairDevicesIntegration:
    """End-to-end tests of pair_devices() with mocked USB layer."""

    @patch("razer_nari_pair.time.sleep")
    @patch("razer_nari_pair.platform.system", return_value="Linux")
    @patch("razer_nari_pair.os.geteuid", return_value=0)
    @patch("razer_nari_pair.usb.util.release_interface")
    @patch("razer_nari_pair.usb.util.claim_interface")
    @patch("razer_nari_pair.usb.core.find")
    def test_successful_pairing(
        self, mock_find, mock_claim, mock_release, mock_geteuid,
        _mock_sys, mock_sleep, mock_usb_device,
    ):
        dongle = mock_usb_device()
        headset = mock_usb_device()

        # First 3 calls for dongle PIDs (first matches), next 3 for headset PIDs (first matches)
        mock_find.side_effect = [dongle, headset]

        result = pair_devices()

        assert result is True
        # Both devices got the pair command
        dongle.ctrl_transfer.assert_called_once()
        headset.ctrl_transfer.assert_called_once()
        # Interfaces were released
        assert mock_release.call_count == 2

    @patch("razer_nari_pair.platform.system", return_value="Linux")
    @patch("razer_nari_pair.os.geteuid", return_value=1000)
    def test_fails_without_root(self, mock_geteuid, _mock_sys):
        result = pair_devices()
        assert result is False

    @patch("razer_nari_pair.platform.system", return_value="Linux")
    @patch("razer_nari_pair.os.geteuid", return_value=0)
    @patch("razer_nari_pair.usb.core.find", return_value=None)
    def test_fails_no_dongle(self, mock_find, mock_geteuid, _mock_sys):
        result = pair_devices()
        assert result is False

    @patch("razer_nari_pair.platform.system", return_value="Linux")
    @patch("razer_nari_pair.os.geteuid", return_value=0)
    @patch("razer_nari_pair.usb.core.find")
    def test_fails_no_headset(self, mock_find, mock_geteuid, _mock_sys, mock_usb_device):
        dongle = mock_usb_device()
        # Dongle found on first call, headset not found (3 None for each headset PID)
        mock_find.side_effect = [dongle, None, None, None]

        result = pair_devices()
        assert result is False

    @patch("razer_nari_pair.time.sleep")
    @patch("razer_nari_pair.platform.system", return_value="Linux")
    @patch("razer_nari_pair.os.geteuid", return_value=0)
    @patch("razer_nari_pair.usb.util.release_interface")
    @patch("razer_nari_pair.usb.util.claim_interface")
    @patch("razer_nari_pair.usb.core.find")
    def test_fails_dongle_command_error(
        self, mock_find, mock_claim, mock_release, mock_geteuid,
        _mock_sys, mock_sleep, mock_usb_device,
    ):
        dongle = mock_usb_device()
        headset = mock_usb_device()
        dongle.ctrl_transfer.side_effect = Exception("USB error")
        mock_find.side_effect = [dongle, headset]

        result = pair_devices()

        assert result is False
        # Interfaces still released in finally block
        assert mock_release.call_count == 2

    @patch("razer_nari_pair.time.sleep")
    @patch("razer_nari_pair.platform.system", return_value="Linux")
    @patch("razer_nari_pair.os.geteuid", return_value=0)
    @patch("razer_nari_pair.usb.util.release_interface")
    @patch("razer_nari_pair.usb.util.claim_interface")
    @patch("razer_nari_pair.usb.core.find")
    def test_fails_headset_command_error(
        self, mock_find, mock_claim, mock_release, mock_geteuid,
        _mock_sys, mock_sleep, mock_usb_device,
    ):
        dongle = mock_usb_device()
        headset = mock_usb_device()
        headset.ctrl_transfer.side_effect = Exception("USB error")
        mock_find.side_effect = [dongle, headset]

        result = pair_devices()

        assert result is False
        assert mock_release.call_count == 2

    @patch("razer_nari_pair.time.sleep")
    @patch("razer_nari_pair.platform.system", return_value="Linux")
    @patch("razer_nari_pair.os.geteuid", return_value=0)
    @patch("razer_nari_pair.usb.util.release_interface")
    @patch("razer_nari_pair.usb.util.claim_interface", side_effect=Exception("busy"))
    @patch("razer_nari_pair.usb.core.find")
    def test_fails_claim_dongle_interface(
        self, mock_find, mock_claim, mock_release, mock_geteuid,
        _mock_sys, mock_sleep, mock_usb_device,
    ):
        dongle = mock_usb_device()
        headset = mock_usb_device()
        mock_find.side_effect = [dongle, headset]

        result = pair_devices()
        assert result is False

    @patch("razer_nari_pair.time.sleep")
    @patch("razer_nari_pair.platform.system", return_value="Linux")
    @patch("razer_nari_pair.os.geteuid", return_value=0)
    @patch("razer_nari_pair.usb.util.release_interface")
    @patch("razer_nari_pair.usb.util.claim_interface")
    @patch("razer_nari_pair.usb.core.find")
    def test_claim_headset_fails_releases_dongle(
        self, mock_find, mock_claim, mock_release, mock_geteuid,
        _mock_sys, mock_sleep, mock_usb_device,
    ):
        dongle = mock_usb_device()
        headset = mock_usb_device()
        mock_find.side_effect = [dongle, headset]
        # First claim (dongle) succeeds, second (headset) fails
        mock_claim.side_effect = [None, Exception("busy")]

        result = pair_devices()

        assert result is False
        # Dongle interface released after headset claim failure
        mock_release.assert_called()


# ============================================================================
# main (integration)
# ============================================================================


class TestMainIntegration:
    @patch("razer_nari_pair.pair_devices", return_value=True)
    def test_exits_0_on_success(self, mock_pair, monkeypatch):
        monkeypatch.setattr("sys.argv", ["razer_nari_pair.py"])
        with pytest.raises(SystemExit) as exc_info:
            razer_nari_pair.main()
        assert exc_info.value.code == 0

    @patch("razer_nari_pair.pair_devices", return_value=False)
    def test_exits_1_on_failure(self, mock_pair, monkeypatch):
        monkeypatch.setattr("sys.argv", ["razer_nari_pair.py"])
        with pytest.raises(SystemExit) as exc_info:
            razer_nari_pair.main()
        assert exc_info.value.code == 1

    @patch("razer_nari_pair.pair_devices", side_effect=KeyboardInterrupt)
    def test_exits_0_on_keyboard_interrupt(self, mock_pair, monkeypatch):
        monkeypatch.setattr("sys.argv", ["razer_nari_pair.py"])
        with pytest.raises(SystemExit) as exc_info:
            razer_nari_pair.main()
        assert exc_info.value.code == 0

    @patch("razer_nari_pair.pair_devices", side_effect=RuntimeError("boom"))
    def test_exits_1_on_unexpected_error(self, mock_pair, monkeypatch):
        monkeypatch.setattr("sys.argv", ["razer_nari_pair.py"])
        with pytest.raises(SystemExit) as exc_info:
            razer_nari_pair.main()
        assert exc_info.value.code == 1
