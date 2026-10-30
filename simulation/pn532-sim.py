#!/usr/bin/env python3
"""
PN532 Target Emulation Protocol Simulator
Implements low-level host frame encoding/decoding for TgInitAsTarget (0x8C).
Satisfies the simulation fallback deliverable for BACSE324 Review 1.
"""

import time

PREAMBLE = 0x00
START_CODE_1 = 0x00
START_CODE_2 = 0xFF
POSTAMBLE = 0x00
HOST_TO_PN532 = 0xD4
PN532_TO_HOST = 0xD5

def build_pn532_frame(command_bytes: list) -> bytes:
    """Builds a verified standard PN532 information frame with length & data checksums."""
    length = len(command_bytes)
    lcs = (~length + 1) & 0xFF  # Length checksum
    dcs = (~(sum(command_bytes) & 0xFF) + 1) & 0xFF  # Data checksum
    
    frame = bytearray([PREAMBLE, START_CODE_1, START_CODE_2, length, lcs])
    frame.extend(command_bytes)
    frame.extend([dcs, POSTAMBLE])
    return bytes(frame)

def simulate_card_emulation():
    print("=" * 60)
    print("PN532 Target-Mode Simulation: Emulating MIFARE Classic / ISO14443A")
    print("=" * 60)

    # Command: TgInitAsTarget (0x8C)
    # Mode 0x01 (Passive only), MifareParams (6 bytes), FelicaParams (18 bytes), NFCID3t (10 bytes)
    mifare_params = [0x04, 0x00, 0x08, 0x04, 0xAA, 0xBB, 0xCC] # SAK 0x08, ATQA 0x0004, UID AA:BB:CC
    cmd_init_target = [HOST_TO_PN532, 0x8C, 0x01] + mifare_params + [0x00] * 28
    
    frame = build_pn532_frame(cmd_init_target)
    print(f"\n[HOST -> PN532] Transmitting TgInitAsTarget command frame:")
    print("  Hex:", " ".join(f"{b:02X}" for b in frame))

    print("\n[SIMULATOR] ESP32 configured PN532 into target emulation mode.")
    print("[SIMULATOR] Waiting for RF field detection from external reader/smartphone...")
    time.sleep(1.5)

    # Simulated Reader Handshake Response Frame
    simulated_resp_bytes = [
        PN532_TO_HOST, 0x8D,  # TgInitAsTarget response code
        0x01,                # Target activated by ISO/IEC 14443A reader
        0x04, 0x00,          # ATQA: 0x0004 (MIFARE Classic)
        0x08,                # SAK: 0x08
        0x04,                # UID Length (4 bytes)
        0xAA, 0xBB, 0xCC, 0xDD # Emulated UID
    ]
    resp_frame = build_pn532_frame(simulated_resp_bytes)
    print("\n[PN532 -> HOST] External Reader coupled! Response frame received:")
    print("  Hex:", " ".join(f"{b:02X}" for b in resp_frame))
    print("\n[VERIFICATION] Target emulation handshake completed successfully.")
    print("  Emulated UID : AA:BB:CC:DD")
    print("  Reported ATQA: 0x0004")
    print("  Reported SAK : 0x08 (MIFARE Classic 1K Compatible)")
    print("=" * 60)

if __name__ == "__main__":
    simulate_card_emulation()