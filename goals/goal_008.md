# Goal #8

Here's a specific, measurable goal for your Raspberry Pi project:

## Iteration 50 — 2026-06-06T23:58:00.001057

**Next Concrete Step – Set Up the Raspberry Pi OS and Enable SSH**

1. **Flash the OS**
   - Download the latest Raspberry Pi OS Lite image from the official site.
   - Use `balenaEtcher` (or `dd` on Linux/macOS) to write the image to a micro‑SD card (≥8 GB).

2. **Enable SSH & Wi‑Fi (headless)**
   - After flashing, mount the boot partition.
   - Create an empty file named `ssh` (no extension) to enable SSH on boot.
   - Create a `wpa_supplicant.conf` file with your network credentials:
     ```conf
     country=US
     ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
     update_config=1

     network={
         ssid="YOUR_SSID"
         psk="YOUR_PASSWORD"
         key_mgmt=WPA-PSK
     }
     ```
   - Save the file to the boot partition.

3. **Boot and Connect**
   - Insert the SD card, power the Pi, and wait ~30 s.
   - Find its IP (e.g., via your router’s client list or `arp -a`).
   - SSH into the Pi: `ssh pi@<IP_ADDRESS>` (default password: `raspberry`).

4. **Update System**
   ```bash
   sudo apt update && sudo apt full-upgrade -y
   sudo reboot
   ```

Once you have a reachable SSH shell, the next milestone (installing required Python libraries and hardware drivers) can proceed.
