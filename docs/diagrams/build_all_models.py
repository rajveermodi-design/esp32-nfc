#!/usr/bin/env python3
"""
Comprehensive DFG and CDFG Generator for Draw.io & SVG
Project: ESP32 13.56 MHz RFID/NFC Security Framework (BACSE324 Review 2)
Author: Antigravity Assistant & Rajveer Modi
"""

import os
import html
import re
import xml.etree.ElementTree as ET

def escape_xml(text):
    return html.escape(str(text), quote=True)

class DiagramBuilder:
    def __init__(self, diagram_id, name, width=1600, height=1000):
        self.id = diagram_id
        self.name = name
        self.width = width
        self.height = height
        self.nodes = []
        self.edges = []
        self.groups = []
        self.cell_id_counter = 100

    def add_group(self, gid, label, x, y, w, h, fill="#0b1329", stroke="#334155", font="#94a3b8"):
        style = f"swimlane;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontColor={font};startSize=26;fontSize=12;fontStyle=1;rounded=1;strokeWidth=1.5;"
        self.groups.append({
            "id": gid,
            "label": label,
            "x": x, "y": y, "w": w, "h": h,
            "style": style,
            "fill": fill, "stroke": stroke, "font": font
        })

    def add_node(self, nid, label, x, y, w, h, style_type="process", custom_style=None, sublabel=""):
        full_label = f"<b>{label}</b>"
        if sublabel:
            full_label += f"<br/><span style='font-size:9px;opacity:0.85;'>{sublabel}</span>"

        if custom_style:
            style = custom_style
        elif style_type == "input":
            style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#064e3b;strokeColor=#10b981;strokeWidth=2;fontColor=#ecfdf5;fontStyle=0;fontSize=11;"
        elif style_type == "process":
            style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#1e293b;strokeColor=#38bdf8;strokeWidth=2;fontColor=#f8fafc;fontStyle=0;fontSize=11;"
        elif style_type == "operational":
            style = "ellipse;whiteSpace=wrap;html=1;fillColor=#1e293b;strokeColor=#38bdf8;strokeWidth=2;fontColor=#f8fafc;fontStyle=0;fontSize=11;"
        elif style_type == "critical":
            style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#1e293b;strokeColor=#f59e0b;strokeWidth=2.5;fontColor=#fef3c7;fontStyle=0;fontSize=11;"
        elif style_type == "critical_op":
            style = "ellipse;whiteSpace=wrap;html=1;fillColor=#1e293b;strokeColor=#f59e0b;strokeWidth=2.5;fontColor=#fef3c7;fontStyle=0;fontSize=11;"
        elif style_type == "decision":
            style = "rhombus;whiteSpace=wrap;html=1;fillColor=#312e81;strokeColor=#818cf8;strokeWidth=2;fontColor=#e0e7ff;fontStyle=1;fontSize=11;"
        elif style_type == "error":
            style = "ellipse;whiteSpace=wrap;html=1;fillColor=#7f1d1d;strokeColor=#f87171;strokeWidth=2;fontColor=#fef2f2;fontStyle=1;fontSize=10;"
        elif style_type == "terminal":
            style = "ellipse;whiteSpace=wrap;html=1;fillColor=#0f766e;strokeColor=#2dd4bf;strokeWidth=2;fontColor=#f0fdfa;fontStyle=1;fontSize=12;"
        elif style_type == "storage":
            style = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#78350f;strokeColor=#f59e0b;strokeWidth=2;fontColor=#fef3c7;fontStyle=1;fontSize=11;"
        elif style_type == "annotation":
            style = "rounded=1;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#f59e0b;strokeWidth=1.5;fontColor=#fde68a;fontStyle=0;fontSize=10;dashed=1;dashPattern=6 4;"
        elif style_type == "header":
            style = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;rounded=0;fontColor=#f8fafc;"
        elif style_type == "legend":
            style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#0f172a;strokeColor=#475569;strokeWidth=1;fontColor=#94a3b8;fontSize=10;"
        else:
            style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#1e293b;strokeColor=#64748b;strokeWidth=1.5;fontColor=#f8fafc;"

        self.nodes.append({
            "id": nid,
            "label": full_label,
            "raw_label": label,
            "sublabel": sublabel,
            "x": x, "y": y, "w": w, "h": h,
            "type": style_type,
            "style": style
        })

    def add_edge(self, source, target, label="", edge_type="data", exit_point=None, entry_point=None):
        if edge_type == "data":
            style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#10b981;strokeWidth=2.2;fontColor=#6ee7b7;fontSize=10;labelBackgroundColor=#0f172a;"
        elif edge_type == "control":
            style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;dashed=1;dashPattern=6 4;strokeColor=#818cf8;strokeWidth=2;fontColor=#c7d2fe;fontSize=10;labelBackgroundColor=#0f172a;"
        elif edge_type == "critical":
            style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#facc15;strokeWidth=3.5;fontColor=#fef08a;fontSize=10;labelBackgroundColor=#0f172a;"
        elif edge_type == "error":
            style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;dashed=1;dashPattern=4 3;strokeColor=#ef4444;strokeWidth=2;fontColor=#fca5a5;fontSize=10;labelBackgroundColor=#0f172a;"
        elif edge_type == "loopback":
            style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;dashed=1;dashPattern=3 3;strokeColor=#38bdf8;strokeWidth=2;fontColor=#7dd3fc;fontSize=10;labelBackgroundColor=#0f172a;"
        else:
            style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#64748b;strokeWidth=1.5;fontColor=#94a3b8;fontSize=10;"

        if exit_point:
            style += f"exitX={exit_point[0]};exitY={exit_point[1]};exitDx=0;exitDy=0;"
        if entry_point:
            style += f"entryX={entry_point[0]};entryY={entry_point[1]};entryDx=0;entryDy=0;"

        self.cell_id_counter += 1
        self.edges.append({
            "id": f"e{self.cell_id_counter}",
            "source": source,
            "target": target,
            "label": label,
            "type": edge_type,
            "style": style
        })

    def to_drawio_xml_diagram(self):
        lines = []
        lines.append(f'  <diagram id="{self.id}" name="{escape_xml(self.name)}">')
        lines.append(f'    <mxGraphModel dx="1422" dy="798" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.width}" pageHeight="{self.height}" background="#0f172a" math="0" shadow="0">')
        lines.append('      <root>')
        lines.append('        <mxCell id="0" />')
        lines.append('        <mxCell id="1" parent="0" />')

        # Groups / Swimlanes
        for g in self.groups:
            lines.append(f'        <mxCell id="{g["id"]}" value="{escape_xml(g["label"])}" style="{g["style"]}" vertex="1" parent="1">')
            lines.append(f'          <mxGeometry x="{g["x"]}" y="{g["y"]}" width="{g["w"]}" height="{g["h"]}" as="geometry" />')
            lines.append('        </mxCell>')

        # Nodes
        for n in self.nodes:
            lines.append(f'        <mxCell id="{n["id"]}" value="{escape_xml(n["label"])}" style="{n["style"]}" vertex="1" parent="1">')
            lines.append(f'          <mxGeometry x="{n["x"]}" y="{n["y"]}" width="{n["w"]}" height="{n["h"]}" as="geometry" />')
            lines.append('        </mxCell>')

        # Edges
        for e in self.edges:
            lines.append(f'        <mxCell id="{e["id"]}" value="{escape_xml(e["label"])}" style="{e["style"]}" edge="1" parent="1" source="{e["source"]}" target="{e["target"]}">')
            lines.append('          <mxGeometry relative="1" as="geometry" />')
            lines.append('        </mxCell>')

        lines.append('      </root>')
        lines.append('    </mxGraphModel>')
        lines.append('  </diagram>')
        return "\n".join(lines)

    def to_svg(self):
        node_lookup = {n["id"]: n for n in self.nodes}
        svg = []
        svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" width="{self.width}" height="{self.height}" style="background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif;">')
        svg.append('  <defs>')
        svg.append('    <marker id="arrow-data" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9 z" fill="#10b981" /></marker>')
        svg.append('    <marker id="arrow-control" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9 z" fill="#818cf8" /></marker>')
        svg.append('    <marker id="arrow-critical" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9 z" fill="#facc15" /></marker>')
        svg.append('    <marker id="arrow-error" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9 z" fill="#ef4444" /></marker>')
        svg.append('    <marker id="arrow-loop" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9 z" fill="#38bdf8" /></marker>')
        svg.append('    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000" flood-opacity="0.35"/></filter>')
        svg.append('  </defs>')

        # Groups
        for g in self.groups:
            svg.append(f'  <g id="{g["id"]}">')
            svg.append(f'    <rect x="{g["x"]}" y="{g["y"]}" width="{g["w"]}" height="{g["h"]}" rx="8" fill="{g["fill"]}" stroke="{g["stroke"]}" stroke-width="1.5" />')
            svg.append(f'    <rect x="{g["x"]}" y="{g["y"]}" width="{g["w"]}" height="28" rx="8" fill="{g["stroke"]}" fill-opacity="0.25" />')
            svg.append(f'    <text x="{g["x"] + 14}" y="{g["y"] + 19}" fill="{g["font"]}" font-size="12" font-weight="bold">{escape_xml(g["label"])}</text>')
            svg.append('  </g>')

        # Edges
        for e in self.edges:
            src = node_lookup.get(e["source"])
            dst = node_lookup.get(e["target"])
            if not src or not dst:
                continue

            sx = src["x"] + src["w"]
            sy = src["y"] + src["h"] / 2
            dx = dst["x"]
            dy = dst["y"] + dst["h"] / 2

            if abs(src["x"] - dst["x"]) < 60 and dst["y"] > src["y"]:
                sx = src["x"] + src["w"] / 2
                sy = src["y"] + src["h"]
                dx = dst["x"] + dst["w"] / 2
                dy = dst["y"]
                path_d = f"M {sx} {sy} L {dx} {dy}"
                mid_x = sx
                mid_y = (sy + dy) / 2
            elif dx < sx:
                sx = src["x"]
                dx = dst["x"] + dst["w"]
                mid_x = min(src["x"], dst["x"]) - 40
                path_d = f"M {src['x']} {sy} L {mid_x} {sy} L {mid_x} {dy} L {dst['x']} {dy}"
                mid_y = (sy + dy) / 2
            else:
                mid_x = (sx + dx) / 2
                path_d = f"M {sx} {sy} C {mid_x} {sy}, {mid_x} {dy}, {dx} {dy}"
                mid_y = (sy + dy) / 2

            if e["type"] == "data":
                stroke = "#10b981"
                dash = ""
                marker = "url(#arrow-data)"
                text_col = "#6ee7b7"
                stroke_w = "2.2"
            elif e["type"] == "control":
                stroke = "#818cf8"
                dash = 'stroke-dasharray="6,4"'
                marker = "url(#arrow-control)"
                text_col = "#c7d2fe"
                stroke_w = "2"
            elif e["type"] == "critical":
                stroke = "#facc15"
                dash = 'stroke-dasharray="6,4"'
                marker = "url(#arrow-critical)"
                text_col = "#fef08a"
                stroke_w = "3.5"
            elif e["type"] == "error":
                stroke = "#ef4444"
                dash = 'stroke-dasharray="4,3"'
                marker = "url(#arrow-error)"
                text_col = "#fca5a5"
                stroke_w = "2"
            elif e["type"] == "loopback":
                stroke = "#38bdf8"
                dash = 'stroke-dasharray="3,3"'
                marker = "url(#arrow-loop)"
                text_col = "#7dd3fc"
                stroke_w = "2"
            else:
                stroke = "#64748b"
                dash = ""
                marker = ""
                text_col = "#94a3b8"
                stroke_w = "1.5"

            svg.append(f'  <path d="{path_d}" fill="none" stroke="{stroke}" stroke-width="{stroke_w}" {dash} marker-end="{marker}" />')
            if e["label"]:
                svg.append(f'  <g transform="translate({mid_x}, {mid_y})">')
                svg.append(f'    <rect x="-4" y="-10" width="{len(e["label"])*6 + 10}" height="16" rx="4" fill="#0f172a" fill-opacity="0.9" stroke="{stroke}" stroke-width="0.7"/>')
                svg.append(f'    <text x="2" y="2" fill="{text_col}" font-size="9" font-family="monospace">{escape_xml(e["label"])}</text>')
                svg.append('  </g>')

        # Nodes
        for n in self.nodes:
            t = n["type"]
            x, y, w, h = n["x"], n["y"], n["w"], n["h"]

            if t == "header":
                svg.append(f'  <g transform="translate({x}, {y})">')
                svg.append(f'    <text x="0" y="20" fill="#f8fafc" font-size="16" font-weight="bold">{escape_xml(n["raw_label"])}</text>')
                if n["sublabel"]:
                    svg.append(f'    <text x="0" y="38" fill="#94a3b8" font-size="11">{escape_xml(n["sublabel"])}</text>')
                svg.append('  </g>')
                continue

            if t == "input":
                fill, stroke, text_col = "#064e3b", "#10b981", "#ecfdf5"
            elif t in ("process", "operational"):
                fill, stroke, text_col = "#1e293b", "#38bdf8", "#f8fafc"
            elif t in ("critical", "critical_op"):
                fill, stroke, text_col = "#1e293b", "#f59e0b", "#fef3c7"
            elif t == "annotation":
                fill, stroke, text_col = "none", "#f59e0b", "#fde68a"
            elif t == "decision":
                fill, stroke, text_col = "#312e81", "#818cf8", "#e0e7ff"
            elif t == "error":
                fill, stroke, text_col = "#7f1d1d", "#f87171", "#fef2f2"
            elif t == "terminal":
                fill, stroke, text_col = "#0f766e", "#2dd4bf", "#f0fdfa"
            elif t == "storage":
                fill, stroke, text_col = "#78350f", "#f59e0b", "#fef3c7"
            elif t == "legend":
                fill, stroke, text_col = "#0f172a", "#475569", "#94a3b8"
            else:
                fill, stroke, text_col = "#1e293b", "#64748b", "#f8fafc"

            svg.append(f'  <g id="{n["id"]}" filter="url(#shadow)">')
            if t == "decision":
                pts = f"{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}"
                svg.append(f'    <polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="2" />')
            elif t in ("terminal", "error", "operational", "critical_op"):
                sw = "2.5" if t == "critical_op" else "2"
                svg.append(f'    <ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" />')
            elif t == "annotation":
                svg.append(f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="none" stroke="{stroke}" stroke-width="1.5" stroke-dasharray="6,4" />')
            elif t == "storage":
                svg.append(f'    <rect x="{x}" y="{y+6}" width="{w}" height="{h-6}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="2" />')
                svg.append(f'    <ellipse cx="{x+w/2}" cy="{y+6}" rx="{w/2}" ry="6" fill="{fill}" stroke="{stroke}" stroke-width="2" />')
            else:
                svg.append(f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2" />')

            svg.append(f'    <text x="{x+w/2}" y="{y+h/2 - (4 if n["sublabel"] else -4)}" text-anchor="middle" fill="{text_col}" font-size="11" font-weight="bold">{escape_xml(n["raw_label"])}</text>')
            if n["sublabel"]:
                svg.append(f'    <text x="{x+w/2}" y="{y+h/2 + 12}" text-anchor="middle" fill="{text_col}" font-size="9" fill-opacity="0.85">{escape_xml(n["sublabel"])}</text>')
            svg.append('  </g>')

        svg.append('</svg>')
        return "\n".join(svg)


def create_dfg_crypto_auth():
    d = DiagramBuilder("dfg-crypto-auth", "1. DFG - Crypto Auth & Block Read (Critical Path)", 1560, 920)
    
    # Header
    d.add_node("hdr", "DATA FLOW GRAPH (DFG) — Critical-Path Cryptographic Authentication & Block Read",
               40, 30, 800, 50, "header",
               sublabel="Function: authenticate_and_read_block() | Critical Path Latency: 28,500 µs | Deadline: 35,000 µs")

    # Legend
    d.add_node("leg_in", "Data Source / Input [Reg]", 980, 30, 160, 35, "input")
    d.add_node("leg_op", "Computation Node [Op]", 1160, 30, 160, 35, "process")
    d.add_node("leg_out", "Data Sink [Memory/Bus]", 1340, 30, 160, 35, "storage")

    # Lanes / Stages
    d.add_group("stg_in", "STAGE 0: INPUT OPERANDS & HARDWARE REGISTERS", 40, 100, 240, 780, fill="#0b172a", stroke="#1e3a5f")
    d.add_group("stg_1", "STAGE 1: PCD ENCODING & DEMODULATION", 320, 100, 260, 780, fill="#0b172a", stroke="#1e3a5f")
    d.add_group("stg_2", "STAGE 2: CRYPTO-1 CORE & NONCE ENGINE", 620, 100, 280, 780, fill="#0b172a", stroke="#1e3a5f")
    d.add_group("stg_3", "STAGE 3: MUTUAL AUTH & COMMAND ENCRYPTION", 940, 100, 280, 780, fill="#0b172a", stroke="#1e3a5f")
    d.add_group("stg_4", "STAGE 4: PAYLOAD STREAM DECRYPT & FLUSH", 1260, 100, 260, 780, fill="#0b172a", stroke="#1e3a5f")

    # Column 0: Inputs
    d.add_node("in_key", "Key A Register [48-bit]", 60, 150, 200, 60, "input", sublabel="0xFF 0xFF 0xFF 0xFF 0xFF 0xFF")
    d.add_node("in_block", "Block Address [8-bit]", 60, 280, 200, 60, "input", sublabel="0x04 (Sector 1, Block 0)")
    d.add_node("in_uid", "Card UID Register [32-bit]", 60, 410, 200, 60, "input", sublabel="rfid.uid.uidByte[0..3]")
    d.add_node("in_cmd", "Auth Opcode [8-bit]", 60, 540, 200, 60, "input", sublabel="0x60 (PICC_CMD_MF_AUTH_KEY_A)")
    d.add_node("in_rf", "RF Carrier Field [13.56 MHz]", 60, 670, 200, 60, "input", sublabel="ISO/IEC 14443A Load Modulation")

    # Column 1: Stage 1
    d.add_node("op_pack_auth", "OP1: PCD Auth Frame Pack", 340, 350, 220, 65, "process", sublabel="CMD || Block || CRC-A (16 µs)")
    d.add_node("op_rf_demod", "OP2: RF Demod & Sync", 340, 670, 220, 65, "critical", sublabel="Capture 32-bit Nonce Nt (5,200 µs)")

    # Column 2: Stage 2
    d.add_node("op_prng_reader", "OP3: Hardware PRNG", 650, 170, 220, 60, "process", sublabel="Generate 32-bit Nr (4 µs)")
    d.add_node("op_lfsr_init", "OP4: Crypto-1 LFSR Init", 650, 370, 220, 65, "critical", sublabel="State0 = f(KeyA, UID, Nt) (28 µs)")
    d.add_node("op_keystream", "OP5: Non-Linear Keystream", 650, 570, 220, 65, "critical", sublabel="fk(State) -> ki bits (62 µs)")

    # Column 3: Stage 3
    d.add_node("op_enc_reader", "OP6: Reader Challenge Enc", 970, 220, 220, 65, "critical", sublabel="ar = Nr ^ k1..32 + parity (14 µs)")
    d.add_node("op_tag_auth", "OP7: Tag Response Verifier", 970, 420, 220, 65, "critical", sublabel="at = Ciph ^ k33..64 == succ(Nt) (6,800 µs)")
    d.add_node("op_enc_read_cmd", "OP8: Encrypt Read Block Cmd", 970, 620, 220, 65, "process", sublabel="0x30 || 0x04 || CRC-A ^ k65..96 (18 µs)")

    # Column 4: Stage 4
    d.add_node("op_stream_dec", "OP9: 16-Byte Payload Decrypt", 1280, 320, 220, 65, "critical", sublabel="Plain[0..15] = Ciph ^ k97..224 (42 µs)")
    d.add_node("op_crc_calc", "OP10: CRC-16 Engine", 1280, 470, 220, 60, "process", sublabel="Verify ISO 14443-3 CRC-A (22 µs)")
    d.add_node("out_plain_buf", "OUT1: Block Data Buffer", 1280, 600, 220, 60, "storage", sublabel="16-Byte Plaintext Memory Block")
    d.add_node("out_status", "OUT2: Auth Status Register", 1280, 720, 220, 60, "storage", sublabel="STATUS_OK | AUTH_SUCCESS")

    # Connect Edges (Pure Data Flow)
    d.add_edge("in_cmd", "op_pack_auth", "8-bit Opcode")
    d.add_edge("in_block", "op_pack_auth", "8-bit Addr")
    d.add_edge("in_rf", "op_rf_demod", "13.56 MHz Subcarrier")
    
    d.add_edge("op_rf_demod", "op_lfsr_init", "32-bit Nt Nonce")
    d.add_edge("in_key", "op_lfsr_init", "48-bit Key A")
    d.add_edge("in_uid", "op_lfsr_init", "32-bit UID")
    
    d.add_edge("op_lfsr_init", "op_keystream", "48-bit LFSR State")
    d.add_edge("op_prng_reader", "op_enc_reader", "32-bit Nr Nonce")
    d.add_edge("op_keystream", "op_enc_reader", "k1..32 Keystream")
    d.add_edge("op_keystream", "op_tag_auth", "k33..64 Keystream")
    d.add_edge("op_enc_reader", "op_tag_auth", "64-bit Challenge ar")

    d.add_edge("in_block", "op_enc_read_cmd", "8-bit Block Addr")
    d.add_edge("op_keystream", "op_enc_read_cmd", "k65..96 Keystream")
    d.add_edge("op_tag_auth", "op_stream_dec", "Ciphertext Block")
    d.add_edge("op_keystream", "op_stream_dec", "k97..224 Keystream")
    
    d.add_edge("op_stream_dec", "op_crc_calc", "16-Byte Plaintext")
    d.add_edge("op_stream_dec", "out_plain_buf", "16-Byte Buffer")
    d.add_edge("op_crc_calc", "out_status", "Checksum Valid")
    
    return d


def create_dfg_telemetry():
    d = DiagramBuilder("dfg-telemetry", "2. DFG - System Telemetry & Benchmark Pipeline", 1560, 920)
    
    # Header
    d.add_node("hdr", "DATA FLOW GRAPH (DFG) — System Telemetry, Latency Benchmark & Flash Logging Pipeline",
               40, 30, 850, 50, "header",
               sublabel="Data Pipeline: Sensor Timers & Registers -> Hex/JSON Formatting -> SSD1306 Framebuffer & LittleFS Flash")

    # Legend
    d.add_node("leg_in", "Telemetry Source [HW]", 980, 30, 160, 35, "input")
    d.add_node("leg_op", "Formatting / Serializer", 1160, 30, 160, 35, "process")
    d.add_node("leg_out", "Flash / Display Sink", 1340, 30, 160, 35, "storage")

    # Lanes
    d.add_group("stg_src", "STAGE 0: SENSOR & HARDWARE TELEMETRY SOURCES", 40, 100, 250, 780, fill="#0b172a", stroke="#1e3a5f")
    d.add_group("stg_parse", "STAGE 1: ARITHMETIC & HEX SERIALIZATION", 330, 100, 270, 780, fill="#0b172a", stroke="#1e3a5f")
    d.add_group("stg_struct", "STAGE 2: DOM PACKING & FRAMEBUFFER BLIT", 640, 100, 280, 780, fill="#0b172a", stroke="#1e3a5f")
    d.add_group("stg_stream", "STAGE 3: BUS PACKAGING & FLASH BUFFERING", 960, 100, 270, 780, fill="#0b172a", stroke="#1e3a5f")
    d.add_group("stg_sink", "STAGE 4: HARDWARE SINKS & WEB OUTPUT", 1270, 100, 250, 780, fill="#0b172a", stroke="#1e3a5f")

    # Column 0: Sources
    d.add_node("src_t0", "Timer t0 Register [32-bit]", 60, 140, 210, 55, "input", sublabel="micros() at RF start")
    d.add_node("src_t1", "Timer t1 Register [32-bit]", 60, 230, 210, 55, "input", sublabel="micros() at RF finish")
    d.add_node("src_uid", "Raw UID Bytes [4..7 Bytes]", 60, 330, 210, 55, "input", sublabel="rfid.uid.uidByte[]")
    d.add_node("src_sak", "SAK Byte [8-bit]", 60, 440, 210, 55, "input", sublabel="0x08 (MIFARE) / 0x00 (Ultralight)")
    d.add_node("src_atqa", "ATQA Word [16-bit]", 60, 540, 210, 55, "input", sublabel="0x0004 (ISO 14443-3)")
    d.add_node("src_auth", "Auth Status Flag", 60, 640, 210, 55, "input", sublabel="AUTH_SUCCESS / AUTH_FAILED")
    d.add_node("src_uptime", "System Uptime [32-bit]", 60, 740, 210, 55, "input", sublabel="millis() since boot")

    # Column 1: Stage 1
    d.add_node("op_sub_time", "OP1: Delta-t Latency Subtractor", 350, 180, 230, 65, "critical", sublabel="Delta_t = t1 - t0 (1.2 µs)")
    d.add_node("op_hex_fmt", "OP2: UID Hex-ASCII Serializer", 350, 330, 230, 65, "process", sublabel="uidByte[] -> \"AA:BB:CC:DD\" (14.5 µs)")
    d.add_node("op_classify", "OP3: Tag Family Classifier", 350, 490, 230, 65, "process", sublabel="size==7 ? NTAG : MIFARE (0.8 µs)")

    # Column 2: Stage 2
    d.add_node("op_oled_blit", "OP4: SSD1306 Glyph Rasterizer", 660, 230, 240, 65, "process", sublabel="Convert text to 128x64 bitmask (2.1 ms)")
    d.add_node("op_json_doc", "OP5: ArduinoJson DOM Builder", 660, 520, 240, 75, "process", sublabel="StaticJsonDocument<256> (18.2 µs)\ntimestamp, uid, read_time_us, status")

    # Column 3: Stage 3
    d.add_node("op_i2c_bus", "OP6: I2C Fast-Mode Transmit", 980, 230, 230, 65, "process", sublabel="400 kHz Wire Buffer Tx (2,050 µs)")
    d.add_node("op_jsonl_ser", "OP7: JSONL Line Serializer", 980, 480, 230, 65, "process", sublabel="serializeJson(doc, file) (32.4 µs)")
    d.add_node("op_flash_flush", "OP8: LittleFS Page Cache Flush", 980, 640, 230, 65, "critical", sublabel="SPI Physical Flash Commit (3,800 µs)")

    # Column 4: Sinks
    d.add_node("sink_oled", "SINK 1: OLED Display Screen", 1290, 230, 210, 65, "storage", sublabel="128x64 Monochrome Pixel Grid")
    d.add_node("sink_flash", "SINK 2: LittleFS Physical Flash", 1290, 560, 210, 65, "storage", sublabel="/scans.jsonl Partition (Non-Volatile)")
    d.add_node("sink_web", "SINK 3: Async Web Client Buffer", 1290, 720, 210, 65, "storage", sublabel="/api/logs REST API Stream (WiFi AP)")

    # Edges
    d.add_edge("src_t0", "op_sub_time", "t0 µs")
    d.add_edge("src_t1", "op_sub_time", "t1 µs")
    d.add_edge("src_uid", "op_hex_fmt", "Raw Bytes")
    d.add_edge("src_uid", "op_classify", "UID Size")
    d.add_edge("src_sak", "op_classify", "SAK Byte")

    d.add_edge("op_sub_time", "op_oled_blit", "Delta_t (µs)")
    d.add_edge("op_hex_fmt", "op_oled_blit", "UID String")
    d.add_edge("src_auth", "op_oled_blit", "Auth Status")

    d.add_edge("src_uptime", "op_json_doc", "timestamp")
    d.add_edge("op_classify", "op_json_doc", "family string")
    d.add_edge("op_hex_fmt", "op_json_doc", "uid string")
    d.add_edge("src_atqa", "op_json_doc", "atqa string")
    d.add_edge("src_sak", "op_json_doc", "sak string")
    d.add_edge("op_sub_time", "op_json_doc", "read_time_us")
    d.add_edge("src_auth", "op_json_doc", "status string")

    d.add_edge("op_oled_blit", "op_i2c_bus", "1024-Byte Framebuffer")
    d.add_edge("op_i2c_bus", "sink_oled", "I2C SDA/SCL Wire")
    
    d.add_edge("op_json_doc", "op_jsonl_ser", "JSON Object")
    d.add_edge("op_jsonl_ser", "op_flash_flush", "ASCII Line Buffer")
    d.add_edge("op_flash_flush", "sink_flash", "Flash Page Commit")
    d.add_edge("sink_flash", "sink_web", "Async HTTP Socket")

    return d


def create_cdfg_critical_function():
    d = DiagramBuilder("cdfg-function", "3. CDFG - Critical Function (authenticate_and_read_block)", 1560, 1180)
    
    # Header
    d.add_node("hdr", "CONTROL DATA FLOW GRAPH (CDFG) — Critical-Path Function",
               40, 25, 800, 50, "header",
               sublabel="Function: authenticate_and_read_block(block=4, keyA) | T_exec: 28,500 µs | Deadline: 35,000 µs | Slack: 6,500 µs")

    # Legend
    d.add_node("leg_ctrl", "Control Flow Edge", 980, 25, 130, 25, "decision")
    d.add_node("leg_data", "Data Flow Edge", 1120, 25, 130, 25, "input")
    d.add_node("leg_err", "Error / Rejection Trap", 1260, 25, 140, 25, "error")

    # Basic Block Container Groups
    d.add_group("bb0", "BB0: Operand Preparation {D1}", 520, 155, 360, 95)
    d.add_group("bb1", "BB1: Bus Verification & Command Transmission {C1, D2}", 520, 255, 360, 195)
    d.add_group("bb2", "BB2: RF Handshake & Reader Challenge {C2, D3, D4}", 520, 455, 360, 290)
    d.add_group("bb3", "BB3: Mutual Authentication & Block Read {C3, D5}", 520, 755, 360, 195)
    d.add_group("bb4", "BB4: Integrity Check & Buffer Commit {C4, D6}", 520, 955, 360, 180)
    d.add_group("bb_err", "BB_ERR: Fault & Timeout Traps {ERR1–ERR4}", 230, 250, 240, 795, fill="#1c0f14", stroke="#7f1d1d", font="#fca5a5")
    d.add_group("bb_exit", "BB_EXIT: PCD Teardown & Return {CLEANUP, RETURN}", 950, 580, 300, 290)

    # Vertical Layout for Control Decisions & Execution
    # Start (Terminal)
    d.add_node("c_entry", "START: authenticate_and_read_block()", 560, 90, 280, 50, "terminal", sublabel="Trigger: Valid PICC Serial Detected")

    # D1: Load Parameters (Operational - Ellipse)
    d.add_node("d_load", "D1: Load Key A & UID Operands", 560, 180, 280, 55, "operational", sublabel="KeyA = 0xFF*6 (6B), UID = rfid.uid (4B) | 2 µs")
    
    # C1: Check SPI Ready (Decision - Rhombus)
    d.add_node("c_spi_check", "C1: SPI Bus Ready?", 610, 270, 180, 70, "decision", sublabel="Check PCD_Ready (4 µs)")
    d.add_node("err_spi", "ERR: SPI Bus Timeout", 260, 280, 180, 50, "error", sublabel="Set STATUS_SPI_ERR")

    # D2: Tx Auth Command (Operational - Ellipse)
    d.add_node("d_tx_auth", "D2: Transmit MF_AUTH Command", 560, 380, 280, 55, "operational", sublabel="0x60 || Block 0x04 || CRC-A | 16 µs")

    # C2: Ack Received (Decision - Rhombus)
    d.add_node("c_ack", "C2: Tag Handshake Ack?", 610, 470, 180, 70, "decision", sublabel="RF Response in < 1.5 ms (1,480 µs)")
    d.add_node("err_timeout", "ERR: RF Timeout", 260, 480, 180, 50, "error", sublabel="Set STATUS_TIMEOUT")

    # D3: Receive Nonce & Crypto1 (Critical Operational - Ellipse)
    d.add_node("d_crypto", "D3: LFSR Init & Reader Encrypt", 560, 580, 280, 60, "critical_op", sublabel="Rx Nt -> State0 = f(Key,UID,Nt) -> Enc ar | 42 µs")

    # D4: Transmit Reader Challenge Response (Critical Operational - Ellipse)
    d.add_node("d_tx_resp", "D4: Transmit 64-bit Challenge Response", 560, 680, 280, 55, "critical_op", sublabel="Send ar = Nr ^ k1..32 over RF | 5,200 µs")

    # C3: Mutual Authentication Check (Decision - Rhombus)
    d.add_node("c_mutual", "C3: Mutual Auth OK?", 610, 770, 180, 70, "decision", sublabel="at == succ(Nt) verified (6,800 µs)")
    d.add_node("err_auth", "ERR: Auth Rejection", 260, 780, 180, 50, "error", sublabel="Spoof / Key Mismatch Detected")

    # D5: Issue Read Command (Operational - Ellipse)
    d.add_node("d_tx_read", "D5: Transmit Read Block 4 Cmd", 560, 880, 280, 55, "operational", sublabel="0x30 || 0x04 || CRC-A ^ k65..96 | 18 µs")

    # C4: Block CRC Check (Decision - Rhombus, CRC-A)
    d.add_node("c_crc", "C4: Payload CRC-A Valid?", 610, 970, 180, 70, "decision", sublabel="Verify ISO 14443-3 CRC-A (22 µs)")
    d.add_node("err_crc", "ERR: CRC Mismatch", 260, 980, 180, 50, "error", sublabel="Payload Corrupted")

    # D6: Commit Buffer (Operational - Ellipse)
    d.add_node("d_commit", "D6: Commit 16-Byte Block to Buffer", 560, 1070, 280, 50, "operational", sublabel="status = STATUS_OK | AUTH_SUCCESS | 5 µs")

    # Cleanup & Exit Lane (Operational - Ellipse)
    d.add_node("d_cleanup", "CLEANUP: PCD & PICC Teardown", 980, 620, 240, 60, "operational", sublabel="rfid.PCD_StopCrypto1(); rfid.PICC_HaltA(); | 180 µs")
    d.add_node("c_exit", "RETURN: authenticate_and_read_block()", 980, 800, 240, 50, "terminal", sublabel="Exit with Status & Measured Delta_t")

    # Side Data Nodes to illustrate Data Flow in CDFG
    d.add_node("data_key_storage", "DATA: Key A Store [48-bit]", 980, 180, 220, 50, "input", sublabel="0xFF 0xFF 0xFF 0xFF 0xFF 0xFF")
    d.add_node("data_nt_buf", "DATA: Tag Nonce Nt [32-bit]", 980, 480, 220, 50, "input", sublabel="Captured over RF Demod")
    d.add_node("data_block_out", "DATA: Decrypted Block [16B]", 980, 1070, 220, 50, "storage", sublabel="Plaintext Memory Array")

    # Annotations: RF Bus Idle Overhead & Critical Path Key
    d.add_node("rf_overhead", "RF Bus Idle Overhead: 14,719 µs", 40, 600, 200, 120, "annotation",
               sublabel="Includes RF frame timing gaps, antenna settling,\nSPI clock overhead & ISO 14443 guard times.\nIncluded in WCET (28,500 µs). Visible nodes = 13,781 µs.")
    d.add_node("crit_path_note", "━━ Critical Path (Yellow Highlight)", 40, 740, 200, 100, "annotation",
               sublabel="START→D1→C1(Y)→D2→C2(Y)→D3→D4→C3(Y)→D5→C4(Y)→D6→CLEANUP→RETURN\nTotal: 28,500 µs | Deadline: 35,000 µs | Slack: 6,500 µs (18.6%)")

    # Critical Path Edges (Gold Highlighted)
    d.add_edge("c_entry", "d_load", "Begin Exec", "critical")
    d.add_edge("d_load", "c_spi_check", "Check Bus", "critical")
    d.add_edge("c_spi_check", "d_tx_auth", "Yes (Bus Free)", "critical")
    d.add_edge("d_tx_auth", "c_ack", "Wait RF Ack", "critical")
    d.add_edge("c_ack", "d_crypto", "Yes (Acked)", "critical")
    d.add_edge("d_crypto", "d_tx_resp", "Enc Ready", "critical")
    d.add_edge("d_tx_resp", "c_mutual", "Wait Tag Token", "critical")
    d.add_edge("c_mutual", "d_tx_read", "Yes (Auth OK)", "critical")
    d.add_edge("d_tx_read", "c_crc", "Rx 16B Payload", "critical")
    d.add_edge("c_crc", "d_commit", "Yes (CRC Valid)", "critical")
    d.add_edge("d_commit", "d_cleanup", "Success Exit", "critical")
    d.add_edge("d_cleanup", "c_exit", "Return Result", "critical")

    # Error / Branch Control Edges (Red Dashed)
    d.add_edge("c_spi_check", "err_spi", "No (Bus Busy)", "error")
    d.add_edge("err_spi", "d_cleanup", "Abort", "error")
    d.add_edge("c_ack", "err_timeout", "Timeout (>1.5ms)", "error")
    d.add_edge("err_timeout", "d_cleanup", "Abort", "error")
    d.add_edge("c_mutual", "err_auth", "No (Key Rejection)", "error")
    d.add_edge("err_auth", "d_cleanup", "Abort", "error")
    d.add_edge("c_crc", "err_crc", "No (Checksum Err)", "error")
    d.add_edge("err_crc", "d_cleanup", "Abort", "error")

    # Data Edges (Solid Green)
    d.add_edge("data_key_storage", "d_load", "Key A [48-bit]", "data")
    d.add_edge("d_crypto", "data_nt_buf", "Demod Nonce", "data")
    d.add_edge("data_nt_buf", "d_tx_resp", "Challenge Vector", "data")
    d.add_edge("d_commit", "data_block_out", "16-Byte Payload", "data")

    return d


def create_cdfg_system_main_loop():
    d = DiagramBuilder("cdfg-system", "4. CDFG - System Level (Dual-Mode NFC Engine)", 1600, 1280)
    
    # Header
    d.add_node("hdr", "CONTROL DATA FLOW GRAPH (CDFG) — System-Level Dual-Mode NFC Analysis Engine",
               40, 25, 850, 50, "header",
               sublabel="ESP32 Dual-Mode Engine: Level 1 UID Unauthenticated vs Level 2 Cryptographic Sector | LittleFS Flash Persistence & OLED UI")

    # Legend
    d.add_node("leg_ctrl", "Control Flow Edge", 980, 25, 130, 25, "decision")
    d.add_node("leg_data", "Data Flow Edge", 1120, 25, 130, 25, "input")
    d.add_node("leg_loop", "Periodic Loopback", 1260, 25, 140, 25, "process")

    # System Init Section
    d.add_node("sys_power", "POWER ON / RESET", 560, 90, 260, 45, "terminal", sublabel="ESP32 Boot & Dual-Core Start")
    d.add_node("sys_init", "INIT: Peripherals & Stacks", 560, 165, 260, 60, "process", sublabel="SPI.begin(18,19,23,5) | Wire.begin(21,22)\nLittleFS.begin() | WiFi.softAP()")

    # Polling Section
    d.add_node("c_poll_card", "C1: PICC_IsNewCardPresent()?", 590, 265, 200, 70, "decision", sublabel="13.56 MHz RF Field Polling")
    d.add_node("c_read_serial", "C2: PICC_ReadCardSerial()?", 590, 375, 200, 70, "decision", sublabel="Anti-Collision Cascade Loop")

    # Timer Start
    d.add_node("d_t0_start", "D1: Start Latency Timer", 560, 485, 260, 50, "process", sublabel="startTime = micros() (ESP32 HW Timer)")

    # UID Extraction
    d.add_node("d_format_uid", "D2: Extract & Format UID String", 560, 570, 260, 55, "process", sublabel="uidByte[0..size] -> uidStr (HEX)")

    # Dual Mode Branching
    d.add_node("c_mode_branch", "C3: Verification Architecture?", 590, 665, 200, 75, "decision", sublabel="Level 1 vs Level 2 Evaluation")

    # Level 1 Branch (Unauthenticated UID)
    d.add_node("d_level1_audit", "LEVEL 1: UID-Only Audit", 220, 770, 240, 60, "critical", sublabel="T_exec ~2.8 ms | Vulnerable to Clones\nDirect Database / Whitelist Check")
    d.add_node("d_level1_warn", "VULNERABILITY DETECTED", 220, 865, 240, 50, "error", sublabel="Zero cryptographic challenge (Trivial Replay)")

    # Level 2 Branch (Authenticated Cryptographic Sector)
    d.add_node("d_level2_exec", "LEVEL 2: Sector 1 Block 4 Auth", 720, 770, 260, 60, "critical", sublabel="authenticate_and_read_block()\nT_exec ~30.2 ms | 3-Pass Mutual Auth")
    
    d.add_node("c_auth_ok", "C4: PCD_Authenticate == OK?", 750, 865, 200, 70, "decision", sublabel="Crypto-1 Key A Accepted?")
    d.add_node("d_auth_pass", "AUTH_SUCCESS (Access Granted)", 600, 970, 220, 50, "terminal", sublabel="Secure Sector Validation")
    d.add_node("d_auth_fail", "AUTH_FAILED (Access Denied)", 880, 970, 220, 50, "error", sublabel="Key Rejection / Tamper Detected")

    # Join Node: Benchmark Delta-t
    d.add_node("d_bench_calc", "D3: Stop Benchmark Timer", 560, 1055, 260, 55, "process", sublabel="readTimeUs = micros() - startTime\nTag Family Classified (SAK/ATQA)")

    # Storage & Telemetry Lane (Right Side)
    d.add_node("d_flash_commit", "D4: LittleFS Flash Append", 1200, 750, 240, 60, "critical", sublabel="appendScanRecord() -> /scans.jsonl\nPersists across hardware reboot")
    d.add_node("d_oled_update", "D5: Refresh SSD1306 OLED", 1200, 850, 240, 60, "process", sublabel="Render UID, readTimeUs, authStatus\nI2C Transfer (4,200 µs)")
    d.add_node("d_web_serve", "D6: Async Web Dashboard", 1200, 950, 240, 60, "process", sublabel="Serve /api/logs & index.html\nNon-blocking AsyncTCP Thread")

    # Halt & Teardown
    d.add_node("d_halt", "D7: RF Transponder Teardown", 560, 1145, 260, 50, "process", sublabel="rfid.PICC_HaltA(); rfid.PCD_StopCrypto1();")
    d.add_node("d_delay", "D8: Loop Interval Delay", 560, 1225, 260, 45, "process", sublabel="delay(1500) | Low Power Quiescence")

    # Data Repositories
    d.add_node("store_flash_mem", "PHYSICAL SPI FLASH", 1220, 650, 200, 55, "storage", sublabel="/scans.jsonl Partition")

    # Control Edges
    d.add_edge("sys_power", "sys_init", "Boot", "control")
    d.add_edge("sys_init", "c_poll_card", "Enter loop()", "control")
    d.add_edge("c_poll_card", "c_poll_card", "No (Idle Polling)", "loopback", exit_point=(1, 0.5), entry_point=(1, 0.2))
    d.add_edge("c_poll_card", "c_read_serial", "Yes (Card in Field)", "control")
    d.add_edge("c_read_serial", "c_poll_card", "No (Collision/Drop)", "loopback")
    d.add_edge("c_read_serial", "d_t0_start", "Yes (Serial Acquired)", "control")
    
    d.add_edge("d_t0_start", "d_format_uid", "Timer Running", "control")
    d.add_edge("d_format_uid", "c_mode_branch", "UID Parsed", "control")

    # Branching
    d.add_edge("c_mode_branch", "d_level1_audit", "Level 1: Fast UID", "control")
    d.add_edge("c_mode_branch", "d_level2_exec", "Level 2: Cryptographic", "control")

    d.add_edge("d_level1_audit", "d_level1_warn", "Audit Evaluation", "control")
    d.add_edge("d_level1_warn", "d_bench_calc", "Record ~2.8ms", "control")

    d.add_edge("d_level2_exec", "c_auth_ok", "Handshake Returned", "control")
    d.add_edge("c_auth_ok", "d_auth_pass", "Yes (Key A Valid)", "control")
    d.add_edge("c_auth_ok", "d_auth_fail", "No (Auth Error)", "error")
    d.add_edge("d_auth_pass", "d_bench_calc", "Record ~30.2ms", "control")
    d.add_edge("d_auth_fail", "d_bench_calc", "Record Failure", "control")

    d.add_edge("d_bench_calc", "d_flash_commit", "Dispatch Record", "control")
    d.add_edge("d_flash_commit", "d_oled_update", "Flash Written", "control")
    d.add_edge("d_oled_update", "d_web_serve", "UI Refreshed", "control")
    d.add_edge("d_web_serve", "d_halt", "Events Flushed", "control")

    d.add_edge("d_halt", "d_delay", "RF Off", "control")
    d.add_edge("d_delay", "c_poll_card", "Next Scan Cycle", "loopback", exit_point=(0, 0.5), entry_point=(0, 0.5))

    # Data Edges
    d.add_edge("d_bench_calc", "d_flash_commit", "Log JSON Payload", "data")
    d.add_edge("d_flash_commit", "store_flash_mem", "Physical Page Write", "data")
    d.add_edge("d_bench_calc", "d_oled_update", "UID & Latency Delta", "data")

    return d


import xml.etree.ElementTree as ET

def render_external_drawio_to_svg(drawio_path, svg_path):
    """Converts a Draw.io XML file to a clean, styled SVG."""
    tree = ET.parse(drawio_path)
    root = tree.getroot()
    graph_model = root.find('.//mxGraphModel')
    page_w = int(graph_model.attrib.get('pageWidth', '1600')) if graph_model is not None else 1600
    page_h = int(graph_model.attrib.get('pageHeight', '1100')) if graph_model is not None else 1100
    bg = graph_model.attrib.get('background', '#0f172a') if graph_model is not None else '#0f172a'

    nodes = []
    edges = []
    cell_dict = {}

    for cell in root.findall('.//mxCell'):
        cid = cell.attrib.get('id')
        if cid in ('0', '1'):
            continue
        val = cell.attrib.get('value', '')
        style_str = cell.attrib.get('style', '')
        style = {}
        for part in style_str.split(';'):
            if '=' in part:
                k, v = part.split('=', 1)
                style[k.strip()] = v.strip()
            elif part.strip():
                style[part.strip()] = True

        geo = cell.find('mxGeometry')
        is_edge = cell.attrib.get('edge') == '1'
        info = {
            'id': cid, 'val': val, 'style': style, 'style_str': style_str,
            'is_edge': is_edge, 'source': cell.attrib.get('source'),
            'target': cell.attrib.get('target'), 'geo': geo
        }
        cell_dict[cid] = info
        if is_edge:
            edges.append(info)
        else:
            nodes.append(info)

    min_x, min_y, max_x, max_y = 99999, 99999, 0, 0
    for n in nodes:
        geo = n['geo']
        if geo is not None and 'x' in geo.attrib and 'y' in geo.attrib:
            x = float(geo.attrib['x'])
            y = float(geo.attrib['y'])
            w = float(geo.attrib.get('width', '100'))
            h = float(geo.attrib.get('height', '50'))
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + w)
            max_y = max(max_y, y + h)

    vw = max(int(max_x + 50), page_w, 1600)
    vh = max(int(max_y + 50), page_h, 1000)

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw} {vh}" width="{vw}" height="{vh}" style="background-color: {bg}; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif;">')
    svg.append('  <defs>')
    svg.append('    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9 z" fill="#818cf8" /></marker>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9 z" fill="#10b981" /></marker>')
    svg.append('    <marker id="arrow-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9 z" fill="#ef4444" /></marker>')
    svg.append('    <marker id="arrow-amber" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9 z" fill="#f59e0b" /></marker>')
    svg.append('    <marker id="arrow-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9 z" fill="#38bdf8" /></marker>')
    svg.append('    <marker id="arrow-gold" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9 z" fill="#facc15" /></marker>')
    svg.append('    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000" flood-opacity="0.35"/></filter>')
    svg.append('  </defs>')

    for e in edges:
        src = cell_dict.get(e['source'])
        tgt = cell_dict.get(e['target'])
        if not src or not tgt or src['geo'] is None or tgt['geo'] is None:
            continue
        sx = float(src['geo'].attrib['x']) + float(src['geo'].attrib.get('width', '100'))/2
        sy = float(src['geo'].attrib['y']) + float(src['geo'].attrib.get('height', '50'))/2
        tx = float(tgt['geo'].attrib['x']) + float(tgt['geo'].attrib.get('width', '100'))/2
        ty = float(tgt['geo'].attrib['y']) + float(tgt['geo'].attrib.get('height', '50'))/2

        if 'exitX' in e['style'] and 'exitY' in e['style']:
            ex = float(e['style']['exitX'])
            ey = float(e['style']['exitY'])
            sx = float(src['geo'].attrib['x']) + float(src['geo'].attrib.get('width', '100')) * ex
            sy = float(src['geo'].attrib['y']) + float(src['geo'].attrib.get('height', '50')) * ey

        if 'entryX' in e['style'] and 'entryY' in e['style']:
            enx = float(e['style']['entryX'])
            eny = float(e['style']['entryY'])
            tx = float(tgt['geo'].attrib['x']) + float(tgt['geo'].attrib.get('width', '100')) * enx
            ty = float(tgt['geo'].attrib['y']) + float(tgt['geo'].attrib.get('height', '50')) * eny

        stroke = e['style'].get('strokeColor', '#818cf8')
        stroke_w = e['style'].get('strokeWidth', '2')
        dash = 'stroke-dasharray="6,4"' if 'dashed' in e['style'] else ''
        
        marker_id = 'arrow'
        if stroke == '#10b981': marker_id = 'arrow-green'
        elif stroke in ('#ef4444', '#f87171'): marker_id = 'arrow-red'
        elif stroke == '#f59e0b': marker_id = 'arrow-amber'
        elif stroke == '#38bdf8': marker_id = 'arrow-blue'
        elif stroke == '#facc15': marker_id = 'arrow-gold'

        mid_x = (sx + tx) / 2
        path_d = f"M {sx} {sy} L {mid_x} {sy} L {mid_x} {ty} L {tx} {ty}"
        svg.append(f'  <path d="{path_d}" fill="none" stroke="{stroke}" stroke-width="{stroke_w}" {dash} marker-end="url(#{marker_id})" />')

        if e['val']:
            lbl_x = mid_x
            lbl_y = (sy + ty) / 2
            svg.append(f'  <foreignObject x="{lbl_x - 110}" y="{lbl_y - 15}" width="220" height="40" style="overflow: visible;">')
            svg.append(f'    <div xmlns="http://www.w3.org/1999/xhtml" style="background:#0f172a; border:0.8px solid {stroke}; border-radius:4px; padding:2px 6px; font-size:9px; color:{stroke}; text-align:center; display:inline-block; max-width:210px; font-family: monospace;">')
            svg.append(f'      {e["val"]}')
            svg.append('    </div>')
            svg.append('  </foreignObject>')

    for n in nodes:
        geo = n['geo']
        if geo is None or 'x' not in geo.attrib or 'y' not in geo.attrib:
            continue
        x = float(geo.attrib['x'])
        y = float(geo.attrib['y'])
        w = float(geo.attrib.get('width', '100'))
        h = float(geo.attrib.get('height', '50'))
        st = n['style']

        fill = st.get('fillColor', 'none')
        stroke = st.get('strokeColor', 'none')
        stroke_w = st.get('strokeWidth', '1')
        dash = 'stroke-dasharray="6,4"' if 'dashed' in st else ''

        is_ellipse = 'ellipse' in st
        is_rhombus = 'rhombus' in st
        is_line = st.get('shape') == 'line'
        rx = '8' if 'rounded' in st else '0'

        svg.append(f'  <g id="{n["id"]}">')
        if is_line:
            svg.append(f'    <line x1="{x}" y1="{y}" x2="{x+w}" y2="{y}" stroke="{stroke}" stroke-width="{stroke_w}" />')
        elif is_rhombus:
            pts = f"{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}"
            svg.append(f'    <polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}" {dash} />')
        elif is_ellipse:
            svg.append(f'    <ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}" {dash} />')
        elif fill != 'none' or stroke != 'none':
            svg.append(f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}" {dash} filter="url(#shadow)" />')

        if n['val']:
            f_col = st.get('fontColor', '#f8fafc')
            f_size = st.get('fontSize', '11')
            is_swimlane = 'swimlane' in st
            align = 'left' if is_swimlane else st.get('align', 'center')
            valign = st.get('verticalAlign', 'middle')
            start_size = float(st.get('startSize', '36')) if is_swimlane else 0
            
            valign_css = "display: flex; flex-direction: column; justify-content: center;"
            if is_swimlane:
                valign_css = "display: flex; flex-direction: column; justify-content: center; padding-left: 16px; font-weight: bold; letter-spacing: 0.5px;"
                box_h = start_size
            elif valign == 'top':
                valign_css = "display: flex; flex-direction: column; justify-content: flex-start; padding-top: 6px;"
                box_h = h
            elif valign == 'bottom':
                valign_css = "display: flex; flex-direction: column; justify-content: flex-end; padding-bottom: 6px;"
                box_h = h
            else:
                box_h = h

            svg.append(f'    <foreignObject x="{x}" y="{y}" width="{w}" height="{box_h}">')
            svg.append(f'      <div xmlns="http://www.w3.org/1999/xhtml" style="width:100%; height:100%; box-sizing:border-box; color:{f_col}; font-size:{f_size}px; text-align:{align}; {valign_css} font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;">')
            svg.append(f'        {n["val"]}')
            svg.append('      </div>')
            svg.append('    </foreignObject>')

        svg.append('  </g>')

    svg.append('</svg>')
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))
    print(f"Generated SVG:     {svg_path}")


