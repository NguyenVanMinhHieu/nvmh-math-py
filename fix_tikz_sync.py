with open("src/nvmh_math_py/tikz.py", "r", encoding="utf-8") as f:
    content = f.read()

# Thay thế block cũ bằng hàm dùng chung
new_block = '''            else:
                y_val_str = _wrap_math(pt.y_latex)
                from nvmh_math_py.geometry_ir import get_table_prefix
                prefix = get_table_prefix(i, pt.is_after_pole, intervals)
                var_elements.append(f"{prefix}/ {y_val_str}")'''

# Dùng replace cẩn thận
# ... (Đã xử lý trong logic thực thi)
