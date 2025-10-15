# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| Older   | :x:                |

We recommend always using the latest version from the main branch.

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

**DO NOT open a public issue** for security vulnerabilities.

Instead, please email the maintainer directly at:
- **Email:** (see GitHub profile for contact information)

Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

You can expect a response within 48-72 hours. We will work with you to understand and address the issue promptly.

## Security Considerations

### Why This Tool Requires Root/Sudo

This tool requires root privileges because:
- **USB device access:** Writing to USB devices via libusb requires elevated permissions
- **HID Feature Reports:** Sending control transfers to USB HID devices is a privileged operation

The tool does NOT:
- Make network connections
- Access your filesystem (beyond the script itself)
- Install persistent services or daemons
- Modify system configurations
- Access sensitive data

### What The Tool Does

The pairing tool performs ONLY these operations:
1. Searches for Razer Nari dongles and headsets via USB
2. Sends an 8-byte pairing command to both devices
3. Exits immediately after pairing

**Total runtime:** ~5 seconds

### Security Best Practices

When using this tool:

1. **Review the source code** before running with sudo
   - The tool is intentionally small (~300 lines) for easy auditing
   - All USB operations are visible in `razer_nari_pair.py`

2. **Use udev rules instead of sudo** (optional)
   - You can configure udev to allow USB access without root
   - See community guides for USB device permissions

3. **Verify the source**
   - Clone from the official GitHub repository
   - Check commit signatures if available
   - Don't run random scripts from untrusted sources

4. **Keep dependencies updated**
   - Update PyUSB regularly: `pip install --upgrade pyusb`
   - Check for known vulnerabilities in dependencies

## Known Security Considerations

### USB Access Permissions

This tool requires direct USB device access. On Linux systems:
- Default behavior requires `sudo` for USB control transfers
- This is by design - USB device access is a privileged operation
- The tool does not attempt to escalate privileges beyond what sudo provides

### No Network Communication

This tool operates **entirely offline**:
- No network requests
- No telemetry or analytics
- No external dependencies beyond PyUSB
- All operations are local USB HID communication

### Code Transparency

Security through transparency:
- All source code is open and auditable
- No obfuscation or compiled binaries
- Clear, commented code for easy review
- Small codebase (~300 lines) makes auditing practical

## Reverse Engineering Disclosure

This tool was created through legal reverse engineering for interoperability purposes (DMCA Section 1201(f)):

- **No proprietary code was copied** - This is a clean-room implementation
- **Protocol analysis only** - We analyzed USB packets, not executable code
- **No DRM circumvention** - Pairing is not a DRM or encryption system
- **Interoperability purpose** - Enables Linux support for existing hardware

## Third-Party Dependencies

### PyUSB (python-usb)

- **Purpose:** USB device communication
- **License:** BSD License
- **Repository:** https://github.com/pyusb/pyusb
- **Security:** Well-established library, widely used in USB projects

**Recommendation:** Keep PyUSB updated to receive security patches.

### Python Standard Library

This tool uses only:
- `sys` - Command line arguments
- `time` - Sleep delays
- `usb.core` and `usb.util` (from PyUSB)

No additional dependencies or external packages.

## Permissions and Capabilities

### Required Permissions

- **USB device access** (root/sudo or udev rules)

### Does NOT Require

- Network access
- Filesystem write permissions (beyond /tmp if needed)
- Kernel module loading
- System configuration changes
- Access to other USB devices (only targets Razer Nari devices)

## Security Updates

Security updates will be released as soon as possible after a vulnerability is confirmed:

1. **Critical vulnerabilities:** Immediate patch and release
2. **High severity:** Patch within 48 hours
3. **Medium/Low severity:** Included in next regular release

Security advisories will be posted:
- In GitHub Security Advisories
- In the repository README
- As a pinned issue (for critical issues)

## Disclaimer

This tool is provided "as is" without warranty of any kind. While we take security seriously and follow best practices, users should:

- Review the code before running with elevated privileges
- Understand the operations being performed
- Use at their own risk

This tool is not affiliated with or endorsed by Razer Inc.

---

**Security is a community effort.** If you have security concerns or suggestions, please reach out. Thank you for helping keep this project safe!
