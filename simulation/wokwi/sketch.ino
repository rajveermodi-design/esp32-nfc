#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <WiFi.h>
#include <FS.h>
#include <LittleFS.h>
#include <WebServer.h>
#include <ArduinoJson.h>

// Pin Definitions matching Wokwi diagram.json & System Block Diagram
#define SS_PIN      5    // SPI Slave Select (SDA on MFRC522)
#define RST_PIN     27   // MFRC522 Reset
#define BUZZER_PIN  26   // GPIO26 PWM output for piezo buzzer
#define LED_PIN     2    // GPIO2 indicator LED
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

MFRC522 rfid(SS_PIN, RST_PIN);
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
WebServer server(80);

const char* LOG_FILE = "/scans.jsonl";

// Built-in HTML Dashboard fallback for LittleFS in Wokwi simulator
const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ESP32 RFID/NFC Security Dashboard (Wokwi Virtual)</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --success: #22c55e;
      --danger: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    body { background-color: var(--bg); color: var(--text); padding: 24px; }
    .container { max-width: 1000px; margin: 0 auto; }
    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }
    h1 { font-size: 1.5rem; font-weight: 700; }
    .status-badge { display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; background: rgba(34, 197, 94, 0.1); color: var(--success); border-radius: 9999px; font-size: 0.85rem; font-weight: 600; border: 1px solid rgba(34, 197, 94, 0.2); }
    .status-dot { width: 8px; height: 8px; background: var(--success); border-radius: 50%; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .card { background: var(--card-bg); padding: 16px; border-radius: 8px; border: 1px solid var(--border); }
    .card-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px; }
    .card-value { font-size: 1.25rem; font-weight: 700; color: var(--accent); }
    .controls { display: flex; gap: 12px; margin-bottom: 24px; }
    button { padding: 10px 16px; font-size: 0.85rem; font-weight: 600; border-radius: 6px; border: 1px solid var(--border); background: var(--card-bg); color: var(--text); cursor: pointer; transition: all 0.2s; }
    button:hover { background: var(--border); }
    button.btn-danger { background: rgba(239, 68, 68, 0.1); color: var(--danger); border-color: rgba(239, 68, 68, 0.2); }
    table { width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }
    th, td { padding: 12px 16px; text-align: left; font-size: 0.85rem; }
    th { background: #111e33; color: var(--text-muted); font-weight: 600; border-bottom: 1px solid var(--border); }
    td { border-bottom: 1px solid rgba(51, 65, 85, 0.5); font-family: monospace; }
    tr:last-child td { border-bottom: none; }
    .badge { padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
    .badge-mifare { background: #3b82f6; color: white; }
    .badge-ntag { background: #8b5cf6; color: white; }
    .badge-auth { background: rgba(34, 197, 94, 0.2); color: var(--success); }
    .badge-fail { background: rgba(239, 68, 68, 0.2); color: var(--danger); }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>ESP32 RFID/NFC Virtual Lab Console</h1>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 4px;">Wokwi Simulation Environment (Virtual System)</p>
      </div>
      <div class="status-badge"><span class="status-dot"></span> System Online</div>
    </header>

    <div class="grid">
      <div class="card">
        <div class="card-label">Total Persistent Scans</div>
        <div class="card-value" id="scan-count">0</div>
      </div>
      <div class="card">
        <div class="card-label">Last Tag Family</div>
        <div class="card-value" id="last-family">--</div>
      </div>
      <div class="card">
        <div class="card-label">Avg Auth Latency</div>
        <div class="card-value" id="avg-latency">-- &micro;s</div>
      </div>
    </div>

    <div class="controls">
      <button onclick="fetchLogs()">Refresh Logs</button>
      <button class="btn-danger" onclick="triggerReboot()">Test Hardware Reboot</button>
    </div>

    <table>
      <thead>
        <tr>
          <th>Timestamp (ms)</th>
          <th>Tag Family</th>
          <th>UID (Hex)</th>
          <th>ATQA / SAK</th>
          <th>Auth Read Time</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody id="log-table-body">
        <tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No scan records in flash storage. Approximate a card to the reader in Wokwi!</td></tr>
      </tbody>
    </table>
  </div>

  <script>
    async function fetchLogs() {
      try {
        const response = await fetch('/api/logs');
        const data = await response.json();
        const tbody = document.getElementById('log-table-body');
        
        if (!data || data.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No scan records in flash storage</td></tr>';
          document.getElementById('scan-count').innerText = '0';
          return;
        }

        document.getElementById('scan-count').innerText = data.length;
        document.getElementById('last-family').innerText = data[data.length - 1].family || '--';
        document.getElementById('avg-latency').innerHTML = (data[data.length - 1].read_time_us || '--') + ' &micro;s';

        tbody.innerHTML = data.reverse().map(item => `
          <tr>
            <td>${item.timestamp}</td>
            <td><span class="badge ${item.family.includes('NTAG') ? 'badge-ntag' : 'badge-mifare'}">${item.family}</span></td>
            <td><strong>${item.uid}</strong></td>
            <td>${item.atqa} / ${item.sak}</td>
            <td>${item.read_time_us} &micro;s</td>
            <td><span class="badge ${item.status === 'AUTH_SUCCESS' ? 'badge-auth' : 'badge-fail'}">${item.status}</span></td>
          </tr>
        `).join('');
      } catch (err) {
        console.error('Failed to load logs:', err);
      }
    }

    async function triggerReboot() {
      if (confirm('Reboot ESP32? All logs will persist in LittleFS virtual flash storage.')) {
        await fetch('/api/reboot', { method: 'POST' });
        alert('Reboot command dispatched. Refreshing page...');
        setTimeout(fetchLogs, 3000);
      }
    }

    fetchLogs();
    setInterval(fetchLogs, 2500);
  </script>
</body>
</html>
)rawliteral";

// Helper to append scan logs to LittleFS flash memory
void appendScanRecord(uint32_t timestamp, String family, String uid, String atqa, String sak, uint32_t readTimeUs, String status) {
  File file = LittleFS.open(LOG_FILE, FILE_APPEND);
  if (!file) return;
  
  StaticJsonDocument<256> doc;
  doc["timestamp"] = timestamp;
  doc["family"] = family;
  doc["uid"] = uid;
  doc["atqa"] = atqa;
  doc["sak"] = sak;
  doc["read_time_us"] = readTimeUs;
  doc["status"] = status;

  serializeJson(doc, file);
  file.println();
  file.flush();
  file.close();
}

// Critical function: Authenticate and read a single block from MIFARE Classic tag
// Modeled as CDFG critical path — WCET: 28,500 µs | Deadline: 35,000 µs | Slack: 6,500 µs
MFRC522::StatusCode authenticate_and_read_block(byte blockAddr, MFRC522::MIFARE_Key *key, byte *buffer, byte *bufferSize) {
  // D1: Load Key A & UID Operands (2 µs)
  // C1: SPI Bus Ready? — implicit in PCD_Authenticate
  // D2: Transmit MF_AUTH Command (16 µs) + C2: Tag Handshake Ack (1,480 µs)
  // D3: LFSR Init & Reader Encrypt (42 µs) + D4: Challenge Response (5,200 µs)
  // C3: Mutual Auth OK? (6,800 µs)
  MFRC522::StatusCode status = rfid.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, blockAddr, key, &(rfid.uid));
  if (status != MFRC522::STATUS_OK) {
    return status;  // ERR: Auth Rejection / Timeout
  }

  // D5: Transmit Read Block Cmd (18 µs)
  // C4: Payload CRC-A Valid? (22 µs) — ISO 14443-3 CRC-A checksum
  status = rfid.MIFARE_Read(blockAddr, buffer, bufferSize);
  if (status != MFRC522::STATUS_OK) {
    return status;  // ERR: CRC-A Mismatch / Read Failure
  }

  // D6: Commit 16-Byte Block to Buffer (5 µs)
  return MFRC522::STATUS_OK;
}

void setup() {
  Serial.begin(115200);
  delay(300);

  Serial.println("\n=============================================");
  Serial.println("  ESP32 NFC/RFID System (Wokwi Virtual Setup)");
  Serial.println("=============================================");

  // Initialize GPIO for Buzzer & Status LED
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);  // Buzzer off (0V — safe state)
  digitalWrite(LED_PIN, HIGH);    // LED on (system alive indicator)

  // Initialize Hardware SPI & I2C
  SPI.begin(18, 19, 23, 5); // SCK=18, MISO=19, MOSI=23, SS=5
  rfid.PCD_Init();
  Wire.begin(21, 22);       // SDA=21, SCL=22

  // Initialize OLED Display (0x3C)
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("[-] OLED allocation failed");
  } else {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 0);
    display.println("ESP32-NFC Virtual Lab");
    display.println("Wokwi Simulation");
    display.println("Init LittleFS...");
    display.display();
    Serial.println("[+] OLED display initialized at 0x3C");
  }

  // Initialize LittleFS flash storage
  if (!LittleFS.begin(true)) {
    Serial.println("[-] LittleFS Mount Failed");
  } else {
    Serial.println("[+] LittleFS mounted successfully (4MB Partition)");
    if (!LittleFS.exists(LOG_FILE)) {
      File initFile = LittleFS.open(LOG_FILE, FILE_WRITE);
      initFile.close();
    }
  }

  // Wi-Fi Setup: Start SoftAP and connect to Wokwi virtual Wi-Fi
  WiFi.softAP("ESP32-NFC-Lab", "admin123");
  Serial.print("[+] SoftAP active. SSID: 'ESP32-NFC-Lab' | IP: ");
  Serial.println(WiFi.softAPIP());

  WiFi.begin("Wokwi-GUEST", "");
  Serial.println("[*] Connecting to Wokwi-GUEST virtual Wi-Fi...");

  // Web Server Routes (Using ESP32 Core Native WebServer — No mbedtls conflicts)
  server.on("/", HTTP_GET, [](){
    if (LittleFS.exists("/index.html")) {
      File f = LittleFS.open("/index.html", "r");
      server.streamFile(f, "text/html");
      f.close();
    } else {
      server.send_P(200, "text/html", INDEX_HTML);
    }
  });

  server.on("/api/logs", HTTP_GET, [](){
    File file = LittleFS.open(LOG_FILE, "r");
    if (!file) {
      server.send(200, "application/json", "[]");
      return;
    }
    String jsonResponse = "[";
    bool first = true;
    while (file.available()) {
      String line = file.readStringUntil('\n');
      line.trim();
      if (line.length() > 0) {
        if (!first) jsonResponse += ",";
        jsonResponse += line;
        first = false;
      }
    }
    file.close();
    jsonResponse += "]";
    server.send(200, "application/json", jsonResponse);
  });

  server.on("/api/reboot", HTTP_POST, [](){
    server.send(200, "text/plain", "Rebooting ESP32...");
    delay(500);
    ESP.restart();
  });

  server.begin();
  Serial.println("[+] Web Server listening on port 80");

  // OLED Ready Screen
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println(">> SYSTEM ONLINE <<");
  display.println("AP: ESP32-NFC-Lab");
  display.println("IP: 192.168.4.1");
  display.println("---------------------");
  display.println("Ready: Tap RFID Card");
  display.display();
}

