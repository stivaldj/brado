from __future__ import annotations

from typing import Any


def build_pdf_report(*, title: str, lines: list[str]) -> bytes:
    body_lines = [title, ""] + lines
    escaped = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in body_lines]

    stream_lines = ["BT", "/F1 12 Tf", "50 780 Td"]
    for idx, line in enumerate(escaped):
        if idx == 0:
            stream_lines.append(f"({line}) Tj")
        else:
            stream_lines.append("0 -16 Td")
            stream_lines.append(f"({line}) Tj")
    stream_lines.append("ET")
    stream_content = "\n".join(stream_lines).encode("latin-1", errors="replace")

    objects: list[bytes] = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
    )
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    objects.append(
        b"5 0 obj << /Length "
        + str(len(stream_content)).encode("ascii")
        + b" >> stream\n"
        + stream_content
        + b"\nendstream endobj\n"
    )

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(output))
        output.extend(obj)

    xref_start = len(output)
    output.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        output.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


def format_result_lines(result: dict[str, Any]) -> list[str]:
    payload = result.get("resultado", {})
    vector = payload.get("vetor", {})
    ranking = result.get("ranking", [])

    lines = [
        f"Sessao: {result.get('session_id', '-')}",
        f"Esquerda-Direita: {payload.get('esquerda_direita', 0)}",
        f"Confianca: {payload.get('confianca', 0)}",
        f"Consistencia: {payload.get('consistencia', 0)}",
        "Vetor 8D:",
    ]
    lines.extend([f"  {dim}: {value}" for dim, value in vector.items()])
    lines.append("Top alinhamentos:")
    for row in ranking[:5]:
        lines.append(f"  {row.get('tipo')} {row.get('nome')} ({row.get('similaridade')})")
    return lines
