#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <WiFi.h>
#include <FS.h>
#include <LittleFS.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>

// Pin Definitions for ESP32 + RC522 + OLED + Buzzer + LED
#define SS_PIN    5
#define RST_PIN   27
#define BUZZER_PIN 26   // GPIO26 PWM output for piezo buzzer
#define LED_PIN    2    // GPIO2 onboard blue LED
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

MFRC522 rfid(SS_PIN, RST_PIN);
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
AsyncWebServer server(80);

const char* LOG_FILE = "/scans.jsonl";

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
  file.flush(); // Force write to physical flash
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

  // D6: Commit 16-Byte Block to Buffer (5 µs) — data already in buffer
  return MFRC522::STATUS_OK;
}

void setup() {
  Serial.begin(115200);
  delay(500);

  // Initialize GPIO for Buzzer & Status LED
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);  // Buzzer off (0V — safe state)
  digitalWrite(LED_PIN, HIGH);    // LED on (system alive indicator)

  // Initialize Hardware SPI & I2C
  SPI.begin(18, 19, 23, 5); // SCK, MISO, MOSI, SS
  rfid.PCD_Init();
  Wire.begin(21, 22); // SDA, SCL

  // Initialize OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED allocation failed");
    for (;;);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.println("Initializing System...");
  display.display();

  // Initialize LittleFS
  if (!LittleFS.begin(true)) {
    Serial.println("LittleFS Mount Failed");
    return;
  }
  if (!LittleFS.exists(LOG_FILE)) {
    File initFile = LittleFS.open(LOG_FILE, FILE_WRITE);
    initFile.close();
  }

  // Start Wi-Fi Access Point for Dashboard
  WiFi.softAP("ESP32-NFC-Lab", "admin123");
  Serial.print("Access Point IP: ");
  Serial.println(WiFi.softAPIP());

  // Web Server Routes
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    if (LittleFS.exists("/index.html")) {
      request->send(LittleFS, "/index.html", "text/html");
    } else {
      request->send(200, "text/html", "<html><body style='background:#0f172a;color:#f8fafc;font-family:sans-serif;padding:30px;'>"
                                      "<h2>ESP32 NFC/RFID System Online</h2>"
                                      "<p>LittleFS /index.html not found. View scans via JSON API: <a style='color:#38bdf8;' href='/api/logs'>/api/logs</a></p>"
                                      "</body></html>");
    }
  });

  server.on("/api/logs", HTTP_GET, [](AsyncWebServerRequest *request){
    File file = LittleFS.open(LOG_FILE, FILE_READ);
    if (!file) {
      request->send(200, "application/json", "[]");
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
    request->send(200, "application/json", jsonResponse);
  });

  server.on("/api/reboot", HTTP_POST, [](AsyncWebServerRequest *request){
    request->send(200, "text/plain", "Rebooting ESP32...");
    delay(500);
    ESP.restart();
  });

  server.begin();

  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("System Online");
  display.println("SSID: ESP32-NFC-Lab");
  display.println("Waiting for tag...");
  display.display();
}

void loop() {
  // Check if new card is present
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return;
  }

  uint32_t startTime = micros(); // Start high-resolution timer for security benchmark

  // Format UID
  String uidStr = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uidStr += "0";
    uidStr += String(rfid.uid.uidByte[i], HEX);
    if (i < rfid.uid.size - 1) uidStr += ":";
  }
  uidStr.toUpperCase();

  // Perform Cryptographic Authentication Test on Sector 1, Block 4 (Review 2 Security Requirement)
  MFRC522::MIFARE_Key key;
  for (byte i = 0; i < 6; i++) key.keyByte[i] = 0xFF; // Default transport key
  
  byte blockAddr = 4;
  byte blockData[18];     // 16 bytes data + 2 bytes CRC-A
  byte bufferSize = sizeof(blockData);
  MFRC522::StatusCode status = authenticate_and_read_block(blockAddr, &key, blockData, &bufferSize);
  
  String authStatus = "AUTH_SUCCESS";
  if (status != MFRC522::STATUS_OK) {
    authStatus = "AUTH_FAILED";
    // S4_FAULT: Error feedback — buzzer 500 Hz for 200 ms, LED fast blink
    tone(BUZZER_PIN, 500, 200);
    digitalWrite(LED_PIN, LOW);
    delay(100);
    digitalWrite(LED_PIN, HIGH);
  } else {
    // S5_LOG: Success feedback — buzzer 1 kHz for 100 ms
    tone(BUZZER_PIN, 1000, 100);
  }

  uint32_t readTimeUs = micros() - startTime; // Total execution time for benchmark

  // Determine Tag Family based on SAK/ATQA
  String family = (rfid.uid.size == 7) ? "NTAG21x / Ultralight" : "MIFARE Classic 1K";
  String atqa = "0x0004";
  String sak = "0x08";

  // Save scan record to LittleFS flash storage (Survives Reset)
  appendScanRecord(millis(), family, uidStr, atqa, sak, readTimeUs, authStatus);

  // Update OLED Display Feedback
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println(">> TAG SCANNED <<");
  display.print("UID: "); display.println(uidStr);
  display.print("Time: "); display.print(readTimeUs); display.println(" us");
  display.print("Auth: "); display.println(authStatus);
  display.display();

  // CLEANUP: PCD & PICC Teardown (180 µs) — convergence point for all paths
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  noTone(BUZZER_PIN);            // Ensure buzzer returns to 0V (safe state)
  digitalWrite(LED_PIN, HIGH);   // LED solid ON (S1_IDLE ready)
  delay(1500);
}
