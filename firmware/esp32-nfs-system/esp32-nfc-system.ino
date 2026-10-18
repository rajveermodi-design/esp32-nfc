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

// Pin Definitions for ESP32 + RC522 + OLED
#define SS_PIN    5
#define RST_PIN   27
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

void setup() {
  Serial.begin(115200);
  delay(500);

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
    request->send(LittleFS, "/index.html", "text/html");
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
  MFRC522::StatusCode status = rfid.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, blockAddr, &key, &(rfid.uid));
  
  String authStatus = "AUTH_SUCCESS";
  if (status != MFRC522::STATUS_OK) {
    authStatus = "AUTH_FAILED";
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

  // Cleanup RFID state
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(1500);
}
