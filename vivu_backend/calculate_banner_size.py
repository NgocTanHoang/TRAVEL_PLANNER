"""
Tính toán kích thước nội dung của hero banner không tính padding
"""
print("=" * 80)
print("KÍCH THƯỚC NỘI DUNG HERO BANNER (KHÔNG TÍNH PADDING)")
print("=" * 80)

# Padding của .hero-banner
hero_padding_top = "3rem (48px)"
hero_padding_bottom = "3rem (48px)"
hero_padding_left_right = "2rem (32px)"

print(f"\n[PADDING CỦA .hero-banner (đã loại trừ)]:")
print(f"  - Top/Bottom: {hero_padding_top}")
print(f"  - Left/Right: {hero_padding_left_right}")

# Kích thước nội dung
print("\n" + "=" * 80)
print("KÍCH THƯỚC NỘI DUNG BÊN TRONG:")
print("=" * 80)

print("\n1. .hero-content (Phần trên):")
print("   - .hero-title:")
print("     • font-size: clamp(2rem, 5vw, 3.5rem) = 2rem - 3.5rem")
print("     • line-height: 1.2")
print("     • margin-bottom: 1rem (16px)")
print("     • Chiều cao: ~2.4rem - 4.2rem (38.4px - 67.2px)")

print("\n   - .hero-subtitle:")
print("     • font-size: clamp(1rem, 2vw, 1.25rem) = 1rem - 1.25rem")
print("     • line-height: 1.6")
print("     • margin-bottom: 2rem (32px)")
print("     • Chiều cao: ~1.6rem - 2rem (25.6px - 32px)")

print("\n   - .hero-cta (Buttons):")
print("     • gap: 1rem (16px)")
print("     • Button padding: 0.875rem 2rem = 14px top/bottom")
print("     • Button height: ~2.75rem (44px)")
print("     • Chiều cao: ~2.75rem (44px)")

print("\n   - margin-bottom của .hero-content: 3rem (48px)")
print("\n   → Tổng chiều cao .hero-content: ~11.75rem - 13.55rem (188px - 217px)")

print("\n2. .hero-stats (Phần dưới):")
print("   - .stat-item:")
print("     • padding: 1.5rem (24px) top/bottom")
print("     • .stat-number:")
print("       - font-size: 2rem (32px)")
print("       - line-height: 1.2")
print("       - margin-bottom: 0.5rem (8px)")
print("       - Chiều cao: ~2.9rem (46.4px)")
print("     • .stat-label:")
print("       - font-size: 0.875rem (14px)")
print("       - line-height: 1.6")
print("       - Chiều cao: ~1.4rem (22.4px)")
print("     • Tổng chiều cao stat-item: padding (48px) + number (46.4px) + label (22.4px) = ~7.3rem (116.8px)")

print("\n   - gap giữa các stat-item: 2rem (32px)")
print("   → Chiều cao .hero-stats: ~7.3rem (116.8px)")

print("\n" + "=" * 80)
print("TỔNG KẾT:")
print("=" * 80)
print("\nChiều cao nội dung (không tính padding):")
print("  = .hero-content (~11.75rem - 13.55rem)")
print("  + .hero-stats (~7.3rem)")
print("  = ~19.05rem - 20.85rem")
print("  = ~305px - 334px")

print("\nChiều rộng nội dung:")
print("  - .hero-container: max-width: 1280px")
print("  - Nội dung bên trong: 100% của container (tối đa 1280px)")
print("  - .hero-stats: max-width: 600px (centered)")

print("\n" + "=" * 80)
print("KÍCH THƯỚC TỔNG THỂ (BAO GỒM PADDING):")
print("=" * 80)
print("  - Chiều cao: ~19.05rem - 20.85rem + 3rem (top) + 3rem (bottom)")
print("            = ~25.05rem - 26.85rem")
print("            = ~401px - 430px")
print("  - Chiều rộng: 100% viewport (max-width: 1280px)")

print("\n" + "=" * 80)
print("📱 RESPONSIVE (Mobile - max-width: 768px):")
print("=" * 80)
print("  - Padding: 2rem 1rem (32px top/bottom, 16px left/right)")
print("  - .hero-content margin-bottom: 2rem (32px)")
print("  - .hero-stats gap: 1rem (16px)")
print("  - .stat-item padding: 1rem (16px)")
print("  - .stat-number font-size: 1.5rem (24px)")
print("  → Chiều cao nội dung mobile: ~15rem - 17rem (240px - 272px)")

