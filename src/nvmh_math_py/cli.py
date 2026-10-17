"""Command-line interface for CHD Math Studio."""

from __future__ import annotations
import argparse
import sys

from nvmh_math_py.analyzer import analyze_function
from nvmh_math_py.tikz import generate_tkz_tab


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Khảo sát hàm số biểu tượng bằng SymPy & Xuất mã TikZ."
    )
    parser.add_argument("formula", help="Công thức hàm số (ví dụ: 'ln(x)/x', 'x*exp(-x)', 'x^4 - 4x^2 + 1')")
    parser.add_argument("-o", "--output", help="Đường dẫn file .tex để lưu mã TikZ", default=None)
    parser.add_argument("--body-only", action="store_true", help="Chỉ xuất phần tikzpicture (không kèm preamble)")

    args = parser.parse_args()

    print(f"[*] Đang khảo sát hàm số: y = {args.formula} ...", file=sys.stderr)
    analysis = analyze_function(args.formula)
    latex_code = generate_tkz_tab(analysis, standalone=not args.body_only)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(latex_code)
        print(f"[+] Đã lưu mã TikZ vào: {args.output}", file=sys.stderr)
    else:
        print(latex_code)


if __name__ == "__main__":
    main()
