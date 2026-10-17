import sympy as sp
from nvmh_math_py.analyzer import analyze_function
from nvmh_math_py.tikz import generate_tkz_tab

# Hàm số gây lỗi FR42 trước đó
formula = "(x^2 + 2*x - 3)/(x - 3)"
ana = analyze_function(formula)

# Sinh mã tkz-tab
code = generate_tkz_tab(ana, standalone=True)

# In kết quả để kiểm tra trực quan
print("-" * 20)
print("MÃ TIKZ ĐÃ SINH:")
print("-" * 20)
print(code)

# Kiểm tra tiền tố mốc thứ 4 ($4\sqrt{3}+8$)
if "-/ $4 \\sqrt{3} + 8$" in code:
    print("\n✅ THÀNH CÔNG: Mốc cực tiểu đã có tiền tố '-/'")
elif "+/ $4 \\sqrt{3} + 8$" in code:
    print("\n✅ THÀNH CÔNG: Mốc cực tiểu đã có tiền tố '+/'")
else:
    print("\n❌ LỖI: Mốc cực tiểu vẫn thiếu tiền tố!")
