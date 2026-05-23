#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script test semantic place classifier
"""
import os
import sys
from pathlib import Path

# Setup path
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

from vivu_backend.utils.semantic_place_classifier import (
    classify_place_by_semantics,
    extract_place_features,
    understand_place_semantics,
    is_suitable_for_travel_style
)

# Test cases
test_cases = [
    {
        'name': 'Chùa Một Cột',
        'description': 'Ngôi chùa nổi tiếng với kiến trúc độc đáo, là biểu tượng của Hà Nội',
        'type_hint': 'temple',
        'category': 'attraction'
    },
    {
        'name': 'Nhà hàng Phở Gia Truyền',
        'description': 'Quán phở nổi tiếng với hương vị đậm đà, phục vụ 24/7',
        'type_hint': 'restaurant',
        'category': 'dining'
    },
    {
        'name': 'Vinpearl Resort Nha Trang',
        'description': 'Khu nghỉ dưỡng 5 sao với bãi biển riêng, spa và nhiều tiện nghi',
        'type_hint': 'resort',
        'category': 'accommodation'
    },
    {
        'name': 'Bảo tàng Lịch sử Việt Nam',
        'description': 'Nơi trưng bày các hiện vật lịch sử và văn hóa của Việt Nam',
        'type_hint': 'museum',
        'category': 'cultural'
    },
    {
        'name': 'Chợ Bến Thành',
        'description': 'Chợ truyền thống nổi tiếng với nhiều mặt hàng địa phương',
        'type_hint': 'market',
        'category': 'shopping'
    },
    {
        'name': 'Spa & Wellness Center',
        'description': 'Trung tâm spa và wellness với các dịch vụ massage và thư giãn',
        'type_hint': 'spa',
        'category': 'wellness'
    },
]

print("="*80)
print("TEST SEMANTIC PLACE CLASSIFIER")
print("="*80)

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*80}")
    print(f"Test Case {i}: {test['name']}")
    print(f"{'='*80}")
    
    # Test classification
    loai_dia_diem = classify_place_by_semantics(
        name=test['name'],
        description=test['description'],
        type_hint=test.get('type_hint', ''),
        category=test.get('category', '')
    )
    print(f"Phân loại: {loai_dia_diem}")
    
    # Test full understanding
    semantics = understand_place_semantics(
        name=test['name'],
        description=test['description'],
        type_hint=test.get('type_hint', ''),
        category=test.get('category', '')
    )
    print(f"Độ tin cậy: {semantics['confidence']:.2f}")
    print(f"Đặc điểm:")
    features = semantics['features']
    print(f"  - Phù hợp với: {', '.join(features['suitable_for']) if features['suitable_for'] else 'Tất cả'}")
    print(f"  - Thời gian tốt nhất: {', '.join(features['best_time'])}")
    print(f"  - Thời lượng: {features['duration_hours']} giờ")
    print(f"  - Mức giá: {features['price_level']}")
    print(f"  - Tags: {', '.join(features['tags']) if features['tags'] else 'Không có'}")
    
    # Test travel style suitability
    for style in ['budget', 'luxury', 'romantic', 'family', 'adventure']:
        suitable = is_suitable_for_travel_style(features, style)
        print(f"  - Phù hợp với {style}: {'Có' if suitable else 'Không'}")

print("\n" + "="*80)
print("✓ Hoàn thành test!")
print("="*80)

