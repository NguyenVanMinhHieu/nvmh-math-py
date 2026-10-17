"""FastAPI Web Application for NVMH MATH-ARCH (SymPy + TikZ + Typst/CeTZ)."""

from __future__ import annotations
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sympy as sp

from nvmh_math_py.analyzer import analyze_function
from nvmh_math_py.tikz import generate_tkz_tab, generate_graph_tikz
from nvmh_math_py.typst import generate_typst_document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nvmh-arch_math_server")

app = FastAPI(title="NVMH MATH-ARCH", version="1.2.0")


class AnalyzeRequest(BaseModel):
    formula: str


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


HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NVMH MATH-ARCH · SymPy CAS & Typst/TikZ Studio</title>
  <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
  <style>
    :root {
      --bg: #0f172a;
      --card: #1e293b;
      --border: #334155;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #10b981;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }
    body { background-color: var(--bg); color: var(--text); padding: 24px; min-height: 100vh; }
    .container { max-width: 1360px; margin: 0 auto; }
    header { margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 16px; }
    header h1 { font-size: 1.5rem; color: #60a5fa; display: flex; align-items: center; gap: 8px; }
    .badge { background: #1e3a8a; color: #93c5fd; padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
    
    .grid { display: grid; grid-template-columns: 1fr 1.15fr; gap: 24px; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
    
    .card { min-width: 0; background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); }
    .card h2 { font-size: 1.1rem; margin-bottom: 16px; color: #cbd5e1; display: flex; justify-content: space-between; align-items: center; }
    
    label { display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 6px; }
    .input-row { display: flex; gap: 8px; margin-bottom: 16px; }
    input[type="text"] { flex: 1; background: #0f172a; border: 1px solid var(--border); color: #fff; padding: 10px 14px; border-radius: 8px; font-size: 1.05rem; outline: none; }
    input[type="text"]:focus { border-color: var(--primary); }
    
    button { cursor: pointer; border: none; border-radius: 8px; padding: 10px 18px; font-weight: 600; transition: all 0.2s; }
    button.primary { background: var(--primary); color: #fff; }
    button.primary:hover { background: var(--primary-hover); }
    
    .presets { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 20px; }
    .preset-btn { background: #1e293b; border: 1px solid var(--border); color: #94a3b8; font-size: 0.8rem; padding: 6px 11px; border-radius: 6px; }
    .preset-btn:hover { background: #334155; color: #fff; }
    
    .math-preview { background: #0f172a; border: 1px solid var(--border); border-radius: 8px; padding: 16px; min-height: 100px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 16px; }
    .diff-info { margin-top: 10px; border-top: 1px dashed var(--border); padding-top: 10px; }
    
    /* Tabs chuyển đổi giữa BBT, Đồ thị và Typst */
    .tab-bar { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; border-bottom: 1px solid var(--border); padding-bottom: 8px; justify-content: space-between; align-items: center; }
    .tab-buttons { display: flex; flex-wrap: wrap; gap: 6px; }
    .tab-btn { background: transparent; color: var(--text-muted); padding: 8px 12px; font-size: 0.85rem; border-radius: 6px; }
    .tab-btn.active { background: var(--primary); color: #fff; }
    
    .action-group { display: flex; gap: 6px; }
    button.copy-btn { background: #334155; color: #f1f5f9; font-size: 0.8rem; padding: 6px 12px; border-radius: 6px; }
    button.copy-btn:hover { background: #475569; }
    
    pre { background: #090d16; border: 1px solid var(--border); border-radius: 8px; padding: 14px; color: #a5b4fc; font-family: 'Fira Code', 'Cascadia Code', monospace; font-size: 0.85rem; overflow-x: auto; height: 420px; }
    
    .toast { position: fixed; bottom: 20px; right: 20px; background: var(--accent); color: #fff; padding: 10px 18px; border-radius: 8px; font-weight: 600; opacity: 0; transform: translateY(10px); transition: all 0.3s; pointer-events: none; }
    .toast.show { opacity: 1; transform: translateY(0); }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>NVMH MATH-ARCH <span class="badge">SymPy CAS + TikZ + Typst</span></h1>
      <span style="color: var(--text-muted); font-size: 0.85rem;">Khảo sát tự động & Xuất bản chuyên nghiệp</span>
    </header>

    <div class="grid">
      <!-- Cột trái: Nhập liệu và Phân tích Giải tích -->
      <div class="card">
        <h2>Nhập hàm số khảo sát</h2>
        <label for="formula">Công thức f(x)</label>
        <div class="input-row">
          <input type="text" id="formula" value="(x^2 + 2*x - 3)/(x + 1)" placeholder="Nhập hàm số, ví dụ: x^3 - 3*x">
          <button class="primary" id="btn-analyze">Khảo sát</button>
        </div>

        <label>Các hàm mẫu quen thuộc:</label>
        <div class="presets">
          <button class="preset-btn" data-val="x^4 - 4*x^2 - 1">Trùng phương</button>
          <button class="preset-btn" data-val="x^3 - 3*x">Bậc 3</button>
          <button class="preset-btn" data-val="(2*x - 1)/(x + 1)">Phân thức 1/1</button>
          <button class="preset-btn" data-val="(x^2 + 2*x - 3)/(x + 1)">Phân thức 2/1</button>
          <button class="preset-btn" data-val="ln(x)/x^2">y = ln(x)/x^2</button>
          <button class="preset-btn" data-val="x*exp(-x)">y = x·e⁻ˣ</button>
          <button class="preset-btn" data-val="sqrt(x^2 + 1)">Căn thức</button>
        </div>

        <h2>Kết quả giải tích biểu tượng</h2>
        <div class="math-preview">
          <div id="render-f">$$ y = \dots $$</div>
          <div class="diff-info" id="render-df">$$ y' = \dots $$</div>
        </div>
      </div>

      <!-- Cột phải: Mã nguồn xuất bản với 3 Tab -->
      <div class="card">
        <div class="tab-bar">
          <div class="tab-buttons">
            <button class="tab-btn active" id="tab-bbt">📊 tkz-tab</button>
            <button class="tab-btn" id="tab-graph">📈 TikZ Oxy</button>
            <button class="tab-btn" id="tab-typst">📄 Typst (.typ)</button>
          </div>
          <div class="action-group">
            <button class="copy-btn" id="btn-copy">📋 Sao chép</button>
            <button class="copy-btn" id="btn-download">💾 Tải file</button>
          </div>
        </div>
        <pre><code id="tikz-output">Đang khởi tạo...</code></pre>
      </div>
    </div>
  </div>

  <div id="toast" class="toast">Đã thực hiện xong!</div>

  <script>
    const $ = id => document.getElementById(id);
    const toast = msg => {
      const t = $('toast');
      t.textContent = msg;
      t.classList.add('show');
      setTimeout(() => t.classList.remove('show'), 2500);
    };

    let activeTab = 'bbt'; // 'bbt', 'graph', hoặc 'typst'
    let currentData = null;

    function renderActiveTab() {
      if (!currentData || !currentData.success) return;
      if (activeTab === 'bbt') {
        $('tikz-output').textContent = currentData.tikz_tab;
      } else if (activeTab === 'graph') {
        $('tikz-output').textContent = currentData.tikz_graph;
      } else {
        $('tikz-output').textContent = currentData.typst_doc;
      }
    }

    $('tab-bbt').onclick = () => {
      activeTab = 'bbt';
      $('tab-bbt').classList.add('active');
      $('tab-graph').classList.remove('active');
      $('tab-typst').classList.remove('active');
      renderActiveTab();
    };

    $('tab-graph').onclick = () => {
      activeTab = 'graph';
      $('tab-graph').classList.add('active');
      $('tab-bbt').classList.remove('active');
      $('tab-typst').classList.remove('active');
      renderActiveTab();
    };

    $('tab-typst').onclick = () => {
      activeTab = 'typst';
      $('tab-typst').classList.add('active');
      $('tab-bbt').classList.remove('active');
      $('tab-graph').classList.remove('active');
      renderActiveTab();
    };

    async function analyze() {
      const formula = $('formula').value.trim();
      if (!formula) return;

      $('tikz-output').textContent = 'SymPy CAS đang phân tích giải tích và sinh mã nguồn xuất bản...';

      try {
        const res = await fetch('/api/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ formula })
        });
        currentData = await res.json();

        if (!currentData.success) {
          $('tikz-output').textContent = currentData.message || 'Không thể khảo sát hàm số này.';
          return;
        }

        // Render công thức MathJax chuẩn mực
        $('render-f').innerHTML = `$$ y = ${currentData.expr_latex} $$`;
        $('render-df').innerHTML = `$$ y' = ${currentData.diff_latex} $$`;
        if (window.MathJax) { MathJax.typesetPromise(); }

        renderActiveTab();
      } catch (err) {
        $('tikz-output').textContent = 'Lỗi kết nối máy chủ: ' + err.message;
      }
    }

    $('btn-analyze').onclick = analyze;
    $('formula').onkeydown = e => { if (e.key === 'Enter') analyze(); };

    document.querySelectorAll('.preset-btn').forEach(btn => {
      btn.onclick = () => {
        $('formula').value = btn.dataset.val;
        analyze();
      };
    });

    $('btn-copy').onclick = async () => {
      if (!currentData || !currentData.success) return;
      let snippet = '';
      let msg = '';
      if (activeTab === 'bbt') {
        snippet = currentData.tikz_tab_body;
        msg = 'Đã sao chép mã Bảng biến thiên tkz-tab!';
      } else if (activeTab === 'graph') {
        snippet = currentData.tikz_graph_body;
        msg = 'Đã sao chép mã Đồ thị TikZ!';
      } else {
        snippet = currentData.typst_doc;
        msg = 'Đã sao chép toàn bộ mã Báo cáo Typst!';
      }
      await navigator.clipboard.writeText(snippet);
      toast(msg);
    };

    $('btn-download').onclick = () => {
      if (!currentData || !currentData.success) return;
      let fullCode = '';
      let filename = '';
      if (activeTab === 'bbt') {
        fullCode = currentData.tikz_tab;
        filename = 'bang-bien-thien.tex';
      } else if (activeTab === 'graph') {
        fullCode = currentData.tikz_graph;
        filename = 'do-thi-oxy.tex';
      } else {
        fullCode = currentData.typst_doc;
        filename = 'khao_sat.typ';
      }
      const blob = new Blob([fullCode], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      toast('Đã tải xuống ' + filename);
    };

    window.onload = analyze;
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def serve_index() -> HTMLResponse:
    return HTMLResponse(content=HTML_CONTENT)


def main():
    """Hàm khởi chạy máy chủ tự động chọn cổng trống riêng biệt."""
    import socket
    import uvicorn

    start_port = 8888
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                break
            port += 1

    print("\n" + "=" * 50)
    print(f"🚀 MÁY CHỦ SẴN SÀNG TẠI: http://127.0.0.1:{port}")
    print("=" * 50 + "\n")
    uvicorn.run("nvmh_math_py.server:app", host="127.0.0.1", port=port, reload=True)


if __name__ == "__main__":
    main()
