"""
═══════════════════════════════════════════════════════════════════════════════
    KHỞI CHẠY NHANH - HỆ THỐNG LẬP KẾ HOẠCH DU LỊCH THÔNG MINH
═══════════════════════════════════════════════════════════════════════════════

Chạy toàn bộ hệ thống với một lệnh duy nhất

Sử dụng:
    python run_ui.py
    
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import os

print("="*80)
print(" 🌍 HỆ THỐNG LẬP KẾ HOẠCH DU LỊCH THÔNG MINH")
print("    Multi-Agent System for Travel Planning in Vietnam")
print("="*80)
print()
print("🚀 Đang khởi động hệ thống...")
print("-" * 60)

# Kiểm tra dependencies
try:
    import gradio as gr
    print("✅ Gradio đã cài đặt")
except ImportError:
    print("❌ Chưa có Gradio. Đang cài đặt...")
    os.system("pip install gradio")
    import gradio as gr

try:
    from langchain import __version__
    print("✅ LangChain đã cài đặt")
except ImportError:
    print("❌ Chưa có LangChain. Vui lòng chạy:")
    print("   pip install langchain langchain_core langgraph openai")
    sys.exit(1)

print("-" * 60)
print()
print("📱 Đang khởi động giao diện web...")
print("🌐 Giao diện sẽ tự động mở trong trình duyệt")
print("🔗 Hoặc truy cập: http://localhost:7860")
print()
print("💡 MẸO: Nhấn CTRL+C để dừng server")
print()
print("="*80)
print()

# Import và chạy UI
from app import tao_giao_dien

demo = tao_giao_dien()
demo.launch(
    server_name="127.0.0.1",
    share=False,
    show_error=True,
    inbrowser=True
    # Auto-find available port
)
