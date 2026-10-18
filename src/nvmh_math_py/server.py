"""FastAPI Web Application for NVMH MATH-ARCH (SymPy + TikZ + Typst/CeTZ)."""

from __future__ import annotations
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from pathlib import Path
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import sympy as sp

from nvmh_math_py.analyzer import analyze_function
from nvmh_math_py.tikz import generate_tkz_tab, generate_graph_tikz
from nvmh_math_py.typst import generate_typst_document
from nvmh_math_py.svg import generate_graph_svg, generate_table_svg
from nvmh_math_py.geometry_ir import build_geometric_scene

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nvmh-arch_math_server")

app = FastAPI(title="NVMH MATH-ARCH", version="1.2.0")


class AnalyzeRequest(BaseModel):
    formula: str
    x_min: Optional[float] = None
    x_max: Optional[float] = None
    y_min: Optional[float] = None
    y_max: Optional[float] = None


class AnalyzeResponse(BaseModel):
    success: bool
    formula: str
    expr_latex: str
    diff_latex: str
    tikz_tab: str
    tikz_tab_body: str
    tikz_graph: str
    tikz_graph_body: str
    typst_doc: str
    graph_svg: str = ""
    table_svg: str = ""
    message: Optional[str] = None


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def api_analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    formula = req.formula.strip()
    if not formula:
        raise HTTPException(status_code=400, detail="Công thức không được để trống.")

    try:
        analysis = analyze_function(formula)
        tab_full = generate_tkz_tab(analysis, standalone=True)
        tab_body = generate_tkz_tab(analysis, standalone=False)
        graph_full = generate_graph_tikz(analysis, standalone=True)
        graph_body = generate_graph_tikz(analysis, standalone=False)
        typst_code = generate_typst_document(analysis)
        x_range = (req.x_min, req.x_max) if req.x_min is not None and req.x_max is not None else (-6.0, 6.0)
        y_range = (req.y_min, req.y_max) if req.y_min is not None and req.y_max is not None else (-6.0, 6.0)
        scene = build_geometric_scene(analysis, x_range=x_range, y_range=y_range)
        g_svg = generate_graph_svg(scene)
        t_svg = generate_table_svg(scene)

        return AnalyzeResponse(
            success=True,
            formula=formula,
            expr_latex=sp.latex(analysis.expr, ln_notation=True),
            diff_latex=sp.latex(analysis.diff_expr, ln_notation=True),
            tikz_tab=tab_full,
            tikz_tab_body=tab_body,
            tikz_graph=graph_full,
            tikz_graph_body=graph_body,
            typst_doc=typst_code,
            graph_svg=g_svg,
            table_svg=t_svg,
        )
    except Exception as exc:
        logger.error("Lỗi khi khảo sát hàm '%s': %s", formula, exc)
        return AnalyzeResponse(
            success=False,
            formula=formula,
            expr_latex="",
            diff_latex="",
            tikz_tab="",
            tikz_tab_body="",
            tikz_graph="",
            tikz_graph_body="",
            typst_doc="",
            message=f"Lỗi khảo sát: {str(exc)}",
        )


INDEX_HTML_PATH = Path(__file__).parent / "index.html"

@app.get("/", response_class=FileResponse)
async def serve_index() -> FileResponse:
    if not INDEX_HTML_PATH.is_file():
        raise HTTPException(status_code=404, detail="File index.html không tồn tại.")
    return FileResponse(INDEX_HTML_PATH, media_type="text/html")


def main():
    """Hàm khởi chạy máy chủ tự động chọn cổng hoặc nhận từ môi trường Cloud."""
    import os
    import socket
    import uvicorn

    env_port = os.environ.get("PORT")
    if env_port:
        port = int(env_port)
        host = "0.0.0.0"
    else:
        host = "0.0.0.0"
        port = 8888
        while port < 65535:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("127.0.0.1", port)) != 0:
                    break
                port += 1

    print("\n" + "=" * 50)
    print(f"🚀 MÁY CHỦ SẴN SÀNG TẠI: http://{host}:{port}")
    print("=" * 50 + "\n")
    uvicorn.run("nvmh_math_py.server:app", host=host, port=port)


if __name__ == "__main__":
    main()
