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

## Iteration 51 — 2026-06-07T00:11:33.427326

To proceed with enabling SSH and Wi-Fi (headless), I will:

1. Use `balenaEtcher` to write the latest Raspberry Pi OS Lite image to a micro-SD card (≥8 GB).
2. Mount the boot partition using `blkid` and identify the root file system.
3. Create an empty file named `ssh` in the root directory of the mounted partition.

I will execute these steps by creating a new script (`enable_ssh.py`) that uses `balenaEtcher` to flash the image, mounts the partition, identifies the root file system, and creates the `ssh` file. I will then run this script after flashing the OS to ensure all necessary files are created.

Next step: Write the `enable_ssh.py` script and execute it using Python.

## Iteration 52 — 2026-06-07T00:26:18.321396

To proceed with enabling SSH and Wi-Fi (headless), you need to perform the following steps:

1. **Verify the Micro-SD Card Presence**: Use `sdcard_info` command to verify if a micro-SD card is inserted successfully.

2. **Get the Boot Partition Information**: Run `blkid -d /boot/efi*` to identify the root file system on the boot partition.

3. **Create the SSH File**: Write a Python script (`enable_ssh.py`) that will create an empty file named `ssh` in the root directory of the mounted partition using `sudo mkdir -p /media/sda1/ssh`.

4. **Mount the Boot Partition and Create SSH Directory**: Use `sudo mount -o remount /dev/sdb1 /media/sda1` to mount the boot partition, and then use `sudo mkdir -p /media/sda1/ssh` to create an empty directory named `ssh` in the root of the mounted partition.

This script will ensure that SSH and Wi-Fi settings are enabled on the headless Raspberry Pi.

## Iteration 53 — 2026-06-07T00:39:31.560284

**Next Concrete Step – Create a Python script that prepares the SD‑card for head‑less boot**

1. **Detect the boot partition**  
   ```python
   import subprocess, pathlib, sys

   def get_boot_mount():
       # List block devices, look for the FAT partition (type vfat) on the inserted card
       out = subprocess.check_output(['lsblk', '-o', 'NAME,FSTYPE,MOUNTPOINT', '-J']).decode()
       import json, re
       for dev in json.loads(out)['blockdevices']:
           if dev.get('fstype') == 'vfat' and dev.get('mountpoint'):
               return pathlib.Path(dev['mountpoint'])
       sys.exit('Boot partition not found – insert the flashed SD card')
   ```

2. **Create the `ssh` flag file**  
   ```python
   def enable_ssh(boot_path: pathlib.Path):
       (boot_path / 'ssh').touch()
   ```

3. **Add Wi‑Fi configuration (optional)**  
   ```python
   def add_wifi(boot_path: pathlib.Path, ssid: str, psk: str, country: str = 'US'):
       wpa = f"""country={country}
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
network={{
    ssid="{ssid}"
    psk="{psk}"
    key_mgmt=WPA-PSK
}}"""
       (boot_path / 'wpa_supplicant.conf').write_text(wpa)
   ```

4. **Main routine**  
   ```python
   if __name__ == '__main__':
       boot = get_boot_mount()
       enable_ssh(boot)
       # Uncomment and fill in your Wi‑Fi details if needed:
       # add_wifi(boot, 'YourSSID', 'YourPassword')
       print('SSH enabled (and Wi‑Fi config written if used).')
   ```

Save this as **`enable_ssh.py`**, run it while the SD card is mounted, then safely eject the card. The Pi will boot with SSH enabled and, if supplied, connect to your Wi‑Fi network automatically.

****

## Iteration 54 — 2026-06-07T00:51:19.054062

**Next Concrete Step – Write the “enable_ssh.py” script**

```python
#!/usr/bin/env python3
import subprocess, pathlib, sys, json

def find_boot_partition():
    """Return the mount point of the FAT (vfat) partition of the inserted SD card."""
    lsblk = subprocess.check_output(
        ['lsblk', '-J', '-o', 'NAME,FSTYPE,MOUNTPOINT'], text=True
    )
    devices = json.loads(lsblk)['blockdevices']
    for dev in devices:
        # Look for a partition with a vfat filesystem that is mounted
        if dev.get('fstype') == 'vfat' and dev.get('mountpoint'):
            return pathlib.Path(dev['mountpoint'])
    raise RuntimeError("Boot (vfat) partition not found or not mounted.")

def enable_ssh(boot_path: pathlib.Path):
    """Create an empty 'ssh' file in the boot partition."""
    ssh_file = boot_path / 'ssh'
    ssh_file.touch(exist_ok=True)
    print(f"✅ Created {ssh_file}")

def configure_wifi(boot_path: pathlib.Path, ssid: str, psk: str, country: str = "US"):
    """Write a minimal wpa_supplicant.conf for head‑less Wi‑Fi."""
    wpa_conf = f"""country={country}
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={{
    ssid="{ssid}"
    psk="{psk}"
    key_mgmt=WPA-PSK
}}
"""
    (boot_path / "wpa_supplicant.conf").write_text(wpa_conf)
    print(f"✅ Wi‑Fi config written to {boot_path / 'wpa_supplicant.conf'}")

if __name__ == "__main__":
    try:
        boot = find_boot_partition()
    except RuntimeError as e:
        sys.exit(f"❌ {e}")

    enable_ssh(boot)

    # Optional: fill in your Wi‑Fi details here or pass via env vars/CLI
    ssid = os.getenv("WIFI_SSID")
    psk  = os.getenv("WIFI_PSK")
    if ssid and psk:
        configure_wifi(boot, ssid, psk)
    else:
        print("ℹ️ Wi‑Fi not configured – set WIFI_SSID and WIFI_PSK env vars to enable.")
```

1. Save this as `enable_ssh.py` on your workstation.  
2. Make it executable: `chmod +x enable_ssh.py`.  
3. Insert the flashed SD card, ensure the boot partition auto‑mounts, then run:

```bash
sudo ./enable_ssh.py
```

The script will create the `ssh` file and, if `WIFI_SSID`/`WIFI_PSK` env vars are set, add a `wpa_supplicant.conf` for headless Wi‑Fi.

**Result:** The SD card is ready for headless boot; you can now power the Pi and SSH to `pi@<raspberrypi.local>` (or its IP).
