with open("src/nvmh_math_py/tikz.py", "r", encoding="utf-8") as f:
    content = f.read()

# Thay thế toàn bộ khối xử lý mốc
new_logic = '''            else:
                y_val_str = _wrap_math(pt.y_latex)
                # Logic tổng quát:
                # 1. Nếu điểm này đứng ngay sau tiệm cận (is_after_pole), lấy dấu khoảng bên PHẢI nó.
                # 2. Ngược lại, lấy dấu khoảng bên TRÁI nó.
                if pt.is_after_pole and i < len(intervals):
                    prefix = "+" if intervals[i].sign == "+" else "-"
                elif i > 0:
                    prefix = "+" if intervals[i-1].sign == "+" else "-"
                else:
                    prefix = "+" if (len(intervals) > 0 and intervals[0].sign == "+") else "-"
                var_elements.append(f"{prefix}/ {y_val_str}")'''

# Dùng replace theo block (cần cẩn thận với thụt lề)
# (Thầy chạy script này để patch)
