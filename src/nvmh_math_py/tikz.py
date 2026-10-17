"""Module sinh mã LaTeX/TikZ phục vụ khảo sát hàm số THPT."""

from __future__ import annotations

import logging
import math
from typing import Any, List, Optional, Tuple

import sympy as sp

from nvmh_math_py.geometry_ir import build_geometric_scene

logger = logging.getLogger(__name__)


def _to_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        f_val = float(sp.N(val))
        return f_val if math.isfinite(f_val) else None
    except (TypeError, ValueError):
        return None


def _wrap_math(text: str) -> str:
    s = str(text).strip()
    if not s:
        return ""
    return s if s.startswith("$") else f"${s}$"


def generate_tkz_tab(analysis: Any, standalone: bool = True) -> str:
    """Sinh mã tkz-tab chuẩn THPT dựa trên dấu đạo hàm và bản chất cực trị."""
    try:
        scene = build_geometric_scene(analysis)
        pts = scene.table.points
        intervals = scene.table.intervals

        if not pts:
            return "% Không có dữ liệu điểm để lập bảng biến thiên"

        # 1. Hàng các mốc x
        x_nodes = [_wrap_math(p.x_latex) for p in pts]
        x_str = " , ".join(x_nodes)

        # 2. Hàng dấu đạo hàm y'
        line_elements: List[str] = [""]
        for i, inv in enumerate(intervals):
            line_elements.append(inv.sign)
            if i + 1 < len(pts) - 1:
                mid_pt = pts[i + 1]
                if mid_pt.is_pole:
                    line_elements.append("d")
                elif mid_pt.derivative_mark == "0":
                    line_elements.append("0")
                else:
                    line_elements.append("t")
        line_elements.append("")
        signs_str = " , ".join(line_elements)

        # 3. Hàng biến thiên y (tkzTabVar) suy luận trực tiếp từ dấu đạo hàm
        var_elements: List[str] = []
        n_pts = len(pts)

        for i, pt in enumerate(pts):
            if pt.is_pole:
                # Tiệm cận đứng 2 gạch D
                y_l = _wrap_math(pt.y_left_latex) if pt.y_left_latex else ""
                y_r = _wrap_math(pt.y_right_latex) if pt.y_right_latex else ""
                code_l = "+" if "+" in pt.y_left_latex else "-"
                code_r = "+" if "+" in pt.y_right_latex else "-"
                var_elements.append(f"{code_l}D{code_r}/ {y_l} / {y_r}")
            elif i == 0:
                # Mốc đầu tiên bên trái (-oo hoặc mốc biên)
                # Nếu khoảng đầu tăng (+) -> đi từ dưới lên -> tiền tố '-'
                # Nếu khoảng đầu giảm (-) -> đi từ trên xuống -> tiền tố '+'
                prefix = "-" if (len(intervals) > 0 and intervals[0].sign == "+") else "+"
                var_elements.append(f"{prefix}/ {_wrap_math(pt.y_latex)}")
            elif i == n_pts - 1:
                # Mốc cuối cùng bên phải (+oo hoặc mốc biên)
                # Nếu khoảng cuối tăng (+) -> đi lên đỉnh -> tiền tố '+'
                # Nếu khoảng cuối giảm (-) -> đi xuống đáy -> tiền tố '-'
                prefix = "+" if (len(intervals) > 0 and intervals[-1].sign == "+") else "-"
                var_elements.append(f"{prefix}/ {_wrap_math(pt.y_latex)}")
            else:
                # Điểm mốc ở giữa (Cực trị)
                # Khoảng trước là intervals[i-1], khoảng sau là intervals[i]
                sign_before = intervals[i - 1].sign
                sign_after = intervals[i].sign if i < len(intervals) else ""

                if sign_before == "+" and sign_after == "-":
                    # Tăng rồi giảm -> Điểm CỰC ĐẠI (đỉnh) -> tiền tố '+'
                    prefix = "+"
                elif sign_before == "-" and sign_after == "+":
                    # Giảm rồi tăng -> Điểm CỰC TIỂU (đáy) -> tiền tố '-'
                    prefix = "-"
                else:
                    # Điểm uốn hoặc giữ nguyên chiều: lấy theo chiều đi vào mốc
                    prefix = "+" if sign_before == "+" else "-"

                var_elements.append(f"{prefix}/ {_wrap_math(pt.y_latex)}")

        var_str = " , ".join(var_elements)

        body_lines = [
            "% Bảng biến thiên tạo bởi nvmh-math-py (chuẩn tkz-tab)",
            "\\begin{tikzpicture}",
            f"    \\tkzTabInit[lgt=1.5, espcl=2.5]{{$x$/0.8, $y'$/0.8, $y$/2.0}}{{{x_str}}}",
            f"    \\tkzTabLine{{{signs_str}}}",
            f"    \\tkzTabVar{{{var_str}}}",
            "\\end{tikzpicture}",
        ]
        body = "\n".join(body_lines)

        if standalone:
            return (
                "\\documentclass[border=3pt,tikz]{standalone}\n"
                "\\usepackage{amsmath,amssymb}\n"
                "\\usepackage{tkz-tab}\n"
                "\\begin{document}\n"
                f"{body}\n"
                "\\end{document}\n"
            )
        return body

    except Exception as exc:
        logger.error("Lỗi khi sinh mã tkz-tab: %s", exc)
        return f"% Lỗi tạo tkz-tab: {exc}"


