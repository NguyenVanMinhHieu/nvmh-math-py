"""Geometric Intermediate Representation (IR) Engine for nvmh-math-py.

Chịu trách nhiệm tính toán hình học độc lập với renderer (TikZ/Typst):
- Lấy mẫu toạ độ các nhánh đường cong với thuật toán Hard-Clamping.
- Tính toán toạ độ đoạn thẳng biên của các đường tiệm cận đứng, ngang, xiên.
- Tính toán điểm cực trị và đường gióng vuông góc tới hai trục.
- Chuẩn hoá cấu trúc Bảng biến thiên động chuẩn sư phạm THPT.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, List, Optional, Sequence, Tuple

import sympy as sp

logger = logging.getLogger(__name__)


class LineStyle(Enum):
    """Kiểu đường nét chuẩn hoá."""
    SOLID = auto()
    DASHED = auto()
    DOTTED = auto()


@dataclass(slots=True)
class Point2D:
    """Toạ độ 2D thực trên hệ Oxy."""
    x: float
    y: float
    label: Optional[str] = None


@dataclass(slots=True)
class CurveBranchIR:
    """Một nhánh đồ thị liên tục đã lấy mẫu và Hard-Clamping."""
    points: List[Point2D]
    color: str = "blue"
    stroke_width: float = 1.2


@dataclass(slots=True)
class AsymptoteIR:
    """Đường tiệm cận được tính sẵn toạ độ 2 điểm mút cắt biên."""
    kind: str  # 'vertical', 'horizontal', 'oblique'
    start: Point2D
    end: Point2D
    label_pos: Point2D
    latex_label: str
    typst_label: str
    style: LineStyle = LineStyle.DASHED
    color: str = "red"


@dataclass(slots=True)
class GuideLineIR:
    """Đường gióng vuông góc từ điểm cực trị tới các trục Ox, Oy."""
    point: Point2D
    proj_x: Point2D
    proj_y: Point2D
    style: LineStyle = LineStyle.DOTTED


@dataclass(slots=True)
class VariationIntervalIR:
    """Mô hình hoá một khoảng biến thiên giữa hai mốc liên tiếp."""
    sign: str  # '+', '-'
    arrow_direction: str  # 'up', 'down'
    y_start_latex: str
    y_start_typst: str
    y_end_latex: str
    y_end_typst: str


@dataclass(slots=True)
class TablePointIR:
    """Mô hình hoá một điểm mốc trên Bảng biến thiên."""
    x_latex: str
    x_typst: str
    derivative_mark: str  # '0', '||', 't'
    is_pole: bool = False
    is_after_pole: bool = False
    y_latex: str = ""
    y_typst: str = ""
    y_left_latex: str = ""
    y_left_typst: str = ""
    y_right_latex: str = ""
    y_right_typst: str = ""


@dataclass(slots=True)
class VariationTableIR:
    """Bảng biến thiên trung gian chuẩn sư phạm."""
    points: List[TablePointIR]
    intervals: List[VariationIntervalIR]


@dataclass(slots=True)
class FunctionGraphIR:
    """Mô hình hình học phẳng Oxy hoàn chỉnh."""
    x_range: Tuple[float, float]
    y_range: Tuple[float, float]
    branches: List[CurveBranchIR] = field(default_factory=list)
    asymptotes: List[AsymptoteIR] = field(default_factory=list)
    critical_points: List[Point2D] = field(default_factory=list)
    guide_lines: List[GuideLineIR] = field(default_factory=list)


@dataclass(slots=True)
class GeometricSceneIR:
    """IR trung gian thống nhất bao trùm cả Đồ thị và Bảng biến thiên."""
    graph: FunctionGraphIR
    table: VariationTableIR
    formula_latex: str
    formula_typst: str
    diff_formula_latex: str
    diff_formula_typst: str


def _to_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        try:
            return float(sp.sympify(val).evalf())
        except Exception:
            return None


def sympy_to_typst_math(expr: Any) -> str:
    """Chuyển đổi biểu thức SymPy sang cú pháp toán Typst."""
    if expr is None:
        return ""
    if isinstance(expr, str):
        s = expr.strip()
    else:
        s = sp.printing.sstr(expr)
    
    s = s.replace("**", "^")
    s = s.replace("oo", "infinity")
    s = s.replace("*", " ")
    s = re.sub(r"\bexp\((.*?)\)", r"e^(\1)", s)
    s = re.sub(r"\blog\((.*?)\)", r"ln(\1)", s)
    s = re.sub(r"\bsqrt\((.*?)\)", r"sqrt(\1)", s)
    return s


def latex_to_typst_math(tex_str: str) -> str:
    """Chuyển chuỗi LaTeX ngắn (như giới hạn, mốc) sang Typst math."""
    if not tex_str:
        return ""
    t = tex_str.strip().replace("$", "")
    t = t.replace(r"\infty", "infinity")
    t = t.replace(r"+\infty", "+infinity")
    t = t.replace(r"-\infty", "-infinity")
    t = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1) / (\2)", t)
    t = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", t)
    t = t.replace(r"\ln", "ln")
    t = t.replace(r"\exp", "exp")
    t = t.replace(r"\{", "").replace(r"\}", "")
    return t


def clip_line_to_bbox(
    a: float, b: float, x_min: float, x_max: float, y_min: float, y_max: float
) -> Optional[Tuple[Point2D, Point2D]]:
    """Cắt đường thẳng y = ax + b vào hình chữ nhật [x_min, x_max] x [y_min, y_max]."""
    pts: List[Tuple[float, float]] = []

    # Giao với x = x_min
    y1 = a * x_min + b
    if y_min <= y1 <= y_max:
        pts.append((x_min, y1))

    # Giao với x = x_max
    y2 = a * x_max + b
    if y_min <= y2 <= y_max:
        pts.append((x_max, y2))

    # Giao với y = y_min
    if abs(a) > 1e-9:
        x3 = (y_min - b) / a
        if x_min <= x3 <= x_max and not any(abs(x3 - p[0]) < 1e-4 and abs(y_min - p[1]) < 1e-4 for p in pts):
            pts.append((x3, y_min))

    # Giao với y = y_max
    if abs(a) > 1e-9:
        x4 = (y_max - b) / a
        if x_min <= x4 <= x_max and not any(abs(x4 - p[0]) < 1e-4 and abs(y_max - p[1]) < 1e-4 for p in pts):
            pts.append((x4, y_max))

    if len(pts) >= 2:
        pts.sort(key=lambda p: p[0])
        return (
            Point2D(round(pts[0][0], 3), round(pts[0][1], 3)),
            Point2D(round(pts[-1][0], 3), round(pts[-1][1], 3)),
        )
    return None


def sample_curve_branches(
    expr: sp.Expr,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    poles: Sequence[float],
    num_samples_per_seg: int = 160,
    margin_ratio: float = 0.4,
) -> List[CurveBranchIR]:
    """Tính các điểm toạ độ với Hard-Clamping chống tràn vô cùng."""
    x = sp.Symbol("x")
    f_num = sp.lambdify(x, expr, modules=["math", {"zoo": math.nan, "oo": math.inf}])

    y_lower = y_min - margin_ratio * (y_max - y_min)
    y_upper = y_max + margin_ratio * (y_max - y_min)

    valid_poles = sorted([p for p in poles if (x_min - 0.2) <= p <= (x_max + 0.2)])
    eps = 0.04

    cuts = [x_min]
    for p in valid_poles:
        cuts.extend([p - eps, p + eps])
    cuts.append(x_max)

    branch_list: List[CurveBranchIR] = []

    for i in range(0, len(cuts) - 1, 2):
        seg_a = cuts[i]
        seg_b = cuts[i + 1]
        if seg_b <= seg_a:
            continue

        curr_pts: List[Point2D] = []
        step = (seg_b - seg_a) / num_samples_per_seg
        for s_idx in range(num_samples_per_seg + 1):
            xi = seg_a + s_idx * step
            try:
                yi = float(f_num(xi))
                if math.isfinite(yi) and (y_lower <= yi <= y_upper):
                    curr_pts.append(Point2D(round(xi, 3), round(yi, 3)))
                else:
                    if len(curr_pts) >= 2:
                        branch_list.append(CurveBranchIR(points=curr_pts))
                    curr_pts = []
            except Exception:
                if len(curr_pts) >= 2:
                    branch_list.append(CurveBranchIR(points=curr_pts))
                curr_pts = []

        if len(curr_pts) >= 2:
            branch_list.append(CurveBranchIR(points=curr_pts))

    return branch_list


def build_geometric_scene(
    analysis: Any,
    x_range: Tuple[float, float] = (-6.0, 6.0),
    y_range: Tuple[float, float] = (-6.0, 6.0),
) -> GeometricSceneIR:
    """Xây dựng mô hình hình học phẳng và bảng biến thiên trung gian độc lập."""
    expr = getattr(analysis, "expr", None)
    diff_expr = getattr(analysis, "diff_expr", None)
    if expr is None:
        raise ValueError("Thiếu biểu thức hàm số 'expr' trong FunctionAnalysis.")

    # --- SYMMETRIC 2D ADAPTIVE VIEWPORT (THẦY NGUYỄN VĂN MINH HIẾU) ---
    raw_asymptotes = getattr(analysis, 'asymptotes', [])
    extrema_list = getattr(analysis, 'extrema', [])
    inflection_list = getattr(analysis, 'inflection_points', [])

    xs = [0.0]
    ys = [0.0]

    # Giao điểm trục tung (0, f(0))
    try:
        y0_val = _to_float(expr.subs(sp.Symbol('x'), 0))
        if y0_val is not None and abs(y0_val) < 1000:
            ys.append(y0_val)
    except Exception:
        pass

    vert_poles_list = []
    horiz_lines_list = []
    oblique_lines_list = []

    for item in raw_asymptotes:
        k = getattr(item, 'kind', '')
        p = getattr(item, 'params', {})
        if k == 'vertical':
            v = _to_float(p.get('x0', p.get('x')))
            if v is not None:
                vert_poles_list.append(v)
                xs.append(v)
        elif k == 'horizontal':
            h = _to_float(p.get('y0', p.get('y')))
            if h is not None:
                horiz_lines_list.append(h)
                ys.append(h)
        elif k == 'oblique':
            a = _to_float(p.get('a', 1.0))
            b = _to_float(p.get('b', 0.0))
            if a is not None and b is not None:
                oblique_lines_list.append((a, b))

    for ext in extrema_list:
        xv = _to_float(getattr(ext, 'x', None))
        yv = _to_float(getattr(ext, 'y', None))
        if xv is not None: xs.append(xv)
        if yv is not None: ys.append(yv)

    for ip in inflection_list:
        xv = _to_float(getattr(ip, 'x', None))
        yv = _to_float(getattr(ip, 'y', None))
        if xv is not None: xs.append(xv)
        if yv is not None: ys.append(yv)

    # XÁC ĐỊNH TÂM ĐỐI XỨNG HÌNH HỌC I(cx, cy)
    cx, cy = 0.0, 0.0
    has_center = False

    if vert_poles_list:
        cx = vert_poles_list[0]
        has_center = True
        if horiz_lines_list:
            cy = horiz_lines_list[0]
        elif oblique_lines_list:
            a, b = oblique_lines_list[0]
            cy = a * cx + b
        else:
            cy = sum(ys) / len(ys) if ys else 0.0
    elif inflection_list:
        xv = _to_float(getattr(inflection_list[0], 'x', None))
        yv = _to_float(getattr(inflection_list[0], 'y', None))
        if xv is not None and yv is not None:
            cx, cy = xv, yv
            has_center = True

    if not has_center:
        cx = (min(xs) + max(xs)) / 2.0
        cy = (min(ys) + max(ys)) / 2.0

    max_dx = max([abs(x - cx) for x in xs] + [5.0])
    rx = max(max_dx * 1.5, 6.0)

    req_ry = [abs(y - cy) for y in ys] + [4.0]
    if oblique_lines_list:
        a, b = oblique_lines_list[0]
        req_ry.append(abs(a) * rx + 3.0)

    max_dy = max(req_ry)
    ry = max_dy * 1.25

    if x_range == (-6.0, 6.0):
        x_min = round(cx - rx)
        x_max = round(cx + rx)
        if x_min >= x_max or (x_max - x_min) < 6.0:
            x_min, x_max = -6.0, 6.0
    else:
        x_min, x_max = float(x_range[0]), float(x_range[1])

    if y_range == (-6.0, 6.0):
        y_min = round(cy - ry)
        y_max = round(cy + ry)
        if y_min >= y_max or (y_max - y_min) < 5.0:
            y_min, y_max = -6.0, 6.0
    else:
        y_min, y_max = float(y_range[0]), float(y_range[1])
    # 1. Trích xuất tiệm cận và cực điểm
    raw_asymptotes = getattr(analysis, "asymptotes", [])
    vert_poles: List[float] = []
    horiz_lines: List[float] = []
    oblique_lines: List[Tuple[float, float]] = []

    for item in raw_asymptotes:
        kind = getattr(item, "kind", "")
        params = getattr(item, "params", {})
        if kind == "vertical":
            v = _to_float(params.get("x0", params.get("x")))
            if v is not None and v not in vert_poles:
                vert_poles.append(v)
        elif kind == "horizontal":
            v = _to_float(params.get("y0", params.get("y")))
            if v is not None and v not in horiz_lines:
                horiz_lines.append(v)
        elif kind == "oblique":
            a = _to_float(params.get("a"))
            b = _to_float(params.get("b"))
            if a is not None and b is not None:
                oblique_lines.append((a, b))

    for p in getattr(analysis, "poles", []):
        pf = _to_float(p)
        if pf is not None and pf not in vert_poles:
            vert_poles.append(pf)

    # 2. Xây dựng danh sách AsymptoteIR
    asymptotes_ir: List[AsymptoteIR] = []
    for vp in vert_poles:
        if x_min <= vp <= x_max:
            asymptotes_ir.append(
                AsymptoteIR(
                    kind="vertical",
                    start=Point2D(round(vp, 3), y_min - 0.2),
                    end=Point2D(round(vp, 3), y_max + 0.2),
                    label_pos=Point2D(round(vp, 3), y_max - 0.5),
                    latex_label=f"x = {vp:g}",
                    typst_label=f"x = {vp:g}",
                )
            )

    for hy in horiz_lines:
        if y_min <= hy <= y_max:
            asymptotes_ir.append(
                AsymptoteIR(
                    kind="horizontal",
                    start=Point2D(x_min - 0.2, round(hy, 3)),
                    end=Point2D(x_max + 0.2, round(hy, 3)),
                    label_pos=Point2D(x_max - 1.2, round(hy, 3) + 0.3),
                    latex_label=f"y = {hy:g}",
                    typst_label=f"y = {hy:g}",
                )
            )

    for a_val, b_val in oblique_lines:
        seg = clip_line_to_bbox(a_val, b_val, x_min - 0.2, x_max + 0.2, y_min - 0.2, y_max + 0.2)
        if seg is not None:
            a_str = f"{a_val:g}" if abs(a_val) != 1 else ("" if a_val == 1 else "-")
            b_str = f"+ {b_val:g}" if b_val >= 0 else f"- {abs(b_val):g}"
            eqn_str = f"y = {a_str}x {b_str}".replace("  ", " ")
            asymptotes_ir.append(
                AsymptoteIR(
                    kind="oblique",
                    start=seg[0],
                    end=seg[1],
                    label_pos=Point2D((seg[0].x + seg[1].x) / 2, (seg[0].y + seg[1].y) / 2 + 0.3),
                    latex_label=eqn_str,
                    typst_label=eqn_str,
                )
            )

    # 3. Lấy mẫu các nhánh đường cong f(x)
    branches_ir = sample_curve_branches(expr, x_min, x_max, y_min, y_max, vert_poles)

    # 4. Cực trị và đường gióng
    crit_points_ir: List[Point2D] = []
    guide_lines_ir: List[GuideLineIR] = []

    for pt in getattr(analysis, "points", []):
        if not pt.is_pole and pt.mark == "0":
            px = _to_float(pt.x_symbolic)
            py = _to_float(pt.y_val)
            if px is not None and py is not None:
                if (x_min <= px <= x_max) and (y_min <= py <= y_max):
                    p2d = Point2D(round(px, 3), round(py, 3))
                    crit_points_ir.append(p2d)
                    guide_lines_ir.append(
                        GuideLineIR(
                            point=p2d,
                            proj_x=Point2D(round(px, 3), 0.0),
                            proj_y=Point2D(0.0, round(py, 3)),
                        )
                    )

    graph_ir = FunctionGraphIR(
        x_range=(x_min, x_max),
        y_range=(y_min, y_max),
        branches=branches_ir,
        asymptotes=asymptotes_ir,
        critical_points=crit_points_ir,
        guide_lines=guide_lines_ir,
    )

    # 5. Xây dựng Bảng biến thiên IR
    raw_points = list(getattr(analysis, "points", []))
    # Sắp xếp các mốc x theo thứ tự số thực tăng dần để đảm bảo chuẩn sư phạm
    def _get_x_val(p):
        if hasattr(p, "x_symbolic") and p.x_symbolic is not None:
            val = _to_float(p.x_symbolic)
            if val is not None:
                return val
        return 0.0

    raw_points.sort(key=_get_x_val)
    raw_signs = getattr(analysis, "signs", [])

    points_ir: List[TablePointIR] = []
    for pt in raw_points:
        points_ir.append(
            TablePointIR(
                x_latex=pt.x_latex,
                x_typst=latex_to_typst_math(pt.x_latex),
                derivative_mark="||" if pt.is_pole else ("0" if pt.mark == "0" else "t"),
                is_pole=pt.is_pole,
                y_latex=pt.y_latex,
                y_typst=latex_to_typst_math(pt.y_latex),
                y_left_latex=pt.y_left_latex,
                y_left_typst=latex_to_typst_math(pt.y_left_latex),
                y_right_latex=pt.y_right_latex,
                y_right_typst=latex_to_typst_math(pt.y_right_latex),
            )
        )

    intervals_ir: List[VariationIntervalIR] = []
    for i, s in enumerate(raw_signs):
        # Xác định chiều mũi tên chuẩn: nếu dấu y' là '+' thì tăng (up), '-' thì giảm (down)
        arr = "up" if s == "+" else "down"
        pt_left = points_ir[i]
        pt_right = points_ir[i + 1] if i + 1 < len(points_ir) else None

        y_start_tex = pt_left.y_right_latex if pt_left.is_pole else pt_left.y_latex
        y_start_typ = pt_left.y_right_typst if pt_left.is_pole else pt_left.y_typst

        y_end_tex = pt_right.y_left_latex if (pt_right and pt_right.is_pole) else (pt_right.y_latex if pt_right else "")
        y_end_typ = pt_right.y_left_typst if (pt_right and pt_right.is_pole) else (pt_right.y_typst if pt_right else "")

        intervals_ir.append(
            VariationIntervalIR(
                sign=s,
                arrow_direction=arr,
                y_start_latex=y_start_tex,
                y_start_typst=y_start_typ,
                y_end_latex=y_end_tex,
                y_end_typst=y_end_typ,
            )
        )

    table_ir = VariationTableIR(points=points_ir, intervals=intervals_ir)

    return GeometricSceneIR(
        graph=graph_ir,
        table=table_ir,
        formula_latex=sp.latex(expr),
        formula_typst=sympy_to_typst_math(expr),
        diff_formula_latex=sp.latex(diff_expr) if diff_expr is not None else "",
        diff_formula_typst=sympy_to_typst_math(diff_expr) if diff_expr is not None else "",
    )

def get_table_prefix(i: int, is_after_pole: bool, intervals: List[VariationIntervalIR]) -> str:
    """Xác định tiền tố chuẩn tkz-tab/typst dựa vào chiều biến thiên."""
    if is_after_pole and i < len(intervals):
        return "+" if intervals[i].sign == "+" else "-"
    if i > 0:
        return "+" if intervals[i-1].sign == "+" else "-"
    return "+" if (len(intervals) > 0 and intervals[0].sign == "+") else "-"
