# ESP32 NFC/RFID Virtual Lab — Wokwi Simulation Environment

This directory contains the complete virtual simulation model for the **ESP32 NFC/RFID Vulnerability & Access Control Research Testbench**.

---

## 1. Circuit Architecture & Pinout Mapping

| Component | Wokwi Part Type | Component Pin | ESP32 DevKitC V4 Pin | Interface / Protocol | Wire Color |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MFRC522 RFID** | `board-mfrc522` | `3.3V` | `3V3` | Power (+3.3V Logic) | Red |
| | | `GND` | `GND.1` | Ground Reference | Black |
| | | `RST` | `GPIO 27` (`esp:27`) | Hardware Reset | Gray / Orange |
| | | `SCK` | `GPIO 18` (`esp:18`) | SPI Bus Clock | Blue |
| | | `MISO` | `GPIO 19` (`esp:19`) | SPI Master In Slave Out | Cyan |
| | | `MOSI` | `GPIO 23` (`esp:23`) | SPI Master Out Slave In | Purple |
| | | `SDA (SS)` | `GPIO 5` (`esp:5`) | SPI Chip Select | Gold / Orange |
| **SSD1306 OLED** | `board-ssd1306` | `VCC` | `3V3` | Power (+3.3V) | Red |
| | | `GND` | `GND.2` | Ground Reference | Black |
| | | `SDA` | `GPIO 21` (`esp:21`) | I2C Data Line (0x3C) | Green |
| | | `SCL` | `GPIO 22` (`esp:22`) | I2C Clock Line (0x3C) | Teal |
| **Piezo Buzzer** | `wokwi-buzzer` | `2` (Positive) | `GPIO 26` (`esp:26`) | Hardware PWM Audio | Gold |
| | | `1` (Negative) | `GND.1` | Ground Reference | Black |
| **Status LED** | `wokwi-led` | `A` (Anode via R1) | `GPIO 2` (`esp:2`) | Digital GPIO Output | Blue |
| | | `C` (Cathode) | `GND.2` | Ground Reference | Black |
| **Current Resistor**| `wokwi-resistor` | `1` & `2` | Between `GPIO 2` & LED `A` | 220 &Omega; Current Limiting | Blue |

---

## 2. How to Run the Simulation

### Option A: 1-Click Browser Simulation (Wokwi Web)
1. Navigate to [wokwi.com/new/esp32](https://wokwi.com/projects/new/esp32).
2. Click on the **`diagram.json`** tab and paste the contents of [`diagram.json`](file:///Users/rajveermodi/Documents/GitHub/esp32-nfc/diagram.json).
3. Click on the **`sketch.ino`** tab and paste the contents of [`sketch.ino`](file:///Users/rajveermodi/Documents/GitHub/esp32-nfc/simulation/wokwi/sketch.ino).
4. Click the small **`+`** (New File) tab and create **`libraries.txt`**, pasting [`libraries.txt`](file:///Users/rajveermodi/Documents/GitHub/esp32-nfc/simulation/wokwi/libraries.txt).
5. (Optional for Flash Persistence): Click **`+`** to create **`partitions.csv`**, pasting [`partitions.csv`](file:///Users/rajveermodi/Documents/GitHub/esp32-nfc/simulation/wokwi/partitions.csv) to allocate 1.5MB LittleFS storage.
6. Click the green **Play (Start Simulation)** button.

### Option B: Visual Studio Code (Wokwi Extension)
1. Install the official **Wokwi for VS Code** extension from the Extension Marketplace.
2. Ensure `wokwi.toml` and `diagram.json` are present in your workspace root (already pre-configured).
3. Build your project via PlatformIO or Arduino CLI:
   ```bash
   pio run
   ```
4. Press `F1`, type `Wokwi: Start Simulator`, or click the Play icon in the top right of `diagram.json`.

---

## 3. Interactive Testing in Wokwi

1. **Card Detection & UID Emulation:**
   - While the simulation is running, **click on the blue MFRC522 reader module**.
   - An interactive popover appears displaying virtual cards (e.g., *Blue Card*, *Green Card*, or custom UID inputs).
   - Select a card or click **Tap Card** to simulate a physical ISO 14443A card swipe.
2. **Real-time OLED Feedback:**
   - The SSD1306 OLED (128x64) immediately refreshes showing:
     - Tag UID (e.g., `01:02:03:04`)
     - Tag Family (`MIFARE Classic 1K` or `NTAG21x`)
     - Mutual authentication latency in microseconds (&micro;s)
     - Crypto1 Authentication status (`AUTH_SUCCESS` or `AUTH_FAILED`)
3. **Auditory & Visual Indicators:**
   - **Auth Success:** Piezo buzzer emits a high-pitched 1,000 Hz chime (100 ms) and LED stays solid.
   - **Auth Failure / Fault:** Piezo buzzer emits an error tone at 500 Hz (200 ms) and Status LED blinks.
4. **Persistent Web Dashboard:**
   - Connect your simulated browser to the ESP32 Wi-Fi AP (`ESP32-NFC-Lab`) or visit the virtual gateway URL printed in the Serial Monitor.
   - The embedded LittleFS dashboard automatically parses `/scans.jsonl` and renders historical records with zero server refresh lag.
