"""
Script để kiểm tra các model có sẵn trên Groq API
"""
import requests
import os
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Set Groq API key
groq_key = os.getenv('GROQ_API_KEY')
if not groq_key:
    print("❌ GROQ_API_KEY not found in environment variables")
    print("Please set GROQ_API_KEY in your .env file or environment")
    sys.exit(1)

print("=" * 80)
print("KIỂM TRA CÁC MODEL TRÊN GROQ API")
print("=" * 80)

# Get list of available models
url = "https://api.groq.com/openai/v1/models"
headers = {
    "Authorization": f"Bearer {groq_key}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        models = data.get('data', [])
        
        print(f"\n✅ Tìm thấy {len(models)} models:\n")
        
        # Group by model family
        model_families = {}
        for model in models:
            model_id = model.get('id', '')
            # Extract family name (e.g., 'llama-3.1-70b-versatile' -> 'llama-3.1')
            parts = model_id.split('-')
            if len(parts) >= 2:
                family = '-'.join(parts[:2])
            else:
                family = model_id
            
            if family not in model_families:
                model_families[family] = []
            model_families[family].append(model_id)
        
        # Print organized by family
        for family, model_list in sorted(model_families.items()):
            print(f"\n📦 {family.upper()}:")
            for model_id in sorted(model_list):
                print(f"  - {model_id}")
        
        # Recommendations
        print("\n" + "=" * 80)
        print("KHUYẾN NGHỊ CHO DESCRIPTION GENERATION:")
        print("=" * 80)
        
        # Look for large models suitable for description generation
        recommended = []
        for model_id in sorted([m.get('id', '') for m in models]):
            if any(x in model_id.lower() for x in ['70b', '90b', '405b', '120b', 'versatile', 'instruct']):
                recommended.append(model_id)
        
        if recommended:
            print("\n✅ Models được khuyến nghị (theo thứ tự ưu tiên):")
            for i, model in enumerate(recommended[:5], 1):
                print(f"  {i}. {model}")
            
            print(f"\n💡 Model tốt nhất: {recommended[0]}")
        else:
            print("\n⚠️ Không tìm thấy model lớn, sử dụng model đầu tiên trong danh sách")
            if models:
                print(f"  Model: {models[0].get('id', 'N/A')}")
    else:
        print(f"❌ Lỗi: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Lỗi khi kết nối: {e}")
    print("\nThử test trực tiếp với một số model phổ biến...")
    
    # Test common models
    test_models = [
        'llama-3.3-70b-versatile',
        'llama-3.1-70b-versatile',
        'llama-3.1-405b-reasoning',
        'llama-3.2-90b-text-preview',
        'mixtral-8x7b-32768',
        'gemma2-9b-it',
        'gemma2-27b-it',
    ]
    
    print("\n" + "=" * 80)
    print("TEST TRỰC TIẾP CÁC MODEL:")
    print("=" * 80)
    
    try:
        from langchain_groq import ChatGroq
        available = []
        for model in test_models:
            try:
                llm = ChatGroq(model_name=model, groq_api_key=groq_key, temperature=0.7)
                response = llm.invoke("test")
                available.append(model)
                print(f"✅ {model}: Available")
            except Exception as e:
                error_msg = str(e)
                if "does not exist" in error_msg or "404" in error_msg:
                    print(f"❌ {model}: Not available")
                else:
                    print(f"⚠️ {model}: Error")
        
        if available:
            print(f"\n💡 Model được khuyến nghị: {available[0]}")
    except ImportError:
        print("❌ langchain-groq chưa được cài đặt")

print("\n" + "=" * 80)

