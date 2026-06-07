# Goal #10

Here's a specific, measurable goal for your Raspberry Pi project:

## Iteration 62 — 2026-06-07T02:34:04.954558

**Next Concrete Step – Set Up the Raspberry Pi OS and Enable GPIO Access**

1. **Flash the OS**
   - Download the latest Raspberry Pi OS Lite image from the official site.
   - Use `balenaEtcher` (or `dd` on Linux/macOS) to write the image to a micro‑SD card.
   - Insert the card into the Pi and power it on.

2. **Initial Configuration**
   - On first boot, log in with default credentials (`pi` / `raspberry`).
   - Run `sudo raspi-config`:
     - **Change default password.**
     - **Enable SSH** (Interface Options → SSH → Yes).
     - **Enable I2C, SPI, and GPIO** (Interface Options → I2C/SPI → Yes).
     - **Set up Wi‑Fi** (System Options → Wireless LAN) or connect Ethernet.

3. **Update System**
   ```bash
   sudo apt update && sudo apt full-upgrade -y
   sudo reboot
   ```

4. **Test GPIO Access**
   - Install `python3-gpiozero` and `python3-rpi.gpio`:
     ```bash
     sudo apt install -y python3-gpiozero python3-rpi.gpio
     ```
   - Run a quick test script:
     ```python
     from gpiozero import LED
     from time import sleep

     led = LED(17)   # GPIO17 (pin 11)
     while True:
         led.on()
         sleep(1)
         led.off()
         sleep(1)
     ```
   - Verify the LED blinks; if it does, GPIO is functional.

**Outcome:** The Pi is ready for further development (sensor integration, web server, etc.).
