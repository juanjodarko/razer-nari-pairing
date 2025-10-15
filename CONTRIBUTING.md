# Contributing to Razer Nari Pairing Tool

Thank you for your interest in contributing! This project was born from community reverse engineering efforts, and we welcome contributions from everyone.

## How You Can Help

### 1. Hardware Testing (Most Needed!)

We need help testing on different hardware variants:

**Untested Hardware:**

- Razer Nari Ultimate
- Razer Nari Essential
- Different dongle/headset combinations (cross-model pairing)

**If you have untested hardware:**

1. Test the pairing process following the README instructions
2. Report your results by opening an issue with:
   - **Hardware models** (both dongle and headset USB IDs from `lsusb`)
   - **Success/failure** (did pairing work?)
   - **Any issues encountered** (errors, LED behavior, connection problems)
   - **Your Linux distribution and kernel version**

**Example report:**

```
Hardware: Razer Nari Ultimate headset (1532:051b) + Ultimate dongle (1532:051a)
Distro: Arch Linux (kernel 6.1.0)
Result: Success - paired on first attempt
Notes: Solid blue LED, wireless audio works perfectly
```

### 2. Bug Reports

Found a bug? Please open an issue with:

- **Description:** Clear description of the problem
- **Steps to reproduce:** How to trigger the bug
- **Expected behavior:** What should happen
- **Actual behavior:** What actually happens
- **Environment:**
  - Linux distribution and version
  - Python version (`python3 --version`)
  - PyUSB version (`pip show pyusb`)
  - Hardware variant (from `lsusb`)
- **Logs:** Any error messages or output from the tool

### 3. Code Contributions

**Before starting work:**

- Check existing issues and pull requests to avoid duplication
- For major changes, open an issue first to discuss your approach

**Contribution areas we welcome:**

- Bug fixes
- Platform support (Windows, macOS)
- Code quality improvements
- Performance optimizations
- Better error handling
- Additional features (battery monitoring, configuration tools, etc.)

**Code style:**

- Follow PEP 8 guidelines for Python code
- Use descriptive variable and function names
- Add comments for complex logic
- Keep functions focused and modular

**Testing:**

- Test your changes with actual hardware if possible
- Verify the pairing process still works
- Check for permission errors and USB access issues
- Test on different Linux distributions if you can

### 4. Documentation

Documentation improvements are always welcome:

- Fix typos or unclear instructions
- Add troubleshooting tips
- Improve installation guides
- Translate documentation (if you're multilingual)
- Add diagrams or screenshots

### 5. Pull Request Process

1. **Fork the repository** and create a new branch:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines

3. **Test thoroughly** on your hardware

4. **Commit your changes** with clear, descriptive commit messages:

   ```bash
   git commit -m "Add support for Nari Essential pairing"
   ```

5. **Push to your fork:**

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request** with:
   - Clear title describing the change
   - Description of what changed and why
   - Hardware tested on (if applicable)
   - Any breaking changes or special considerations

### 6. Feature Requests

Have an idea? Open an issue with:

- **Feature description:** What you'd like to see
- **Use case:** Why this would be useful
- **Implementation ideas:** (optional) How it might work

## Development Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/YOUR-USERNAME/razer-nari-pairing.git
   cd razer-nari-pairing
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Test the tool:**
   ```bash
   sudo python3 razer_nari_pair.py
   ```

## Community Guidelines

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). In summary:

- **Be respectful:** Treat everyone with respect and kindness
- **Be constructive:** Provide helpful feedback and suggestions
- **Be patient:** Maintainers are volunteers with limited time
- **Be collaborative:** This is a community project - we're all learning together

For detailed community standards and enforcement guidelines, see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Questions?

Not sure about something? Feel free to:

- Open an issue asking for clarification
- Start a discussion in the issue tracker
- Look at existing issues and PRs for examples

## Legal Considerations

This project was created through legal reverse engineering for interoperability purposes. When contributing:

- Do not submit copyrighted code from Razer or other sources
- Ensure your contributions are your own original work
- By submitting a PR, you agree to license your contribution under the MIT License

---

**Thank you for helping make Razer Nari headsets more accessible on Linux!**

This is a community-driven project, and every contribution - no matter how small - makes a difference.
