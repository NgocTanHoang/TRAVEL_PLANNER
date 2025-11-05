"""
Fix LangSmith project access issue
===================================
Script này sẽ giúp fix lỗi quyền truy cập project trong LangSmith
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key

project_root = Path(__file__).resolve().parent
env_path = project_root / '.env'

if env_path.exists():
    load_dotenv(env_path, encoding='utf-8')

print("=" * 70)
print("FIX LANGSMITH PROJECT ACCESS ISSUE")
print("=" * 70)

print("\n⚠️ Lỗi: Can't access tracing projects")
print("   Có thể do:")
print("   1. Project name không tồn tại trong LangSmith account")
print("   2. API key không có quyền truy cập project")
print("   3. Cần sử dụng default project hoặc tạo project mới")
print("\n" + "=" * 70)

print("\n[GIẢI PHÁP]")
print("=" * 70)

# Option 1: Sử dụng default project
print("\n[Option 1] Sử dụng Default Project (Khuyến nghị)")
print("   - LangSmith sẽ tự động tạo project mới hoặc sử dụng default")
print("   - Không cần project name cụ thể")
print("   - Phù hợp cho development và testing")

use_default = input("\n   Bạn có muốn sử dụng default project? (y/n): ").lower().strip()

if use_default == 'y':
    # Xóa LANGCHAIN_PROJECT để dùng default
    if env_path.exists():
        # Đọc file .env và xóa dòng LANGCHAIN_PROJECT nếu có
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        with open(env_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if not line.strip().startswith('LANGCHAIN_PROJECT='):
                    f.write(line)
        
        print("   ✓ Đã xóa LANGCHAIN_PROJECT, sẽ dùng default project")
    else:
        print("   ⚠ File .env không tồn tại")
    
    print("\n   ✅ Setup hoàn tất!")
    print("   💡 LangSmith sẽ tự động tạo project mới khi chạy workflow")
    
else:
    # Option 2: Tạo project mới với tên khác
    print("\n[Option 2] Tạo Project Mới")
    print("   - Bạn có thể tạo project mới trên LangSmith dashboard")
    print("   - Sau đó set tên project vào .env")
    
    new_project_name = input("\n   Nhập tên project mới (hoặc Enter để giữ nguyên): ").strip()
    
    if new_project_name:
        set_key(str(env_path), 'LANGCHAIN_PROJECT', new_project_name)
        print(f"   ✓ Đã set project name: {new_project_name}")
    else:
        print("   ✓ Giữ nguyên project name hiện tại")

# Option 3: Hướng dẫn manual
print("\n" + "=" * 70)
print("[HƯỚNG DẪN MANUAL]")
print("=" * 70)
print("\n1. Truy cập LangSmith Dashboard:")
print("   https://smith.langchain.com/")
print("\n2. Tạo project mới:")
print("   - Vào Projects -> Create New Project")
print("   - Đặt tên project (ví dụ: vi-vu-travel-planner)")
print("   - Copy tên project và set vào .env")
print("\n3. Hoặc sử dụng default project:")
print("   - Xóa LANGCHAIN_PROJECT từ .env")
print("   - LangSmith sẽ tự động tạo project khi chạy workflow")
print("\n4. Kiểm tra API Key permissions:")
print("   - Vào Settings -> API Keys")
print("   - Đảm bảo API key có quyền 'project:read' và 'project:write'")
print("\n5. Reload environment:")
print("   - Restart application hoặc reload .env file")

print("\n" + "=" * 70)
print("KIỂM TRA LẠI")
print("=" * 70)

# Reload và check
load_dotenv(env_path, override=True, encoding='utf-8')

print("\nCurrent configuration:")
print(f"   LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2', 'Not set')}")
print(f"   LANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT', 'Not set (will use default)')}")
print(f"   LANGCHAIN_API_KEY: {'✓ Set' if os.getenv('LANGCHAIN_API_KEY') else '✗ Not set'}")
print(f"   LANGCHAIN_ENDPOINT: {os.getenv('LANGCHAIN_ENDPOINT', 'Not set')}")

print("\n💡 Next steps:")
print("   1. Chạy lại: python check_tracing.py")
print("   2. Test workflow: python test_with_langsmith.py")
print("   3. Xem traces trên dashboard: https://smith.langchain.com/")

