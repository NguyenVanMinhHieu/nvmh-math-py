"""Module sinh tài liệu Typst Chuẩn Sư phạm Toán THPT Việt Nam.

Tương thích tuyệt đối với Typst 0.15+ và CeTZ 0.5.2.
Đặc tính:
1. Ánh xạ trực tiếp từ GeometricSceneIR (Song ánh với TikZ).
2. Tự động sinh Bảng biến thiên động 10/10 cho mọi hàm số (bậc 3, trùng phương, phân thức 1/1, 2/1).
3. Đồ thị Oxy CeTZ chính xác từng milimet từ các nhánh Hard-Clamped.
"""

from __future__ import annotations

import math
from typing import Any, List, Optional, Tuple

import sympy as sp

from nvmh_math_py.geometry_ir import (
    GeometricSceneIR,
    TablePointIR,
    VariationIntervalIR,
    build_geometric_scene,
)


def sympy_to_typst_expr(expr: sp.Expr) -> str:
    """Chuyển biểu thức SymPy sang cú pháp toán Typst đẹp mắt."""
    if expr is None:
        return ""
    numer, denom = sp.fraction(expr)
    if denom != 1:
        denom_factored = sp.factor(denom)
        s_num = sp.printing.sstr(numer).replace("**", "^").replace("*", " ")
        s_den = sp.printing.sstr(denom_factored).replace("**", "^").replace("*", " ")
        return f"({s_num}) / ({s_den})"

    s = sp.printing.sstr(expr).replace("**", "^").replace("*", " ")
    s = s.replace("log(", "ln(")
    return s


def _format_cell_math(s: str) -> str:
    """Bọc ký hiệu toán học an toàn cho cell Typst."""
    s = s.strip()
    if not s:
        return ""
    if s.startswith("$") and s.endswith("$"):
        return s
    return f"${s}$"