void loop() {
  server.handleClient(); // Handle incoming HTTP requests

  // Check if new card is present
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    delay(20);
    return;
  }

  uint32_t startTime = micros(); // High-resolution timer for security benchmark

  // Format UID string
  String uidStr = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uidStr += "0";
    uidStr += String(rfid.uid.uidByte[i], HEX);
    if (i < rfid.uid.size - 1) uidStr += ":";
  }
  uidStr.toUpperCase();

  Serial.println("\n---------------------------------------------");
  Serial.print("[*] Tag Detected! UID: ");
  Serial.println(uidStr);

  // Perform Cryptographic Authentication Test on Sector 1, Block 4
  MFRC522::MIFARE_Key key;
  for (byte i = 0; i < 6; i++) key.keyByte[i] = 0xFF; // Default transport key
  
  byte blockAddr = 4;
  byte blockData[18];
  byte bufferSize = sizeof(blockData);
  MFRC522::StatusCode status = authenticate_and_read_block(blockAddr, &key, blockData, &bufferSize);
  
  String authStatus = "AUTH_SUCCESS";
  if (status != MFRC522::STATUS_OK) {
    authStatus = "AUTH_FAILED";
    Serial.print("[-] Crypto1 Authentication FAILED: ");
    Serial.println(rfid.GetStatusCodeName(status));
    
    // S4_FAULT: Error feedback — buzzer 500 Hz for 200 ms, LED fast blink
    tone(BUZZER_PIN, 500, 200);
    digitalWrite(LED_PIN, LOW);
    delay(100);
    digitalWrite(LED_PIN, HIGH);
  } else {
    Serial.println("[+] Crypto1 Authentication SUCCESS!");
    // S5_LOG: Success feedback — buzzer 1 kHz for 100 ms
    tone(BUZZER_PIN, 1000, 100);
  }

  uint32_t readTimeUs = micros() - startTime;
  Serial.print("[+] Total Execution Latency: ");
  Serial.print(readTimeUs);
  Serial.println(" us");

  // Determine Tag Family
  String family = (rfid.uid.size == 7) ? "NTAG21x / Ultralight" : "MIFARE Classic 1K";
  String atqa = "0x0004";
  String sak = "0x08";

  // Append scan record to LittleFS flash
  appendScanRecord(millis(), family, uidStr, atqa, sak, readTimeUs, authStatus);

  // Update OLED Display
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println(">> TAG SCANNED <<");
  display.print("UID: "); display.println(uidStr);
  display.print("Type: "); display.println(family);
  display.print("Time: "); display.print(readTimeUs); display.println(" us");
  display.print("Auth: "); display.println(authStatus);
  display.display();

  // Teardown & Safe State Transition
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  noTone(BUZZER_PIN);
  digitalWrite(LED_PIN, HIGH);

  // Allow web server to process requests during post-scan dwell
  for (int i = 0; i < 20; i++) {
    server.handleClient();
    delay(50);
  }
}
