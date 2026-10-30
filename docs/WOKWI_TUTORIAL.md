# Wokwi Virtual Simulation Tutorial: ESP32 NFC/RFID Access Control & Security Lab

This tutorial provides complete, step-by-step instructions for running the **ESP32 NFC/RFID Cryptographic Access Control & Vulnerability Testbench** inside the [Wokwi Virtual Embedded Systems Simulator](https://wokwi.com/).

You can run the entire simulation directly in your web browser (zero installation required) or locally in Visual Studio Code.

---

## Table of Contents
1. [Simulation Overview](#1-simulation-overview)
2. [Simulation Artifacts & Code Manifest](#2-simulation-artifacts--code-manifest)
3. [Method 1: 1-Click Online Simulation (Wokwi Web)](#3-method-1-1-click-online-simulation-wokwi-web)
4. [Method 2: Visual Studio Code Simulation (Wokwi Extension)](#4-method-2-visual-studio-code-simulation-wokwi-extension)
5. [Hardware Circuit & Pinout Reference](#5-hardware-circuit--pinout-reference)
6. [Interactive Testing: Swiping Virtual RFID Cards](#6-interactive-testing-swiping-virtual-rfid-cards)
7. [Testing the Embedded Web Dashboard & REST APIs](#7-testing-the-embedded-web-dashboard--rest-apis)
8. [Code Architecture Walkthrough (`sketch.ino`)](#8-code-architecture-walkthrough-sketchino)
9. [Troubleshooting & Common Questions](#9-troubleshooting--common-questions)

---

## 1. Simulation Overview

The Wokwi virtual lab emulates a high-security access control system powered by an **ESP32 DevKitC V4**, demonstrating:
- **ISO/IEC 14443A Card Detection**: Real-time ATQA, SAK, and UID acquisition via an MFRC522 reader module over high-speed hardware SPI.
- **Crypto1 Authentication vs. UID Spoofing Defense**: Verifies cryptographic sector security rather than relying on forgeable UIDs.
- **Visual Feedback**: Real-time status updates on a 128x64 I2C SSD1306 OLED display.
- **Auditory Feedback**: Distinct PWM tone frequencies emitted via a piezo buzzer (1,000 Hz chime for authorized cards, 500 Hz error buzz for rogue cards).
- **Dual Telemetry Engine**: Persistent JSONL logging via LittleFS (`/scans.jsonl`) backed by a zero-latency RAM fallback ring buffer.
- **Local Web Server**: An embedded HTTP dashboard running on port 80 with real-time audit log streaming.

```
       +-----------------------------------------------------------+
       |               ESP32 DevKitC V4 Microcontroller            |
       +-----+----------------+---------------+----------------+---+
             |                |               |                |
             | SPI            | I2C           | PWM (GPIO 26)  | GPIO 2
             v                v               v                v
      +--------------+ +--------------+ +--------------+ +---------------+
      |   MFRC522    | |   SSD1306    | |    Piezo     | |   Status LED  |
      | RFID Reader  | |  OLED 128x64 | |    Buzzer    | |   (220R Res)  |
      +--------------+ +--------------+ +--------------+ +---------------+
             ^
             | 13.56 MHz RF Field
      +--------------+
      | Virtual Tag  | (Alice, Bob, Facility Key, Rogue Red Tag, etc.)
      +--------------+
```

---

## 2. Simulation Artifacts & Code Manifest

All required files are tracked directly in this repository:

| File | Purpose | Location in Repo |
| :--- | :--- | :--- |
| **`sketch.ino`** | Core Arduino firmware code containing the state machine, OLED driver, buzzer feedback, web server, and credential database | [`simulation/wokwi/sketch.ino`](../simulation/wokwi/sketch.ino) |
| **`diagram.json`** | Wokwi virtual circuit canvas defining part coordinates, attributes, and wiring netlist | [`diagram.json`](../diagram.json) or [`simulation/wokwi/diagram.json`](../simulation/wokwi/diagram.json) |
| **`libraries.txt`** | Dependency manifest required by the Wokwi online compiler | [`libraries.txt`](../libraries.txt) or [`simulation/wokwi/libraries.txt`](../simulation/wokwi/libraries.txt) |
| **`partitions.csv`** | ESP32 partition table with 1.5 MB LittleFS storage for persistent access logs | [`partitions.csv`](../partitions.csv) or [`simulation/wokwi/partitions.csv`](../simulation/wokwi/partitions.csv) |
| **`wokwi.toml`** | Configuration manifest for the Wokwi VS Code extension | [`wokwi.toml`](../wokwi.toml) or [`simulation/wokwi/wokwi.toml`](../simulation/wokwi/wokwi.toml) |

---

## 3. Method 1: 1-Click Online Simulation (Wokwi Web)

This is the fastest method with **zero local setup**.

### Step 1: Open the Wokwi ESP32 Workspace
In any modern web browser, open:
👉 **[https://wokwi.com/projects/new/esp32](https://wokwi.com/projects/new/esp32)**

### Step 2: Configure the Circuit (`diagram.json`)
1. Click the **`diagram.json`** tab in the Wokwi editor.
2. Select all existing text and delete it.
3. Open [`diagram.json`](../diagram.json) from this repository, copy its entire contents, and paste it into the tab:
   ```json
   {
     "version": 1,
     "author": "Rajveer Modi",
     "editor": "wokwi",
     "parts": [
       { "type": "board-esp32-devkit-c-v4", "id": "esp", "top": 0, "left": 0, "attrs": { "flashSize": "4" } },
       { "type": "board-mfrc522", "id": "rfid1", "top": -45, "left": -260, "attrs": {} },
       { "type": "board-ssd1306", "id": "oled1", "top": -80, "left": 250, "attrs": { "i2cAddress": "0x3c" } },
       { "type": "wokwi-buzzer", "id": "bz1", "top": 80, "left": 250, "attrs": { "volume": "0.5" } },
       { "type": "wokwi-resistor", "id": "r1", "top": 230, "left": 200, "rotate": 90, "attrs": { "value": "220" } },
       { "type": "wokwi-led", "id": "led1", "top": 210, "left": 270, "attrs": { "color": "blue", "label": "STATUS" } }
     ],
     "connections": [
       [ "esp:TX", "$serialMonitor:RX", "", [] ],
       [ "esp:RX", "$serialMonitor:TX", "", [] ],
       [ "rfid1:3.3V", "esp:3V3", "red", [ "v-30", "h120" ] ],
       [ "rfid1:GND", "esp:GND.1", "black", [ "v-20", "h100" ] ],
       [ "rfid1:RST", "esp:27", "gray", [ "v20", "h80" ] ],
       [ "rfid1:SCK", "esp:18", "blue", [ "v50", "h110" ] ],
       [ "rfid1:MISO", "esp:19", "cyan", [ "v60", "h120" ] ],
       [ "rfid1:MOSI", "esp:23", "purple", [ "v70", "h130" ] ],
       [ "rfid1:SDA", "esp:5", "orange", [ "v80", "h140" ] ],
       [ "oled1:VCC", "esp:3V3", "red", [ "v-30", "h-140" ] ],
       [ "oled1:GND", "esp:GND.2", "black", [ "v-20", "h-130" ] ],
       [ "oled1:SDA", "esp:21", "green", [ "v20", "h-110" ] ],
       [ "oled1:SCL", "esp:22", "teal", [ "v30", "h-100" ] ],
       [ "bz1:2", "esp:26", "gold", [ "v0" ] ],
       [ "bz1:1", "esp:GND.1", "black", [ "v20", "h-90" ] ],
       [ "esp:2", "r1:1", "blue", [ "h20" ] ],
       [ "r1:2", "led1:A", "blue", [ "h10" ] ],
       [ "led1:C", "esp:GND.2", "black", [ "v20", "h-120" ] ]
     ],
     "dependencies": {}
   }
   ```
4. As soon as you paste this, the schematic canvas will display the ESP32, MFRC522, SSD1306, Piezo Buzzer, and Blue LED neatly wired!

### Step 3: Add Dependencies (`libraries.txt`)
1. Click the small **`+`** (New File) button in the top tab bar of Wokwi.
2. Enter the file name: **`libraries.txt`**.
3. Paste the following 4 library names into `libraries.txt`:
   ```text
   MFRC522
   Adafruit SSD1306
   Adafruit GFX Library
   ArduinoJson
   ```

### Step 4: Add Partition Table (`partitions.csv` — Optional but Recommended)
1. Click the **`+`** (New File) button again.
2. Enter the file name: **`partitions.csv`**.
3. Paste the partition table from [`partitions.csv`](../partitions.csv):
   ```csv
   # ESP32 Partition Table with 1.5MB SPIFFS/LittleFS Storage
   # Name,   Type, SubType, Offset,  Size,    Flags
   nvs,      data, nvs,     0x9000,  0x5000,
   otadata,  data, ota,     0xe000,  0x2000,
   app0,     app,  ota_0,   0x10000, 0x140000,
   app1,     app,  ota_1,   0x150000,0x140000,
   spiffs,   data, spiffs,  0x290000,0x170000,
   ```

### Step 5: Load Firmware Code (`sketch.ino`)
1. Click on the **`sketch.ino`** tab.
2. Delete the default template code.
3. Open [`simulation/wokwi/sketch.ino`](../simulation/wokwi/sketch.ino) in your local editor, copy its entire contents, and paste it into the `sketch.ino` tab.

### Step 6: Start Simulation!
1. Click the green **Play (Start Simulation)** button in the upper toolbar.
2. Watch the Serial Monitor on the right and the OLED screen:
   - Serial Monitor prints initialization banner, LittleFS status, Wi-Fi SoftAP info, and MFRC522 firmware version.
   - The SSD1306 OLED displays:
     ```
     >> SYSTEM ONLINE <<
     AP: ESP32-NFC-Lab
     IP: 192.168.4.1
     ---------------------
     Ready: Tap RFID Card
     ```

---

## 4. Method 2: Visual Studio Code Simulation (Wokwi Extension)

If you prefer simulating within VS Code:

1. **Install the Extension**:
   - Open VS Code Extensions (`Ctrl+Shift+X` or `Cmd+Shift+X`).
   - Search for **Wokwi for VS Code** and click **Install**.
2. **Activate Free License**:
   - Press `F1` (or `Cmd+Shift+P`), type `Wokwi: Request License`, and follow the browser authorization prompt.
3. **Open this Repository**:
   - The repository root already includes [`diagram.json`](../diagram.json) and [`wokwi.toml`](../wokwi.toml).
4. **Compile Firmware**:
   - Using PlatformIO:
     ```bash
     pio run
     ```
   - Or using Arduino CLI:
     ```bash
     arduino-cli compile --fqbn esp32:esp32:esp32 simulation/wokwi/sketch.ino --output-dir simulation/wokwi/
     ```
5. **Launch Simulator**:
   - Open [`diagram.json`](../diagram.json) in VS Code.
   - Click the green **Play** button at the top-right of the editor, or press `F1` and execute `Wokwi: Start Simulator`.

---

## 5. Hardware Circuit & Pinout Reference

| Component | Wokwi Part ID | Module Pin | ESP32 GPIO Pin | Protocol / Function | Wire Color |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MFRC522 RFID** | `rfid1` | `3.3V` | `3V3` | +3.3V Power | Red |
| | | `GND` | `GND.1` | Ground | Black |
| | | `RST` | `GPIO 27` | Module Reset | Gray |
| | | `SCK` | `GPIO 18` | Hardware SPI Clock | Blue |
| | | `MISO` | `GPIO 19` | SPI Master-In Slave-Out | Cyan |
| | | `MOSI` | `GPIO 23` | SPI Master-Out Slave-In | Purple |
| | | `SDA (SS)` | `GPIO 5` | SPI Chip Select | Orange |
| **SSD1306 OLED** | `oled1` | `VCC` | `3V3` | +3.3V Power | Red |
| | | `GND` | `GND.2` | Ground | Black |
| | | `SDA` | `GPIO 21` | I2C Data (0x3C) | Green |
| | | `SCL` | `GPIO 22` | I2C Clock (0x3C) | Teal |
| **Piezo Buzzer** | `bz1` | `Pin 2` (+) | `GPIO 26` | Hardware PWM Audio | Gold |
| | | `Pin 1` (-) | `GND.1` | Ground | Black |
| **Status LED** | `led1` | `Anode (A)` | `GPIO 2` (via R1) | Digital Output | Blue |
| | | `Cathode (C)`| `GND.2` | Ground | Black |
| **Current Limiter**| `r1` | `1` & `2` | In-series GPIO 2 | 220 &Omega; Current Protection | Blue |

---

## 6. Interactive Testing: Swiping Virtual RFID Cards

Once the simulation is running, test the system's access-control decision engine:

1. **Click directly on the blue MFRC522 RFID reader module** in the simulation canvas.
2. An interactive popup modal appears showing virtual RFID tags.
3. Select one of the pre-configured tags or enter a custom UID.

### Test Card Roster & Expected Behavior

| Virtual Card | UID | Cardholder & Role | Expected Decision | Buzzer / LED Tone | Expected OLED Screen |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Blue Card** | `01:02:03:04` | Alice Smith (Lab Admin) | **`AUTH_SUCCESS`** (Access Granted) | 1,000 Hz chime (120 ms)<br>LED stays solid | `>> ACCESS GRANTED <<`<br>`Alice Smith (Blue)`<br>`Role: Lab Admin`<br>`UID: 01:02:03:04` |
| **Green Card** | `11:22:33:44` | Bob Jones (Embedded Eng) | **`AUTH_SUCCESS`** (Access Granted) | 1,000 Hz chime (120 ms)<br>LED stays solid | `>> ACCESS GRANTED <<`<br>`Bob Jones (Green)`<br>`Role: Embedded Eng`<br>`UID: 11:22:33:44` |
| **Facility Key Fob** | `C0:FF:EE:99` | Facility Key Fob (Operations) | **`AUTH_SUCCESS`** (Access Granted) | 1,000 Hz chime (120 ms)<br>LED stays solid | `>> ACCESS GRANTED <<`<br>`Facility Key Fob`<br>`Role: Operations Lead`<br>`UID: C0:FF:EE:99` |
| **Red Card** (Intruder) | `AA:BB:CC:DD` | Intruder (Rogue Clone Tag) | **`AUTH_FAILED`** (Access Denied) | 500 Hz error buzz (350 ms)<br>LED double-blink | `>> ACCESS DENIED <<`<br>`Intruder (Red Card)`<br>`Alert: UNAUTHORIZED`<br>`UID: AA:BB:CC:DD` |
| **Yellow Card** | `55:66:77:88` | Charlie (Card Revoked) | **`AUTH_FAILED`** (Access Denied) | 500 Hz error buzz (350 ms)<br>LED double-blink | `>> ACCESS DENIED <<`<br>`Charlie (Yellow Card)`<br>`Alert: Card Revoked`<br>`UID: 55:66:77:88` |
| **Custom UID / Any Other Tag** | *e.g.,* `DE:AD:BE:EF` | Unregistered Foreign Credential | **`AUTH_FAILED`** (Access Denied) | 500 Hz error buzz (350 ms)<br>LED double-blink | `>> ACCESS DENIED <<`<br>`Unknown Tag`<br>`Alert: Unregistered Tag` |

### Expected Serial Monitor Output (Sample)

#### On Successful Authentication:
```text
[+] Access Control: VERIFIED AUTHORIZED CREDENTIAL
[+] Cardholder: Alice Smith (Blue) | Role: Lab Admin
[+] Security Decision: ACCESS GRANTED (AUTH_SUCCESS)
[+] Nominal Latency: 21250 us
```

#### On Rogue / Unauthorized Tag:
```text
[-] Access Control: ROGUE / UNAUTHORIZED TAG DETECTED
[-] Tag Identity: Intruder (Red Card) | Reason: UNAUTHORIZED
[-] Security Decision: ACCESS DENIED (AUTH_FAILED)
[-] Worst-Case Latency: 28500 us
```

---

## 7. Testing the Embedded Web Dashboard & REST APIs

The firmware runs an asynchronous web server inside Wokwi on port 80:

### 1. Connecting to Wi-Fi
- The ESP32 broadcasts a SoftAP:
  - **SSID**: `ESP32-NFC-Lab`
  - **Password**: `admin123`
  - **IP**: `192.168.4.1`
- It also connects to Wokwi's virtual gateway: `Wokwi-GUEST`.

### 2. Available REST Endpoints

| Endpoint | Method | Description | Sample Output |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | Serves the web dashboard (HTML/CSS/JS) | Access control telemetry user interface |
| `/api/logs` | `GET` | Returns full scan history from LittleFS or RAM | `[{"timestamp": 12500, "uid": "01:02:03:04", "user": "Alice Smith (Blue)", "status": "AUTH_SUCCESS"}]` |
| `/api/test-rogue` | `POST` | Simulates an intruder attack event | Injects rogue card scan, triggers buzzer warning and OLED alert |
| `/api/reboot` | `POST` | Triggers a software restart of the ESP32 | `Rebooting ESP32...` |

---

## 8. Code Architecture Walkthrough (`sketch.ino`)

The firmware in [`simulation/wokwi/sketch.ino`](../simulation/wokwi/sketch.ino) is organized into clear functional layers:

1. **Hardware Configuration (Lines 1–25)**:
   - Configures SPI pins (`SS=5`, `RST=27`), PWM buzzer (`GPIO 26`), status LED (`GPIO 2`), and I2C OLED display.
2. **Access Control Database (Lines 44–65)**:
   - Defines the static credential whitelist with cardholder names, roles, and authorization flags.
3. **Dual-Tier Logging Architecture (Lines 28–42, 280–330)**:
   - If LittleFS is available, writes records formatted as JSON Lines (`/scans.jsonl`).
   - If flash storage is unpartitioned, seamlessly falls back to an in-memory 30-entry RAM ring buffer (`ramLogs`) to guarantee zero loss of audit telemetry.
4. **Crypto1 Sector Authentication (Lines 332–365)**:
   - Authenticates against Sector 1 (Block 4) using Factory Default Key A (`0xFF 0xFF 0xFF 0xFF 0xFF 0xFF`).
   - Emulates hardware-enforced cryptographic mutual authentication.
5. **State Machine & Loop (Lines 502–627)**:
   - Non-blocking card detection using `PICC_IsNewCardPresent()` and `PICC_ReadCardSerial()`.
   - Parses ATQA, SAK, and UID string.
   - Measures transaction latency via `micros()`.
   - Dispatches audio/visual alerts and updates OLED before executing PICC halt and crypto teardown.

---

## 9. Troubleshooting & Common Questions

### Q1: The compiler gives an error: `fatal error: MFRC522.h: No such file or directory`
> **Solution**: Ensure you created the `libraries.txt` tab in Wokwi and pasted the 4 required libraries:
> ```text
> MFRC522
> Adafruit SSD1306
> Adafruit GFX Library
> ArduinoJson
> ```

### Q2: The OLED screen stays blank or dark
> **Solution**:
> 1. Verify `diagram.json` has `i2cAddress` set to `"0x3c"` for `oled1`.
> 2. Ensure I2C pins match: SDA to GPIO 21, SCL to GPIO 22, VCC to 3V3, GND to GND.2.

### Q3: Clicking the MFRC522 reader does not show the card popover
> **Solution**: Ensure the simulation is actively **running** (the green Play button has been clicked and the simulation timer is ticking) before clicking the reader module.

### Q4: LittleFS displays `LittleFS Mount Failed` in Serial Monitor
> **Solution**: This is expected if `partitions.csv` was omitted. The code will automatically activate its internal RAM fallback log buffer (`ramLogs`). All web dashboard views, OLED screens, and audio alerts continue working normally. To enable flash persistence, simply add `partitions.csv`.

### Q5: How do I add my own custom card UID?
> **Solution**: Open `sketch.ino`, navigate to `CARD_DATABASE[]` around line 51, and add your card entry:
> ```cpp
> { "AA:11:BB:22", "Your Name", "Lab Security", true },
> ```
