# Vi Vu Frontend Development Setup

Hướng dẫn cài đặt và sử dụng các công cụ frontend cho project Vi Vu.

## 📦 Package.json Overview

File `package.json` này được tối ưu cho Django project với frontend sử dụng:
- **Django Templates** (HTML)
- **Vanilla JavaScript** (không dùng React/Next.js)
- **Tailwind CSS 4.x** (với PostCSS)
- **CSS/JS Utilities**

## 🚀 Cài đặt

### 1. Cài đặt Node.js và npm

Đảm bảo bạn đã cài đặt:
- **Node.js**: >= 18.0.0
- **npm**: >= 9.0.0

Kiểm tra phiên bản:
```bash
node --version
npm --version
```

### 2. Cài đặt Dependencies

```bash
# Di chuyển đến thư mục project
cd TRAVEL_PLANNER

# Cài đặt tất cả dependencies
npm install
```

## 📝 Available Scripts

### CSS Development

```bash
# Build CSS từ global.css (production)
npm run build:css

# Watch CSS changes (development)
npm run watch:css
```

### Linting & Formatting

```bash
# Lint CSS files
npm run lint:css

# Lint JavaScript files
npm run lint:js

# Format CSS files
npm run format:css

# Format JavaScript files
npm run format:js
```

### Django Commands

```bash
# Collect static files (sau khi build CSS)
python manage.py collectstatic

# Run development server
python manage.py runserver
```

## 🎨 Dependencies

### Runtime Dependencies

- **date-fns**: Date manipulation utilities (có thể dùng trong vanilla JS)
- **clsx**: Utility for constructing className strings
- **tailwind-merge**: Merge Tailwind CSS classes

### Development Dependencies

- **tailwindcss**: CSS framework
- **postcss**: CSS processor
- **autoprefixer**: Auto-add vendor prefixes
- **eslint**: JavaScript linter
- **prettier**: Code formatter
- **stylelint**: CSS linter
- **typescript**: Type checking (optional)

## 📁 Project Structure

```
TRAVEL_PLANNER/
├── package.json          # Node.js dependencies
├── postcss.config.js     # PostCSS configuration
├── .eslintrc.json        # ESLint configuration
├── .prettierrc           # Prettier configuration
├── .stylelintrc.json     # Stylelint configuration
├── .npmrc                # NPM configuration
│
├── vivu_backend/
│   ├── static/
│   │   ├── css/
│   │   │   ├── global.css      # Main CSS file (Tailwind input)
│   │   │   ├── output.css      # Compiled CSS (generated)
│   │   │   ├── vivu-colors.css
│   │   │   └── vivu-design-system.css
│   │   └── js/
│   │       ├── index.js
│   │       └── travel_plan_workflow.js
│   └── templates/        # Django templates
│
└── node_modules/         # Node dependencies (gitignored)
```

## 🔧 Workflow

### Development Workflow

1. **Start CSS watcher** (trong terminal riêng):
   ```bash
   npm run watch:css
   ```

2. **Start Django server** (trong terminal khác):
   ```bash
   cd vivu_backend
   python manage.py runserver
   ```

3. **Edit files**:
   - CSS: `vivu_backend/static/css/global.css`
   - JS: `vivu_backend/static/js/*.js`
   - Templates: `vivu_backend/templates/*.html`

4. **CSS changes** sẽ tự động compile khi watch mode chạy

### Production Build

1. **Build CSS**:
   ```bash
   npm run build:css
   ```

2. **Collect static files**:
   ```bash
   cd vivu_backend
   python manage.py collectstatic
   ```

## 🎨 Tailwind CSS Configuration

Tailwind CSS được cấu hình trong `global.css`:

```css
@import "tailwindcss";
@import "tw-animate-css";
```

### Custom Colors

Màu sắc Vi Vu được định nghĩa trong CSS variables:
- Primary (Navy Blue): `#153D68`
- Secondary (Teal): `#00838F`
- Accent (Gold): `#DAA520`

Sử dụng trong Tailwind:
```html
<div class="bg-[var(--primary)] text-[var(--accent)]">
  <!-- Content -->
</div>
```

## 🛠️ Linting & Formatting

### ESLint (JavaScript)

Cấu hình trong `.eslintrc.json`:
- Browser environment
- ES2021 syntax
- Warn on unused variables
- Warn on console/debugger

### Prettier (Code Formatting)

Cấu hình trong `.prettierrc`:
- 2 spaces indentation
- Semicolons enabled
- Single quotes: false
- Print width: 100

### Stylelint (CSS)

Cấu hình trong `.stylelintrc.json`:
- Standard CSS rules
- Tailwind-specific rules ignored
- Custom property patterns allowed

## 📚 Utilities

### date-fns

Sử dụng trong JavaScript:
```javascript
import { format, addDays } from 'date-fns';

const today = new Date();
const tomorrow = addDays(today, 1);
console.log(format(tomorrow, 'yyyy-MM-dd'));
```

**Lưu ý**: Để dùng ES6 modules, bạn cần:
1. Sử dụng build tool (webpack, vite, etc.)
2. Hoặc dùng CDN: `<script type="module">`

### clsx

Sử dụng để merge classes:
```javascript
import clsx from 'clsx';

const className = clsx('base-class', {
  'active': isActive,
  'disabled': isDisabled
});
```

## ⚠️ Lưu ý quan trọng

1. **Không sử dụng React/Next.js dependencies**: File package.json này được tối ưu cho Django templates, không phải React components.

2. **Vanilla JavaScript**: Project sử dụng vanilla JS, không dùng JSX hay React.

3. **CSS Build**: CSS được build từ `global.css` sang `output.css`. Đảm bảo import `output.css` trong templates.

4. **Static Files**: Sau khi build CSS, chạy `collectstatic` để copy files vào `staticfiles/`.

## 🔄 Migration từ Next.js package.json

Nếu bạn có file package.json từ Next.js project và muốn migrate:

1. **Loại bỏ** các dependencies không cần thiết:
   - `next`, `react`, `react-dom`
   - `@radix-ui/*` (không dùng React components)
   - `react-hook-form`, `zod` (React-specific)

2. **Giữ lại** các utilities có thể dùng:
   - `date-fns` (có thể dùng với vanilla JS)
   - `clsx` (utility function)
   - `tailwind-merge` (utility function)

3. **Thêm** các build tools:
   - `tailwindcss`
   - `postcss`
   - `autoprefixer`

## 📖 Tài liệu tham khảo

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [PostCSS Documentation](https://postcss.org/)
- [ESLint Documentation](https://eslint.org/)
- [Prettier Documentation](https://prettier.io/)
- [Django Static Files](https://docs.djangoproject.com/en/5.0/howto/static-files/)

## 🤝 Contributing

Khi thêm dependencies mới:

1. Kiểm tra xem có thể dùng với vanilla JS không
2. Tránh các dependencies React-specific
3. Cập nhật README này nếu cần

## 📝 Changelog

### v1.0.0 (2025-01-XX)
- Initial package.json setup
- Tailwind CSS 4.x integration
- ESLint, Prettier, Stylelint configuration
- PostCSS configuration
- Development workflow setup

