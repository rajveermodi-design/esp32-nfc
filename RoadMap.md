# BACSE324 Project Execution Roadmap & Flowchart

This document outlines the end-to-end execution flow for our embedded systems project, spanning formal design models (Review 2), hardware integration, persistence logic, and final deliverables.

## Visual Execution Flowchart

```mermaid
graph TD
    classDef phase1 fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef phase2 fill:#1e293b,stroke:#22c55e,stroke-width:2px,color:#f8fafc;
    classDef phase3 fill:#1e293b,stroke:#8b5cf6,stroke-width:2px,color:#f8fafc;

    subgraph Phase 1: Review 2 Design Models (6-10 Pages)
        A1[1. System Recap & Scope Conditions] --> A2[2. CDFG & Critical Path Analysis]
        A2 --> A3[3. System Behavior FSM & Fault States]
        A3 --> A4[4. Task Schedule & Schedulability Proof]
        A4 --> A5[5. Model Traceability & Plan-to-Final]
    end

    subgraph Phase 2: Hardware & Software Build
        B1[6. Wire ESP32 + RC522 SPI + OLED] --> B2[7. Implement LittleFS Flash Persistence]
        B2 --> B3[8. Host Asynchronous Web Server & UI]
        B3 --> B4[9. Run PN532 Emulation Software Simulation]
    end

    subgraph Phase 3: Final Report & Presentation
        C1[10. Measure Latency, RAM, & Flash Optimisation] --> C2[11. Assemble 15-20 Page Final Report]
        C2 --> C3[12. Prepare 12-Slide Presentation & Demo Video]
    end

    A5 --> B1
    B4 --> C1

    class A1,A2,A3,A4,A5 phase1;
    class B1,B2,B3,B4 phase2;
    class C1,C2,C3 phase3;
