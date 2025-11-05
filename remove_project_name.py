"""
Remove LANGCHAIN_PROJECT để LangSmith tự động tạo project
"""
from pathlib import Path
from dotenv import load_dotenv
import os

project_root = Path(__file__).resolve().parent
env_path = project_root / '.env'

print("=" * 70)
print("FIX LANGSMITH PROJECT ACCESS ISSUE")
print("=" * 70)

if not env_path.exists():
    print("\n⚠ File .env không tồn tại!")
    exit(1)

# Đọc file .env
with open(env_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Xóa dòng LANGCHAIN_PROJECT
new_lines = []
removed = False
for line in lines:
    if line.strip().startswith('LANGCHAIN_PROJECT='):
        removed = True
        print(f"\n✓ Đã xóa dòng: {line.strip()}")
    else:
        new_lines.append(line)

# Ghi lại file
if removed:
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("\n✅ Đã xóa LANGCHAIN_PROJECT từ .env")
    print("   LangSmith sẽ tự động tạo project mới khi chạy workflow")
else:
    print("\n✓ LANGCHAIN_PROJECT không có trong .env")
    print("   LangSmith sẽ tự động tạo project mới")

# Reload và verify
load_dotenv(env_path, override=True, encoding='utf-8')

print("\n" + "=" * 70)
print("KẾT QUẢ")
print("=" * 70)

print(f"\nLANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT', 'Not set (LangSmith sẽ tự động tạo)')}")
print(f"LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2', 'Not set')}")
print(f"LANGCHAIN_API_KEY: {'✓ Set' if os.getenv('LANGCHAIN_API_KEY') else '✗ Not set'}")

print("\n💡 Next steps:")
print("   1. Chạy lại workflow: python test_with_langsmith.py")
print("   2. LangSmith sẽ tự động tạo project mới")
print("   3. Xem project trên dashboard: https://smith.langchain.com/")

