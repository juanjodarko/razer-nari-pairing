"""Shared fixtures for razer_nari_pair tests."""

from unittest.mock import MagicMock

import pytest

import razer_nari_pair


@pytest.fixture(autouse=True)
def _reset_logger():
    """Ensure logger is set up and cleaned between tests."""
    razer_nari_pair.setup_logging(verbose=False)
    yield
    razer_nari_pair.logger.handlers.clear()


@pytest.fixture()
def mock_usb_device():
    """Factory that creates a mock usb.core.Device."""

    def _make(**overrides):
        dev = MagicMock()
        dev.is_kernel_driver_active.return_value = False
        dev.ctrl_transfer.return_value = 8  # matches CMD_PAIR length
        for attr, val in overrides.items():
            setattr(dev, attr, val)
        return dev

    return _make
