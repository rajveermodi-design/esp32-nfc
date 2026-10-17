# MIFARE Classic 1K Memory Map & Security Benchmark

## 1. Sector & Block Memory Allocation (Sector 1 Provisioned)

| Sector | Block | Type | Sample Hex Content | Description |
| :--- | :--- | :--- | :--- | :--- |
| **0** | Block 0 | Manufacturer | `A4 3B 11 0C 88 08 04 00 ...` | Read-only UID & Factory Data |
| **0** | Block 1-2 | Data | `00 00 00 00 00 00 ...` | Unused Sector 0 Data |
| **0** | Block 3 | Sector Trailer | `FF FF FF FF FF FF FF 07 80 69 ...` | Default Transport Keys |
| **1** | **Block 4** | **User Data** | `56 49 54 5F 32 30 32 36 5F 4C 41 42` | **Provisioned Payload ("VIT_2026_LAB")** |
| **1** | Block 5-6 | User Data | `00 00 00 00 00 00 ...` | Reserved Blocks |
| **1** | **Block 7** | **Sector Trailer**| `A0 A1 A2 A3 A4 A5 FF 07 80 69 B0 B1...`| **Custom Key A / Access Bits / Key B** |

---

## 2. Security Analysis: UID-Only vs. Authenticated Block Access

| Parameter | Unauthenticated UID Check | Authenticated Sector Access |
| :--- | :--- | :--- |
| **Authentication Required** | None (Broadcasted in cleartext) | 3-Pass Mutual Authentication (Crypto1) |
| **Cloning Vulnerability** | High (Trivially spoofed via UID-changeable tags) | Protected (Keys required to decrypt payload) |
| **Average Read Latency** | ~2,500 – 3,000 µs | ~25,000 – 38,000 µs |
| **Integrity Protection** | None | Encrypted communication channel |
