"""Bộ kiểm thử đơn vị cho Geometric IR và các Backend Renderer."""

import pytest
from nvmh_math_py.analyzer import analyze_function
from nvmh_math_py.geometry_ir import build_geometric_scene
from nvmh_math_py.tikz import generate_graph_tikz, generate_tkz_tab
from nvmh_math_py.typst import generate_typst_document


@pytest.mark.parametrize(
    "formula, has_oblique, has_vert, has_horiz, min_branches",
    [
        ("x^3 - 3*x", False, False, False, 1),
        ("x^4 - 2*x^2", False, False, False, 1),
        ("(2*x - 1)/(x + 1)", False, True, True, 2),
        ("(x^2 + 2*x - 3)/(x + 1)", True, True, False, 2),
    ],
)
def test_geometric_scene_generation(
    formula: str,
    has_oblique: bool,
    has_vert: bool,
    has_horiz: bool,
    min_branches: int,
) -> None:
    """Kiểm tra việc trích xuất và tính toán các thực thể hình học trong Scene IR."""
    ana = analyze_function(formula)
    scene = build_geometric_scene(ana, x_range=(-6.0, 6.0), y_range=(-6.0, 6.0))

    # 1. Kiểm tra số nhánh đồ thị sau Hard-Clamping
    assert len(scene.graph.branches) >= min_branches
    for br in scene.graph.branches:
        assert len(br.points) >= 2
        for pt in br.points:
            assert -11.0 <= pt.y <= 11.0  # Nằm trong biên an toàn margin

    # 2. Kiểm tra tiệm cận
    kinds = [asy.kind for asy in scene.graph.asymptotes]
    assert ("vertical" in kinds) == has_vert
    assert ("horizontal" in kinds) == has_horiz
    assert ("oblique" in kinds) == has_oblique

    # 3. Kiểm tra bảng biến thiên IR
    assert len(scene.table.points) >= 2
    assert len(scene.table.intervals) == len(scene.table.points) - 1


def test_tikz_renderer_validity() -> None:
    """Kiểm tra sinh mã LaTeX / TikZ."""
    ana = analyze_function("(x^2 + 2*x - 3)/(x + 1)")
    tkz_tab = generate_tkz_tab(ana)
    tikz_graph = generate_graph_tikz(ana)

    assert "\\begin{tikzpicture}" in tkz_tab
    assert "\\tkzTabInit" in tkz_tab
    assert "\\tkzTabLine" in tkz_tab
    assert "\\tkzTabVar" in tkz_tab

    assert "\\begin{tikzpicture}" in tikz_graph
    assert "plot coordinates" in tikz_graph
    assert "\\clip" in tikz_graph


def test_typst_renderer_validity() -> None:
    """Kiểm tra sinh mã Typst / CeTZ."""
    ana = analyze_function("x^3 - 3*x")
    typst_doc = generate_typst_document(ana)

    assert "#table(" in typst_doc
    assert "@preview/cetz:0.5.2" in typst_doc
    assert "cetz.canvas(" in typst_doc
    assert "arrow.tr" in typst_doc or "arrow.br" in typst_doc
