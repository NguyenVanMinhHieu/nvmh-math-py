from nvmh_math_py.analyzer import analyze_function
from nvmh_math_py.tikz import generate_tkz_tab

# Hàm số gây lỗi tiệm cận
formula = "(x^2 + 2*x - 3)/(x - 3)"
ana = analyze_function(formula)

# Sinh mã tkz-tab
code = generate_tkz_tab(ana, standalone=True)

print("--- MÃ TKZ-TAB SINH RA ---")
print(code)

# Kiểm tra sự hiện diện của cấu trúc D và tiền tố cho mốc sau D
# Cấu trúc mong đợi: ... -D+/ ... / ... , -/ $4\sqrt{3}+8$ ...
if "-D+/" in code and "-/" in code.split("-D+/")[1]:
    print("\n✅ KIỂM TRA: Cấu trúc Tiệm cận và Mũi tên đã CHUẨN!")
else:
    print("\n❌ KIỂM TRA: Cấu trúc vẫn chưa đạt chuẩn!")
