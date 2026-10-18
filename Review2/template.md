# Review 2 Architecture Deliverable: CDFG, FSM, and Schedulability

## 1. System Recap & Carried Conditions

### System Context
The device is a dual-mode 13.56 MHz RFID/NFC security analysis terminal built around an ESP32 microcontroller, an RC522/PN532 transponder interface over SPI, a local I2C OLED display, and a non-volatile LittleFS storage engine served via an asynchronous web dashboard.

### Conditions Carried from Proposal Review
| Condition / Mandatory Addition | Status | Where It Is Addressed |
| :--- | :--- | :--- |
| **Written Scope-and-Ethics Statement** | Fully Complied | `docs/ETHICS_AND_SCOPE.md` (Own tags only, no campus testing) |
| **PN532 Emulation Early Test & Fallback** | Fallback Executed | Software simulation via `simulation/pn532_target_sim.py` |
| **Tag Detection across >= 2 Tag Families** | Implemented | Firmware supports MIFARE Classic (4-byte UID) & NTAG21x (7-byte UID) |
| **Data-Block Reading on Provisioned Tag** | Implemented | Sector 1, Block 4 authenticated memory extraction |
| **Security Timing Benchmark** | Documented | Unauthenticated UID (~2.8 ms) vs. Authenticated Block (~30.2 ms) |
| **Wi-Fi Log Surviving Device Reset** | Implemented | LittleFS flash persistence verified across hardware reboot |

---

## 2. Control Data Flow Graph (CDFG)

### 2.1 Candidate Functions Comparison
| Function / ISR | Trigger | Rate | Est. Execution Time | Deadline | Chosen? Why / Why not |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `pn532_isr()` | Hardware IRQ Pin | Event-driven (~2 Hz) | 12 µs | 50 µs | No: Trivial flag-setter; no internal control flow. |
| `update_oled_ui()` | Timer tick | Periodic (5 Hz) | 4,200 µs | 50,000 µs | No: Predictable I2C block transfer; large slack. |
| **`authenticate_and_read_block()`** | Tag Presence Flag | Event-driven (~1 Hz) | **28,500 µs** | **35,000 µs** | **Yes: Critical path containing cryptographic handshakes, multi-step SPI bus transfers, and strict RF timeout deadlines.** |

### 2.2 CDFG Node Definitions
```mermaid
graph TD
    N1((N1: Init Crypto Context)) --> N2((N2: Transmit MF_AUTH Command))
    N2 --> D1{D1: Handshake Ack?}
    D1 -- Yes --> N3((N3: Send 6-byte Key A))
    D1 -- No --> F1((F1: Log Auth Error))
    N3 --> D2{D2: Mutual Auth OK?}
    D2 -- Yes --> N4((N4: Issue READ Block Cmd))
    D2 -- No --> F1
    N4 --> N5((N5: Receive 16-byte Payload))
    N5 --> N6((N6: Verify CRC & Flush to LittleFS))