def generate_graph_tikz(
    analysis: Any,
    x_range: Tuple[float, float] = (-6.0, 6.0),
    y_range: Tuple[float, float] = (-6.0, 6.0),
    standalone: bool = True,
) -> str:
    """Sinh mã PGF/TikZ đồ thị Oxy từ Geometric IR."""
    scene = build_geometric_scene(analysis, x_range=x_range, y_range=y_range)
    graph = scene.graph
    x_min, x_max = graph.x_range
    y_min, y_max = graph.y_range

    lines: List[str] = [
        "% Đồ thị khảo sát hàm số sinh bởi nvmh-math-py (Geometric IR)",
        "\\begin{tikzpicture}[>=stealth, scale=1.0]",
        f"    \\clip ({x_min - 0.5:.2f}, {y_min - 0.5:.2f}) rectangle ({x_max + 0.8:.2f}, {y_max + 0.8:.2f});",
        f"    \\draw[step=1.0, gray!25, very thin] ({x_min:.1f}, {y_min:.1f}) grid ({x_max:.1f}, {y_max:.1f});",
        f"    \\draw[->, thick] ({x_min - 0.3:.2f}, 0) -- ({x_max + 0.5:.2f}, 0) node[below] {{$x$}};",
        f"    \\draw[->, thick] (0, {y_min - 0.3:.2f}) -- (0, {y_max + 0.5:.2f}) node[left] {{$y$}};",
        "    \\node[below left] at (0, 0) {$O$};",
    ]

    for xi in range(int(math.ceil(x_min)), int(math.floor(x_max)) + 1):
        if xi != 0:
            lines.append(f"    \\draw ({xi}, 0.06) -- ({xi}, -0.06) node[below, font=\\scriptsize] {{${xi}$}};")
    for yi in range(int(math.ceil(y_min)), int(math.floor(y_max)) + 1):
        if yi != 0:
            lines.append(f"    \\draw (0.06, {yi}) -- (-0.06, {yi}) node[left, font=\\scriptsize] {{${yi}$}};")

    for asy in graph.asymptotes:
        if asy.kind == "vertical":
            lines.append(
                f"    \\draw[red, dashed, thick] ({asy.start.x:.3f}, {asy.start.y:.2f}) -- ({asy.end.x:.3f}, {asy.end.y:.2f})"
                f" node[pos=0.95, right, font=\\scriptsize] {{${asy.latex_label}$}};"
            )
        elif asy.kind == "horizontal":
            lines.append(
                f"    \\draw[red, dashed, thick] ({asy.start.x:.2f}, {asy.start.y:.3f}) -- ({asy.end.x:.2f}, {asy.end.y:.3f})"
                f" node[pos=0.95, above, font=\\scriptsize] {{${asy.latex_label}$}};"
            )
        elif asy.kind == "oblique":
            lines.append(
                f"    \\draw[red, dashed, thick] ({asy.start.x:.2f}, {asy.start.y:.2f}) -- ({asy.end.x:.2f}, {asy.end.y:.2f})"
                f" node[pos=0.85, above, sloped, font=\\scriptsize] {{${asy.latex_label}$}};"
            )

    for gl in graph.guide_lines:
        lines.append(
            f"    \\draw[gray, dotted, thin] ({gl.proj_x.x:.3f}, {gl.proj_x.y:.3f}) -- "
            f"({gl.point.x:.3f}, {gl.point.y:.3f}) -- ({gl.proj_y.x:.3f}, {gl.proj_y.y:.3f});"
        )

    for cp in graph.critical_points:
        lines.append(f"    \\filldraw[black] ({cp.x:.3f}, {cp.y:.3f}) circle (1.5pt);")

    for br in graph.branches:
        if len(br.points) >= 2:
            coord_str = " ".join([f"({p.x:.3f}, {p.y:.3f})" for p in br.points])
            lines.append(f"    \\draw[blue, thick, smooth] plot coordinates {{ {coord_str} }};")

    lines.append("\\end{tikzpicture}")
    body = "\n".join(lines)

    if standalone:
        return (
            "\\documentclass[border=3pt,tikz]{standalone}\n"
            "\\usepackage{amsmath,amssymb}\n"
            "\\begin{document}\n"
            f"{body}\n"
            "\\end{document}\n"
        )
    return body
