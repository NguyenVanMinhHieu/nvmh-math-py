"""Symbolic Mathematical Analysis Engine with Full Asymptote Support."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import List, Optional, Tuple

import sympy as sp
from sympy.calculus.util import continuous_domain, singularities
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TablePoint:
    """Biểu diễn một mốc trên hàng x của bảng biến thiên."""

    x_symbolic: sp.Expr | str
    x_latex: str
    mark: str
    is_pole: bool = False
    y_val: Optional[sp.Expr] = None
    y_latex: str = ""
    y_left_latex: str = ""
    y_right_latex: str = ""


@dataclass(frozen=True)
class AsymptoteInfo:
    """Thông tin về một đường tiệm cận."""

    kind: str  # 'vertical', 'horizontal', 'oblique'
    latex_eqn: str
    params: dict


@dataclass
class FunctionAnalysis:
    """Kết quả phân tích giải tích toàn diện của hàm số."""

    formula_str: str
    expr: sp.Expr
    diff_expr: sp.Expr
    points: List[TablePoint] = field(default_factory=list)
    signs: List[str] = field(default_factory=list)
    poles: List[sp.Expr] = field(default_factory=list)
    asymptotes: List[AsymptoteInfo] = field(default_factory=list)


def parse_math_input(formula_str: str, x_symbol: sp.Symbol) -> sp.Expr:
    clean_str = (
        formula_str.strip()
        .replace("−", "-")
        .replace("^", "**")
        .replace("ln(", "log(")
    )
    transformations = standard_transformations + (
        implicit_multiplication_application,
        convert_xor,
    )
    local_dict = {"x": x_symbol, "e": sp.E, "pi": sp.pi}
    return parse_expr(clean_str, local_dict=local_dict, transformations=transformations)


def analyze_function(formula_str: str) -> FunctionAnalysis:
    x = sp.Symbol("x", real=True)
    expr = parse_math_input(formula_str, x)
    diff_expr = sp.diff(expr, x).simplify()

    # 1. Tập xác định và tiệm cận đứng
    try:
        domain = continuous_domain(expr, x, sp.S.Reals)
    except Exception:
        domain = sp.S.Reals

    try:
        poles_set = singularities(expr, x, sp.S.Reals)
        poles = sorted(list(poles_set), key=lambda p: float(p.evalf()))
    except Exception:
        poles = []

    # 2. Tìm nghiệm đạo hàm f'(x) = 0
    try:
        raw_roots = sp.solve(diff_expr, x)
        stationary_points = []
        for r in raw_roots:
            if isinstance(r, dict):
                r = r.get(x, None)
            if r is not None and r.is_real and r not in poles:
                stationary_points.append(r)
        stationary_points = sorted(
            list(set(stationary_points)), key=lambda r: float(r.evalf())
        )
    except Exception as exc:
        logger.warning("Lỗi giải nghiệm đạo hàm: %s", exc)
        stationary_points = []

    # 3. Biên khảo sát
    left_bound = -sp.oo
    right_bound = sp.oo
    if isinstance(domain, sp.Interval):
        left_bound = domain.start
        right_bound = domain.end
    elif hasattr(domain, "args") and domain.args:
        intervals = [arg for arg in domain.args if isinstance(arg, sp.Interval)]
        if intervals:
            left_bound = min(iv.start for iv in intervals)
            right_bound = max(iv.end for iv in intervals)

    # 4. Tìm kiếm Tiệm cận đứng, ngang, và tiệm cận xiên
    asymptotes: List[AsymptoteInfo] = []

    # Tiệm cận đứng
    for p in poles:
        asymptotes.append(
            AsymptoteInfo(
                kind="vertical",
                latex_eqn=f"x = {sp.latex(p, ln_notation=True)}",
                params={"x0": p},
            )
        )

    # Tiệm cận ngang & Tiệm cận xiên
    for direction in [sp.oo, -sp.oo]:
        try:
            lim_val = sp.limit(expr, x, direction)
            if lim_val.is_real and lim_val.is_finite:
                eqn = f"y = {sp.latex(lim_val, ln_notation=True)}"
                if not any(a.latex_eqn == eqn for a in asymptotes):
                    asymptotes.append(
                        AsymptoteInfo(
                            kind="horizontal",
                            latex_eqn=eqn,
                            params={"y0": lim_val},
                        )
                    )
            elif lim_val in (sp.oo, -sp.oo):
                a_slope = sp.limit(expr / x, x, direction)
                if a_slope.is_real and a_slope.is_finite and a_slope != 0:
                    b_intercept = sp.limit(expr - a_slope * x, x, direction)
                    if b_intercept.is_real and b_intercept.is_finite:
                        slant_line = a_slope * x + b_intercept
                        eqn = f"y = {sp.latex(slant_line, ln_notation=True)}"
                        if not any(a.latex_eqn == eqn for a in asymptotes):
                            asymptotes.append(
                                AsymptoteInfo(
                                    kind="oblique",
                                    latex_eqn=eqn,
                                    params={"a": a_slope, "b": b_intercept},
                                )
                            )
        except Exception:
            pass

    # 5. Lập danh sách mốc trên bảng biến thiên
    finite_nodes: List[Tuple[sp.Expr, bool]] = []
    valid_poles = [p for p in poles if float(p.evalf()) != float(left_bound.evalf()) and float(p.evalf()) != float(right_bound.evalf())]
    valid_stat = [r for r in stationary_points if float(r.evalf()) != float(left_bound.evalf()) and float(r.evalf()) != float(right_bound.evalf())]

    for p in valid_poles:
        finite_nodes.append((p, True))
    for r in valid_stat:
        finite_nodes.append((r, False))

    finite_nodes.sort(key=lambda item: float(item[0].evalf()))

    points: List[TablePoint] = []

    def format_val(val: sp.Expr) -> str:
        if val == sp.oo:
            return "+\\infty"
        if val == -sp.oo:
            return "-\\infty"
        return sp.latex(val, ln_notation=True)

    # Cận trái
    try:
        left_lim = sp.limit(expr, x, left_bound, dir="+")
    except Exception:
        left_lim = expr.subs(x, left_bound)
    points.append(
        TablePoint(
            x_symbolic=left_bound,
            x_latex="-\\infty" if left_bound == -sp.oo else sp.latex(left_bound, ln_notation=True),
            mark="",
            is_pole=False,
            y_latex=format_val(left_lim),
        )
    )

    # Các mốc giữa
    for node, is_pole in finite_nodes:
        node_latex = sp.latex(node, ln_notation=True)
        if is_pole:
            try:
                y_left = sp.limit(expr, x, node, dir="-")
            except Exception:
                y_left = -sp.oo
            try:
                y_right = sp.limit(expr, x, node, dir="+")
            except Exception:
                y_right = sp.oo
            points.append(
                TablePoint(
                    x_symbolic=node,
                    x_latex=node_latex,
                    mark="||",
                    is_pole=True,
                    y_left_latex=format_val(y_left),
                    y_right_latex=format_val(y_right),
                )
            )
        else:
            y_val = expr.subs(x, node).simplify()
            points.append(
                TablePoint(
                    x_symbolic=node,
                    x_latex=node_latex,
                    mark="0",
                    is_pole=False,
                    y_val=y_val,
                    y_latex=format_val(y_val),
                )
            )

    # Cận phải
    try:
        right_lim = sp.limit(expr, x, right_bound, dir="-")
    except Exception:
        right_lim = expr.subs(x, right_bound)
    points.append(
        TablePoint(
            x_symbolic=right_bound,
            x_latex="+\\infty" if right_bound == sp.oo else sp.latex(right_bound, ln_notation=True),
            mark="",
            is_pole=False,
            y_latex=format_val(right_lim),
        )
    )

    # 6. Dấu đạo hàm
    signs: List[str] = []
    for i in range(len(points) - 1):
        x_left = points[i].x_symbolic
        x_right = points[i + 1].x_symbolic

        if x_left == -sp.oo and x_right == sp.oo:
            test_x = 0.0
        elif x_left == -sp.oo:
            test_x = float(x_right.evalf()) - 1.0
        elif x_right == sp.oo:
            test_x = float(x_left.evalf()) + 1.0
        else:
            test_x = (float(x_left.evalf()) + float(x_right.evalf())) / 2.0

        try:
            val_diff = float(diff_expr.subs(x, test_x).evalf())
            signs.append("+" if val_diff > 0 else "-")
        except Exception:
            signs.append("+")

    return FunctionAnalysis(
        formula_str=formula_str,
        expr=expr,
        diff_expr=diff_expr,
        points=points,
        signs=signs,
        poles=poles,
        asymptotes=asymptotes,
    )
