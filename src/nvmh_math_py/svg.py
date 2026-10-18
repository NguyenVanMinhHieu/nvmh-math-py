"""Module sinh hình ảnh Vector SVG và hỗ trợ xuất PNG chuẩn Sư phạm THPT.

Ánh xạ trực tiếp từ GeometricSceneIR sang đồ họa trực quan (Visual Graph & Variation Table).
"""

from __future__ import annotations

import math
from typing import List, Tuple

from nvmh_math_py.geometry_ir import GeometricSceneIR


def generate_graph_svg(
    scene: GeometricSceneIR,
    width: int = 680,
    height: int = 560,
    margin: int = 45,
    theme: str = "light",
) -> str:
    """Sinh ảnh đồ thị phẳng Oxy dạng Vector SVG từ Geometric IR."""
    graph = scene.graph
    x_min, x_max = graph.x_range
    y_min, y_max = graph.y_range

    def sx(x: float) -> float:
        return margin + (x - x_min) / (x_max - x_min) * (width - 2 * margin)

    def sy(y: float) -> float:
        return (height - margin) - (y - y_min) / (y_max - y_min) * (height - 2 * margin)

    bg_color = "#ffffff" if theme == "light" else "#0f172a"
    grid_color = "#e2e8f0" if theme == "light" else "#334155"
    axis_color = "#1e293b" if theme == "light" else "#cbd5e1"
    text_color = "#0f172a" if theme == "light" else "#f8fafc"
    curve_color = "#2563eb"
    asym_color = "#ef4444"

    clip_x = sx(x_min)
    clip_y = sy(y_max)
    clip_w = sx(x_max) - sx(x_min)
    clip_h = sy(y_min) - sy(y_max)

    svg_parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="auto" style="background:{bg_color}; border-radius:8px; font-family:system-ui, sans-serif;">',
        '  <defs>',
        '    <marker id="arrow-axis" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        f'      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="{axis_color}"/>',
        '    </marker>',
        f'    <clipPath id="graph-viewport-clip">',
        f'      <rect x="{clip_x:.1f}" y="{clip_y:.1f}" width="{clip_w:.1f}" height="{clip_h:.1f}"/>',
        '    </clipPath>',
        '  </defs>',
        f'  <rect width="{width}" height="{height}" fill="{bg_color}"/>',
        '  <!-- 1. Lưới toạ độ phụ -->',
    ]

    for xi in range(int(math.ceil(x_min)), int(math.floor(x_max)) + 1):
        if xi != 0:
            px = sx(xi)
            svg_parts.append(f'  <line x1="{px:.1f}" y1="{sy(y_min):.1f}" x2="{px:.1f}" y2="{sy(y_max):.1f}" stroke="{grid_color}" stroke-width="0.8"/>')

    for yi in range(int(math.ceil(y_min)), int(math.floor(y_max)) + 1):
        if yi != 0:
            py = sy(yi)
            svg_parts.append(f'  <line x1="{sx(x_min):.1f}" y1="{py:.1f}" x2="{sx(x_max):.1f}" y2="{py:.1f}" stroke="{grid_color}" stroke-width="0.8"/>')

    ox = sx(0.0)
    oy = sy(0.0)

    # 2. Trục toạ độ chính
    svg_parts.append('\n  <!-- 2. Trục toạ độ Oxy -->')
    svg_parts.append(f'  <line x1="{sx(x_min)-10:.1f}" y1="{oy:.1f}" x2="{sx(x_max)+20:.1f}" y2="{oy:.1f}" stroke="{axis_color}" stroke-width="1.8" marker-end="url(#arrow-axis)"/>')
    svg_parts.append(f'  <line x1="{ox:.1f}" y1="{sy(y_min)+10:.1f}" x2="{ox:.1f}" y2="{sy(y_max)-20:.1f}" stroke="{axis_color}" stroke-width="1.8" marker-end="url(#arrow-axis)"/>')
    svg_parts.append(f'  <text x="{sx(x_max)+25:.1f}" y="{oy+4:.1f}" font-size="13" font-style="italic" font-weight="600" fill="{text_color}">x</text>')
    svg_parts.append(f'  <text x="{ox-4:.1f}" y="{sy(y_max)-25:.1f}" font-size="13" font-style="italic" font-weight="600" fill="{text_color}" text-anchor="end">y</text>')
    svg_parts.append(f'  <text x="{ox-8:.1f}" y="{oy+14:.1f}" font-size="12" font-style="italic" fill="{text_color}" text-anchor="end">O</text>')

    # 3. Vạch chia số
    for xi in range(int(math.ceil(x_min)), int(math.floor(x_max)) + 1):
        if xi != 0:
            px = sx(xi)
            svg_parts.append(f'  <line x1="{px:.1f}" y1="{oy-3:.1f}" x2="{px:.1f}" y2="{oy+3:.1f}" stroke="{axis_color}" stroke-width="1.2"/>')
            svg_parts.append(f'  <text x="{px:.1f}" y="{oy+16:.1f}" font-size="10" fill="{text_color}" text-anchor="middle">{xi}</text>')

    for yi in range(int(math.ceil(y_min)), int(math.floor(y_max)) + 1):
        if yi != 0:
            py = sy(yi)
            svg_parts.append(f'  <line x1="{ox-3:.1f}" y1="{py:.1f}" x2="{ox+3:.1f}" y2="{py:.1f}" stroke="{axis_color}" stroke-width="1.2"/>')
            svg_parts.append(f'  <text x="{ox-8:.1f}" y="{py+4:.1f}" font-size="10" fill="{text_color}" text-anchor="end">{yi}</text>')

    # 4. Tiệm cận, đường gióng và đồ thị f(x) ĐƯỢC CLIP GỌN TRONG LƯỚI TOẠ ĐỘ
    svg_parts.append('\n  <!-- Vùng đồ thị & tiệm cận được Clip chuẩn xuất bản SGK -->')
    svg_parts.append('  <g clip-path="url(#graph-viewport-clip)">')
    for asy in graph.asymptotes:
        x1, y1 = sx(asy.start.x), sy(asy.start.y)
        x2, y2 = sx(asy.end.x), sy(asy.end.y)
        svg_parts.append(f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{asym_color}" stroke-width="1.4" stroke-dasharray="6,4"/>')
    for gl in graph.guide_lines:
        px, py = sx(gl.point.x), sy(gl.point.y)
        g_ox = sx(0.0)
        g_oy = sy(0.0)
        svg_parts.append(f'    <polyline points="{px:.1f},{g_oy:.1f} {px:.1f},{py:.1f} {g_ox:.1f},{py:.1f}" fill="none" stroke="#64748b" stroke-width="1.0" stroke-dasharray="3,3"/>')
    for br in graph.branches:
        if len(br.points) >= 2:
            pts_str = " ".join([f"{sx(p.x):.1f},{sy(p.y):.1f}" for p in br.points])
            svg_parts.append(f'    <polyline points="{pts_str}" fill="none" stroke="{curve_color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')
    svg_parts.append('  </g>')

    # 5. Điểm cực trị và nhãn chữ tiệm cận (vẽ ngoài clip để không bị cắt chữ)
    for cp in graph.critical_points:
        cpx, cpy = sx(cp.x), sy(cp.y)
        svg_parts.append(f'  <circle cx="{cpx:.1f}" cy="{cpy:.1f}" r="4.0" fill="#0f172a"/>')
    for asy in graph.asymptotes:
        lx, ly = sx(asy.label_pos.x), sy(asy.label_pos.y)
        svg_parts.append(f'  <text x="{lx:.1f}" y="{ly:.1f}" font-size="11" font-weight="600" fill="{asym_color}">{asy.typst_label}</text>')
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def generate_table_svg(
    scene: GeometricSceneIR,
    width: int = 760,
    height: int = 220,
) -> str:
    """Sinh Bảng biến thiên trực quan dạng Vector SVG chuẩn mực SGK THPT."""
    pts = scene.table.points
    intervals = scene.table.intervals

    if not pts or not intervals:
        return '<svg width="100%" height="60"><text x="20" y="30">Không có dữ liệu bảng biến thiên</text></svg>'

    n_intervals = len(intervals)
    hdr_w = 90.0
    data_w = width - hdr_w
    step_w = data_w / n_intervals

    y_x = 42.0
    y_yprime = 88.0
    y_y_top = 125.0
    y_y_bot = 195.0
    y_y_mid = 160.0

    svg: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="auto" style="background:#ffffff; border-radius:8px; font-family:system-ui, sans-serif;">',
        '  <defs>',
        '    <marker id="arr-up" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '      <path d="M 0 2 L 7 5 L 0 8 z" fill="#1e293b"/>',
        '    </marker>',
        '    <marker id="arr-dn" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '      <path d="M 0 2 L 7 5 L 0 8 z" fill="#1e293b"/>',
        '    </marker>',
        '  </defs>',
        f'  <rect width="{width}" height="{height}" fill="#ffffff" stroke="#334155" stroke-width="1.6" rx="6"/>',
        f'  <rect x="0" y="0" width="{width}" height="{y_x+18:.1f}" fill="#f1f5f9" rx="6"/>',
        f'  <line x1="0" y1="{y_x+18:.1f}" x2="{width}" y2="{y_x+18:.1f}" stroke="#334155" stroke-width="1.2"/>',
        f'  <line x1="0" y1="{y_yprime+18:.1f}" x2="{width}" y2="{y_yprime+18:.1f}" stroke="#334155" stroke-width="1.2"/>',
        f'  <line x1="{hdr_w}" y1="0" x2="{hdr_w}" y2="{height}" stroke="#334155" stroke-width="1.4"/>',
        f'  <text x="{hdr_w/2}" y="{y_x:.1f}" font-size="16" font-style="italic" font-weight="bold" fill="#0f172a" text-anchor="middle">x</text>',
        f'  <text x="{hdr_w/2}" y="{y_yprime:.1f}" font-size="16" font-style="italic" font-weight="bold" fill="#0f172a" text-anchor="middle">y\'</text>',
        f'  <text x="{hdr_w/2}" y="{y_y_mid:.1f}" font-size="16" font-style="italic" font-weight="bold" fill="#0f172a" text-anchor="middle">y</text>',
    ]

    # Điểm toạ độ x của các mốc
    x_coords = [hdr_w + 35.0]
    for i in range(1, len(pts) - 1):
        x_coords.append(hdr_w + i * step_w)
    x_coords.append(width - 35.0)

    # 1. Hàng x
    for i, pt in enumerate(pts):
        xc = x_coords[i]
        label = pt.x_typst.replace("infinity", "∞")
        svg.append(f'  <text x="{xc:.1f}" y="{y_x:.1f}" font-size="13" font-weight="600" fill="#0f172a" text-anchor="middle">{label}</text>')

    # 2. Hàng y'
    for i, inv in enumerate(intervals):
        x_mid = (x_coords[i] + x_coords[i+1]) / 2.0
        svg.append(f'  <text x="{x_mid:.1f}" y="{y_yprime:.1f}" font-size="16" font-weight="bold" fill="#0f172a" text-anchor="middle">{inv.sign}</text>')

    for i in range(1, len(pts) - 1):
        pt = pts[i]
        xc = x_coords[i]
        if pt.is_pole:
            svg.append(f'  <line x1="{xc-2:.1f}" y1="{y_x+18:.1f}" x2="{xc-2:.1f}" y2="{height}" stroke="#0f172a" stroke-width="1.2"/>')
            svg.append(f'  <line x1="{xc+2:.1f}" y1="{y_x+18:.1f}" x2="{xc+2:.1f}" y2="{height}" stroke="#0f172a" stroke-width="1.2"/>')
        elif pt.derivative_mark == "0":
            svg.append(f'  <text x="{xc:.1f}" y="{y_yprime:.1f}" font-size="14" fill="#0f172a" text-anchor="middle">0</text>')

    # 3. Hàng y (Mũi tên và giá trị biến thiên)
    for i, inv in enumerate(intervals):
        pt_l = pts[i]
        pt_r = pts[i+1]
        x1 = x_coords[i] + 18.0
        x2 = x_coords[i+1] - 18.0

        y_s_val = inv.y_start_typst.replace("infinity", "∞")
        y_e_val = inv.y_end_typst.replace("infinity", "∞")

        if inv.arrow_direction == "up":
            y1, y2 = y_y_bot, y_y_top
            svg.append(f'  <line x1="{x1:.1f}" y1="{y1-5:.1f}" x2="{x2:.1f}" y2="{y2+8:.1f}" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-up)"/>')
            if not ((i > 0) and (not pt_l.is_pole) and (pt_l.derivative_mark == "0")):
                svg.append(f'  <text x="{x_coords[i]:.1f}" y="{y_y_bot+12:.1f}" font-size="11" font-weight="600" fill="#0f172a" text-anchor="middle">{y_s_val}</text>')
            if not ((i < n_intervals - 1) and (not pt_r.is_pole) and (pt_r.derivative_mark == "0")):
                svg.append(f'  <text x="{x_coords[i+1]:.1f}" y="{y_y_top-6:.1f}" font-size="11" font-weight="600" fill="#0f172a" text-anchor="middle">{y_e_val}</text>')
        else:
            y1, y2 = y_y_top, y_y_bot
            svg.append(f'  <line x1="{x1:.1f}" y1="{y1+8:.1f}" x2="{x2:.1f}" y2="{y2-5:.1f}" stroke="#1e293b" stroke-width="1.8" marker-end="url(#arr-dn)"/>')
            if not ((i > 0) and (not pt_l.is_pole) and (pt_l.derivative_mark == "0")):
                svg.append(f'  <text x="{x_coords[i]:.1f}" y="{y_y_top-6:.1f}" font-size="11" font-weight="600" fill="#0f172a" text-anchor="middle">{y_s_val}</text>')
            if not ((i < n_intervals - 1) and (not pt_r.is_pole) and (pt_r.derivative_mark == "0")):
                svg.append(f'  <text x="{x_coords[i+1]:.1f}" y="{y_y_bot+12:.1f}" font-size="11" font-weight="600" fill="#0f172a" text-anchor="middle">{y_e_val}</text>')

    # Giá trị cực đại / cực tiểu tại các đỉnh
    for i in range(1, len(pts) - 1):
        pt = pts[i]
        if not pt.is_pole and pt.derivative_mark == "0":
            xc = x_coords[i]
            val = pt.y_typst.replace("infinity", "∞")
            inv_before = intervals[i-1]
            pos_y = y_y_top - 6.0 if inv_before.arrow_direction == "up" else y_y_bot + 12.0
            svg.append(f'  <text x="{xc:.1f}" y="{pos_y:.1f}" font-size="12" font-weight="bold" fill="#0f172a" text-anchor="middle">{val}</text>')

    svg.append('</svg>')
    return "\n".join(svg)