def generate_typst_variation_table(scene: GeometricSceneIR) -> str:
    """Sinh mã bảng biến thiên Typst động chuẩn sư phạm THPT từ GeometricSceneIR."""
    pts = scene.table.points
    intervals = scene.table.intervals

    if not pts or not intervals:
        return "/* Bảng biến thiên không có dữ liệu */"

    num_intervals = len(intervals)
    inter_points = pts[1:-1]  # Các điểm mốc ở giữa (cực trị hoặc tiệm cận đứng)
    num_inter = len(inter_points)

    # 1. Tính toán độ rộng các cột
    # Tổng độ rộng khả dụng cho các cột dữ liệu ~ 10.0cm -> 12.0cm
    hdr_width = "1.8cm"
    inter_col_width = "0.9cm"
    if num_intervals == 1:
        seg_col_width = "9.0cm"
    elif num_intervals == 2:
        seg_col_width = "4.2cm"
    elif num_intervals == 3:
        seg_col_width = "2.8cm"
    else:
        seg_col_width = f"{max(1.8, round(8.5 / num_intervals, 2))}cm"

    col_widths = [hdr_width]
    for i in range(num_intervals):
        col_widths.append(seg_col_width)
        if i < num_inter:
            col_widths.append(inter_col_width)

    cols_str = "(" + ", ".join(col_widths) + ")"

    # 2. Xây dựng hàng x
    x_cells = ["[$x$]"]
    for i in range(num_intervals):
        # Ô khoảng của x
        p_left = pts[i]
        p_right = pts[i + 1]

        left_x_str = f"{p_left.x_typst}^+" if (i > 0 and p_left.is_pole) else (p_left.x_typst if i == 0 else "")
        right_x_str = f"{p_right.x_typst}^-" if (i < num_intervals - 1 and p_right.is_pole) else (p_right.x_typst if i == num_intervals - 1 else "")

        if left_x_str and right_x_str:
            x_cells.append(
                f"[#grid(columns: (1fr, 1fr), align: (left, right), [{_format_cell_math(left_x_str)}], [{_format_cell_math(right_x_str)}])]"
            )
        elif left_x_str:
            x_cells.append(
                f"[#grid(columns: (1fr, 1fr), align: (left, right), [{_format_cell_math(left_x_str)}], [])]"
            )
        elif right_x_str:
            x_cells.append(
                f"[#grid(columns: (1fr, 1fr), align: (left, right), [], [{_format_cell_math(right_x_str)}])]"
            )
        else:
            x_cells.append("[]")

        # Ô điểm mốc ở giữa
        if i < num_inter:
            mid_pt = inter_points[i]
            x_cells.append(f"[{_format_cell_math(mid_pt.x_typst)}]")

    # 3. Xây dựng hàng y'
    yprime_cells = ["[$y'$]"]
    for i in range(num_intervals):
        inv = intervals[i]
        yprime_cells.append(f"[{_format_cell_math(inv.sign)}]")
        if i < num_inter:
            mid_pt = inter_points[i]
            mark_str = "$||$" if mid_pt.is_pole else ("$0$" if mid_pt.derivative_mark == "0" else "")
            yprime_cells.append(f"[{mark_str}]")

    # 4. Xây dựng hàng y (chiều mũi tên và các mốc cực trị / tiệm cận)
    y_cells = ["[$y$]"]
    for i in range(num_intervals):
        inv = intervals[i]
        p_left = pts[i]
        p_right = pts[i + 1]

        # Kiểm tra xem mốc trái / phải có phải là điểm cực trị không
        is_left_extrema = (i > 0) and (not p_left.is_pole) and (p_left.derivative_mark == "0")
        is_right_extrema = (i < num_intervals - 1) and (not p_right.is_pole) and (p_right.derivative_mark == "0")

        y_s = inv.y_start_typst
        y_e = inv.y_end_typst

        if inv.arrow_direction == "up":
            arrow = "$arrow.tr$"
            if not is_left_extrema and not is_right_extrema:
                y_cells.append(
                    f"[\n      #grid(\n        columns: (1fr, 1fr, 1fr),\n        align: (left + bottom, center + horizon, right + top),\n        [{_format_cell_math(y_s)}], [{arrow}], [{_format_cell_math(y_e)}]\n      )\n    ]"
                )
            elif is_left_extrema and not is_right_extrema:
                y_cells.append(
                    f"[\n      #grid(\n        columns: (1fr, 1fr),\n        align: (center + horizon, right + top),\n        [{arrow}], [{_format_cell_math(y_e)}]\n      )\n    ]"
                )
            elif not is_left_extrema and is_right_extrema:
                y_cells.append(
                    f"[\n      #grid(\n        columns: (1fr, 1fr),\n        align: (left + bottom, center + horizon),\n        [{_format_cell_math(y_s)}], [{arrow}]\n      )\n    ]"
                )
            else:
                y_cells.append(f"[{arrow}]")
        else:
            arrow = "$arrow.br$"
            if not is_left_extrema and not is_right_extrema:
                y_cells.append(
                    f"[\n      #grid(\n        columns: (1fr, 1fr, 1fr),\n        align: (left + top, center + horizon, right + bottom),\n        [{_format_cell_math(y_s)}], [{arrow}], [{_format_cell_math(y_e)}]\n      )\n    ]"
                )
            elif is_left_extrema and not is_right_extrema:
                y_cells.append(
                    f"[\n      #grid(\n        columns: (1fr, 1fr),\n        align: (center + horizon, right + bottom),\n        [{arrow}], [{_format_cell_math(y_e)}]\n      )\n    ]"
                )
            elif not is_left_extrema and is_right_extrema:
                y_cells.append(
                    f"[\n      #grid(\n        columns: (1fr, 1fr),\n        align: (left + top, center + horizon),\n        [{_format_cell_math(y_s)}], [{arrow}]\n      )\n    ]"
                )
            else:
                y_cells.append(f"[{arrow}]")

        # Ô giá trị mốc giữa
        if i < num_inter:
            mid_pt = inter_points[i]
            if mid_pt.is_pole:
                y_cells.append("[]")  # Cột tiệm cận đứng, có thể vẽ nét đôi
            else:
                # Đỉnh cực đại thì căn top, cực tiểu thì căn bottom
                align_y = "top" if (inv.arrow_direction == "up") else "bottom"
                y_cells.append(f"[#align({align_y})[{_format_cell_math(mid_pt.y_typst)}]]")

    rows_code = ",\n    ".join(x_cells) + ",\n    " + ",\n    ".join(yprime_cells) + ",\n    " + ",\n    ".join(y_cells)

    return f"""  #table(
    columns: {cols_str},
    align: center + horizon,
    fill: (col, row) => if row == 0 {{ gray.lighten(85%) }} else {{ none }},
    stroke: (col, row) => (
      top: if row == 0 {{ 1pt + black }} else {{ 0.5pt + gray }},
      bottom: if row == 2 {{ 1pt + black }} else {{ 0.5pt + gray }},
      right: if col == 0 {{ 1pt + black }} else {{ none }},
      left: none
    ),
    {rows_code}
  )"""


