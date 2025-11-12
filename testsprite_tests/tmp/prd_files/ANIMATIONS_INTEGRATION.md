# Animations Integration Guide

## ✅ Đã tích hợp

File `animations.css` đã được tích hợp vào project Vi Vu với các tính năng sau:

### 1. Keyframe Animations
- `fadeIn` - Fade in effect
- `fadeInUp` - Fade in từ dưới lên
- `fadeInDown` - Fade in từ trên xuống
- `fadeInLeft` - Fade in từ trái
- `fadeInRight` - Fade in từ phải
- `scaleIn` - Scale in effect
- `float` - Floating animation (subtle)
- `pulse` - Pulse effect
- `glow` - Glow effect (sử dụng màu Teal của Vi Vu)
- `shimmer` - Shimmer loading effect
- `bounce` - Bounce animation
- `ripple` - Ripple effect cho buttons
- `slideInUp` - Slide in từ dưới

### 2. Component Animations

#### Navbar
- Fade in từ trên xuống khi load
- Logo float animation trên hover (desktop only)
- User avatar float animation trên hover (desktop only)

#### Search Dropdown
- Fade in khi hiển thị
- Scale in cho các items khi hover

#### Hero Banner
- Fade in khi load
- Scale effect trên hover

#### Place Cards
- Fade in up khi load
- Stagger animation cho danh sách (delay khác nhau)
- Glow effect trên hover (desktop only)
- Scale effect cho images trên hover

#### Feature Cards
- Fade in up với stagger delay
- Bounce animation cho icon trên hover
- Float animation trên hover (desktop only)

#### Buttons
- Ripple effect khi click
- Bounce animation trên hover

#### Modals
- Slide in từ dưới lên
- Fade in cho overlay

#### Nearby Place Detail
- Stagger animation cho các sections
- Fade in up cho image và content

### 3. Loading States
- Pulse animation cho loading placeholders
- Shimmer effect cho skeleton loading

### 4. Scroll Animations
- Elements với class `.scroll-animate` sẽ animate khi scroll vào viewport
- Sử dụng Intersection Observer API (qua JavaScript)

### 5. Performance Optimizations
- `will-change` property cho frequently animated elements
- Reduced animations trên mobile
- Disable float animations trên mobile
- Throttled scroll events

### 6. Accessibility
- Respects `prefers-reduced-motion` media query
- Instant animations cho users who prefer reduced motion
- Essential transitions vẫn hoạt động nhưng nhanh hơn

## 📁 Files đã tạo/cập nhật

1. **TRAVEL_PLANNER/vivu_backend/static/css/animations.css** - File animations mới
2. **TRAVEL_PLANNER/vivu_backend/templates/index.html** - Thêm link đến animations.css
3. **TRAVEL_PLANNER/vivu_backend/templates/base.html** - Thêm link đến animations.css
4. **TRAVEL_PLANNER/vivu_backend/static/js/index.js** - Thêm scroll animation handler

## 🎨 Màu sắc

Animations sử dụng màu sắc Vi Vu:
- **Glow effect**: Sử dụng Secondary color (Teal #00838F)
- **Accent animations**: Sử dụng Accent color (Gold #DAA520)
- **Shadows**: Sử dụng Primary color (Navy Blue #153D68) với opacity

## 📱 Responsive

- **Desktop (>768px)**: Full animations với float effects
- **Mobile (<=768px)**: Reduced animations, không có float effects
- **Performance**: Tối ưu cho mobile với will-change và reduced motion

## 🚀 Sử dụng

### Thêm scroll animation cho element:
```html
<div class="scroll-animate">
  <!-- Content -->
</div>
```

### Thêm skeleton loading:
```html
<div class="skeleton-shimmer loading-placeholder">
  <!-- Loading content -->
</div>
```

## ⚙️ Customization

### Thay đổi animation speed:
```css
.place-bar {
  animation-duration: 0.5s; /* Thay đổi thời gian */
}
```

### Thay đổi glow color:
```css
@keyframes glow {
  0%, 100% {
    box-shadow: 0 0 20px rgba(0, 131, 143, 0.3); /* Thay đổi màu */
  }
}
```

### Disable animations cho specific element:
```css
.no-animation {
  animation: none !important;
  transition: none !important;
}
```

## 🐛 Troubleshooting

### Animations không chạy:
1. Kiểm tra file `animations.css` đã được load chưa
2. Kiểm tra browser console cho errors
3. Kiểm tra `prefers-reduced-motion` setting

### Performance issues:
1. Disable animations trên mobile (đã tự động)
2. Giảm số lượng animated elements
3. Sử dụng `will-change` sparingly

### Conflicts với code hiện có:
1. Animations không override existing styles
2. Sử dụng specificity để override nếu cần
3. Check for conflicting transitions

## 📝 Notes

- Animations được tối ưu cho performance
- Respects user preferences (prefers-reduced-motion)
- Mobile-friendly với reduced animations
- Sử dụng Vi Vu brand colors
- Không conflict với existing code

## 🔄 Updates

Nếu cần thêm animations mới:
1. Thêm keyframes vào `animations.css`
2. Apply cho các elements cần thiết
3. Test trên desktop và mobile
4. Đảm bảo accessibility