def extract_diagram_xml(filepath):
    """Extracts the <diagram ...>...</diagram> element string from a .drawio file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'(<diagram[\s\S]*?</diagram>)', content)
    if match:
        return match.group(1)
    return ""


def main():
    out_dir = "/Users/rajveermodi/Documents/GitHub/esp32-nfc/docs/diagrams"
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Build programmatic diagrams
    d1 = create_dfg_crypto_auth()
    d2 = create_dfg_telemetry()
    d3 = create_cdfg_critical_function()
    d4 = create_cdfg_system_main_loop()

    diagrams = [
        ("dfg_crypto_auth", d1),
        ("dfg_system_telemetry", d2),
        ("cdfg_authenticate_and_read", d3),
        ("cdfg_system_main_loop", d4)
    ]

    # 2. Export Standalone .drawio and .svg for programmatic models
    for filename, diag in diagrams:
        xml_content = f'''<mxfile host="app.diagrams.net" modified="2026-10-29T17:00:00.000Z" agent="Mozilla/5.0" version="24.0.0" type="device">
{diag.to_drawio_xml_diagram()}
</mxfile>'''
        drawio_path = os.path.join(out_dir, f"{filename}.drawio")
        with open(drawio_path, "w", encoding="utf-8") as f:
            f.write(xml_content)
        print(f"Generated Draw.io: {drawio_path}")

        svg_content = diag.to_svg()
        svg_path = os.path.join(out_dir, f"{filename}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Generated SVG:     {svg_path}")

    # 3. Render Standalone SVGs for the other 3 diagrams
    external_diagrams = [
        "system_block_diagram",
        "wokwi_system_block_diagram",
        "fsm_system_behaviour",
        "task_schedule_timeline"
    ]
    for ext_name in external_diagrams:
        dpath = os.path.join(out_dir, f"{ext_name}.drawio")
        spath = os.path.join(out_dir, f"{ext_name}.svg")
        if os.path.exists(dpath):
            render_external_drawio_to_svg(dpath, spath)

    # 4. Export Master Multi-Page .drawio file (Contains all 7 tabs!)
    master_xml = ['<mxfile host="app.diagrams.net" modified="2026-10-29T17:00:00.000Z" agent="Mozilla/5.0" version="24.0.0" type="device">']
    
    # Tab 1: System Block Diagram (Fig 1 Hardware)
    sbd_diag = extract_diagram_xml(os.path.join(out_dir, "system_block_diagram.drawio"))
    if sbd_diag: master_xml.append(sbd_diag)

    # Tab 1b: Wokwi Virtual Setup Block Diagram
    wokwi_diag = extract_diagram_xml(os.path.join(out_dir, "wokwi_system_block_diagram.drawio"))
    if wokwi_diag: master_xml.append(wokwi_diag)

    # Tab 2: Critical Function CDFG (Fig 2)
    master_xml.append(d3.to_drawio_xml_diagram())

    # Tab 3: System Main Loop CDFG
    master_xml.append(d4.to_drawio_xml_diagram())

    # Tab 4: Critical Path DFG
    master_xml.append(d1.to_drawio_xml_diagram())

    # Tab 5: System Telemetry DFG
    master_xml.append(d2.to_drawio_xml_diagram())

    # Tab 6: System-Behaviour FSM (Fig 3)
    fsm_diag = extract_diagram_xml(os.path.join(out_dir, "fsm_system_behaviour.drawio"))
    if fsm_diag: master_xml.append(fsm_diag)

    # Tab 7: Task Schedule & Schedulability Proof (Fig 4)
    tsk_diag = extract_diagram_xml(os.path.join(out_dir, "task_schedule_timeline.drawio"))
    if tsk_diag: master_xml.append(tsk_diag)

    master_xml.append('</mxfile>')
    
    master_drawio_path = os.path.join(out_dir, "esp32_nfc_complete_models.drawio")
    with open(master_drawio_path, "w", encoding="utf-8") as f:
        f.write("\n".join(master_xml))
    print(f"\nSUCCESS: Master Multi-Page Draw.io (7 tabs) generated at:\n  {master_drawio_path}")


if __name__ == "__main__":
    main()
