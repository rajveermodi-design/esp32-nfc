#include <WiFi.h>
#include <FS.h>
#include <LittleFS.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>

AsyncWebServer server(80);
const char* LOG_FILE = "/scans.jsonl";

// Append scan record to non-volatile LittleFS storage
void appendScanRecord(uint32_t timestamp, String family, String uid, String atqa, String sak, uint32_t readTimeUs, String status) {
  File file = LittleFS.open(LOG_FILE, FILE_APPEND);
  if (!file) {
    Serial.println("Failed to open log file for appending");
    return;
  }
  
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
  file.flush(); // Ensure write reaches physical flash
  file.close();
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n[BOOT] Starting ESP32 NFC Security System...");

  // Initialize LittleFS Flash Storage
  if (!LittleFS.begin(true)) {
    Serial.println("[ERROR] LittleFS Mount Failed");
    return;
  }
  Serial.println("[STORAGE] LittleFS mounted successfully.");

  // If log file does not exist, initialize it
  if (!LittleFS.exists(LOG_FILE)) {
    File initFile = LittleFS.open(LOG_FILE, FILE_WRITE);
    initFile.close();
    // Seed initial dummy records to test persistence immediately
    appendScanRecord(1204, "MIFARE Classic 1K", "A4:3B:11:0C", "0x0004", "0x08", 2840, "AUTH_SUCCESS");
    appendScanRecord(4510, "NTAG213", "04:88:2E:5A:91:0F:80", "0x0044", "0x00", 940, "UID_READ_ONLY");
    Serial.println("[STORAGE] Initial test records seeded to flash.");
  }

  // Start Access Point
  WiFi.softAP("ESP32-NFC-Lab", "admin123");
  Serial.print("[WIFI] Access Point Active. IP Address: ");
  Serial.println(WiFi.softAPIP());

  // Serve Dashboard Web UI
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    if (LittleFS.exists("/index.html")) {
      request->send(LittleFS, "/index.html", "text/html");
    } else {
      request->send(200, "text/plain", "Dashboard ready. Upload index.html to LittleFS.");
    }
  });

  // REST API: Read persistent logs from flash
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

  // REST API: Software-triggered reboot to test persistence
  server.on("/api/reboot", HTTP_POST, [](AsyncWebServerRequest *request){
    request->send(200, "text/plain", "Rebooting ESP32...");
    delay(500);
    ESP.restart();
  });

  server.begin();
  Serial.println("[HTTP] Web dashboard server listening on port 80.");
}

void loop() {
  // Main state machine: RFID interrupt routines will execute here
}