def generate_cetz_graph_code(scene: GeometricSceneIR) -> str:
    """Sinh toàn bộ mã CeTZ vẽ hệ trục Oxy, tiệm cận, nhánh đồ thị và điểm cực trị."""
    graph = scene.graph
    x_min, x_max = graph.x_range
    y_min, y_max = graph.y_range

    lines: List[str] = [
        "  import cetz.draw: *",
        "  // 1. Lưới toạ độ phụ",
    ]
    for xi in range(int(math.ceil(x_min)), int(math.floor(x_max)) + 1):
        if xi != 0:
            lines.append(f"  line(({xi}.0, {y_min:.1f}), ({xi}.0, {y_max:.1f}), stroke: 0.25pt + gray.lighten(70%))")
    for yi in range(int(math.ceil(y_min)), int(math.floor(y_max)) + 1):
        if yi != 0:
            lines.append(f"  line(({x_min:.1f}, {yi}.0), ({x_max:.1f}, {yi}.0), stroke: 0.25pt + gray.lighten(70%))")

    lines += [
        "\n  // 2. Trục toạ độ Oxy chính",
        f"  line(({x_min - 0.4:.2f}, 0.0), ({x_max + 0.6:.2f}, 0.0), mark: (end: \">\"), stroke: 0.9pt)",
        f"  line((0.0, {y_min - 0.4:.2f}), (0.0, {y_max + 0.6:.2f}), mark: (end: \">\"), stroke: 0.9pt)",
        f"  content(({x_max + 0.7:.2f}, -0.3), text(10pt)[$x$])",
        f"  content((-0.3, {y_max + 0.7:.2f}), text(10pt)[$y$])",
        "  content((-0.3, -0.3), text(9pt)[$O$])",
        "",
        "  // 3. Vạch chia số trên hai trục",
    ]

    for xi in range(int(math.ceil(x_min)), int(math.floor(x_max)) + 1):
        if xi != 0:
            lines.append(f"  line(({xi}.0, 0.08), ({xi}.0, -0.08), stroke: 0.7pt)")
            lines.append(f"  content(({xi}.0, -0.35), text(7.5pt)[${xi}$])")
    for yi in range(int(math.ceil(y_min)), int(math.floor(y_max)) + 1):
        if yi != 0:
            lines.append(f"  line((0.08, {yi}.0), (-0.08, {yi}.0), stroke: 0.7pt)")
            lines.append(f"  content((-0.35, {yi}.0), text(7.5pt)[${yi}$])")

    lines.append("\n  // 4. Các đường tiệm cận từ IR")
    for asy in graph.asymptotes:
        lines.append(
            f"  line(({asy.start.x:.2f}, {asy.start.y:.2f}), ({asy.end.x:.2f}, {asy.end.y:.2f}), "
            f"stroke: (paint: red, dash: \"dashed\", thickness: 0.9pt))"
        )
        lines.append(
            f"  content(({asy.label_pos.x:.2f}, {asy.label_pos.y:.2f}), text(8.5pt, red)[${asy.typst_label}$])"
        )

    lines.append("\n  // 5. Đường gióng và điểm cực trị từ IR")
    for gl in graph.guide_lines:
        lines.append(
            f"  line(({gl.proj_x.x:.2f}, {gl.proj_x.y:.2f}), ({gl.point.x:.2f}, {gl.point.y:.2f}), ({gl.proj_y.x:.2f}, {gl.proj_y.y:.2f}), "
            f"stroke: (paint: gray, dash: \"dotted\", thickness: 0.6pt))"
        )

    for cp in graph.critical_points:
        lines.append(f"  circle(({cp.x:.2f}, {cp.y:.2f}), radius: 2.2pt, fill: black)")

    lines.append("\n  // 6. Các nhánh đồ thị f(x) đã Hard-Clamping từ IR")
    for br in graph.branches:
        if len(br.points) >= 2:
            pts_str = ", ".join([f"({p.x:.2f}, {p.y:.2f})" for p in br.points])
            lines.append(f"  line({pts_str}, stroke: (paint: blue.darken(25%), thickness: 1.4pt))")

    return "\n".join(lines)


def generate_typst_document(
    analysis: Any,
    x_range: Tuple[float, float] = (-6.0, 6.0),
    y_range: Tuple[float, float] = (-6.0, 6.0),
) -> str:
    """Sinh toàn bộ tài liệu Typst chuẩn xuất bản chuyên nghiệp dựa trên Geometric IR."""
    scene = build_geometric_scene(analysis, x_range=x_range, y_range=y_range)

    table_code = generate_typst_variation_table(scene)
    cetz_body = generate_cetz_graph_code(scene)

    return f"""#set page(paper: "a4", margin: (x: 1.8cm, y: 1.8cm))
#set text(font: "New Computer Modern", size: 11pt, lang: "vi")

#align(center)[
  #text(16pt, weight: "bold", fill: blue.darken(40%))[BÁO CÁO KHẢO SÁT HÀM SỐ]
]

#v(0.2cm)

== 1. Biểu thức Giải tích
#rect(width: 100%, stroke: 0.5pt + gray.lighten(50%), inset: 10pt, radius: 4pt)[
  - *Hàm số khảo sát:* $y = {scene.formula_typst}$
  - *Đạo hàm cấp một:* $y' = {scene.diff_formula_typst}$
]

== 2. Bảng biến thiên (Chuẩn Sư phạm THPT)
#align(center)[
{table_code}
]

== 3. Đồ thị hàm số phẳng Oxy
#import "@preview/cetz:0.5.2"

#align(center)[
  #cetz.canvas(length: 0.85cm, {{
{cetz_body}
  }})
]
"""
