---
name: design-system
description: Complete design system for family-oriented apps with accessibility, color psychology, and child-friendly UI patterns.
emoji: 🎨
version: 1.0.0
---

# Design System - Complete Guide

## 🎨 Color System

### Primary Palette (Warm, Inviting)
| Color | Hex | RGB | Usage |
|-------|-----|-----|--------|
| Primary | #667eea | 102, 126, 234 | Main buttons, links, accents |
| Primary Dark | #5a67d8 | 90, 103, 216 | Hover states, active |
| Primary Light | #7c8bf5 | 124, 139, 245 | Background tints |
| Secondary | #764ba2 | 118, 75, 162 | Gradient secondary |
| Secondary Dark | #6b3d8a | 107, 61, 138 | Hover states |

### Semantic Colors
| Color | Hex | RGB | Usage |
|-------|-----|-----|--------|
| Success | #48bb78 | 72, 187, 120 | Positive actions, completions |
| Success Light | #c6f6d5 | 198, 246, 213 | Backgrounds |
| Warning | #ed8936 | 237, 137, 54 | Cautions, attention needed |
| Warning Light | #feebc8 | 254, 235, 200 | Backgrounds |
| Error | #f56565 | 245, 101, 101 | Errors, destructive |
| Error Light | #fed7d7 | 254, 215, 215 | Backgrounds |
| Info | #4299e1 | 66, 153, 225 | Information |
| Info Light | #bee3f8 | 190, 227, 248 | Backgrounds |

### Neutral Palette
| Color | Hex | RGB | Usage |
|-------|-----|-----|--------|
| Text Primary | #1a202c | 26, 32, 44 | Main text |
| Text Secondary | #4a5568 | 74, 85, 104 | Secondary text |
| Text Muted | #718096 | 113, 128, 150 | Labels, hints |
| Background | #f7fafc | 247, 250, 252 | Page background |
| Surface | #ffffff | 255, 255, 255 | Cards, containers |
| Border | #e2e8f0 | 226, 232, 240 | Borders, dividers |

### Color Psychology for Kids Apps
- **Warm colors (orange, yellow)**: Energy, happiness, creativity
- **Cool colors (blue, purple)**: Calm, trust, imagination
- **Bright accents**: Attention, engagement
- **Avoid harsh contrasts**: Eye strain prevention
- **Test with color blindness simulators**: Ensure accessibility

## 📐 Spacing System

### Base Unit: 8px
| Scale | Multiplier | Value | Usage |
|-------|-----------|-------|-------|
| xs | 0.5x | 4px | Tight spacing |
| sm | 1x | 8px | Default internal |
| md | 2x | 16px | Standard spacing |
| lg | 3x | 24px | Section spacing |
| xl | 4x | 32px | Large sections |
| 2xl | 6x | 48px | Page margins |
| 3xl | 8x | 64px | Hero sections |

### Formula
```css
--space-xs: 4px;
--space-sm: 8px;
--space-md: 16px;
--space-lg: 24px;
--space-xl: 32px;
--space-2xl: 48px;
--space-3xl: 64px;
```

## 🔤 Typography System

### Font Stack
```css
--font-primary: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
--font-display: 'Nunito', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
```

### Type Scale
| Level | Size | Line Height | Weight | Usage |
|-------|------|------------|--------|-------|
| Display | 48px | 1.1 | 700 | Hero titles |
| H1 | 36px | 1.2 | 700 | Page titles |
| H2 | 28px | 1.25 | 600 | Section headers |
| H3 | 22px | 1.3 | 600 | Subsection headers |
| Body Large | 18px | 1.6 | 400 | Important body text |
| Body | 16px | 1.6 | 400 | Default body text |
| Body Small | 14px | 1.5 | 400 | Secondary text |
| Caption | 12px | 1.4 | 500 | Labels, hints |

### Reading宽度
- **Optimal line length**: 60-75 characters
- **Body text width**: max 650px
- **Mobile**: readable without zooming

## 📱 Responsive Breakpoints

| Breakpoint | Width | Target |
|-----------|-------|--------|
| xs | 0-479px | Small phones |
| sm | 480-767px | Large phones |
| md | 768-1023px | Tablets portrait |
| lg | 1024-1279px | Tablets landscape / Small laptops |
| xl | 1280-1535px | Desktops |
| 2xl | 1536px+ | Large screens |

## ♿ Accessibility (WCAG 2.1 AA)

### Contrast Ratios
- **Text on Background**: minimum 4.5:1
- **Large Text (18px+)**: minimum 3:1
- **UI Components**: minimum 3:1
- **Focus indicators**: minimum 3:1

### Touch Targets
- **Minimum size**: 44x44px (iOS), 48x48px (Android)
- **Spacing between**: 8px minimum
- **Padding**: at least 12px for interactive elements

### Focus States
```css
:focus-visible {
  outline: 3px solid var(--primary);
  outline-offset: 2px;
}
```

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## 🎯 Component Patterns

### Buttons
```css
.btn {
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.2s ease;
  min-height: 48px;
}

.btn-primary {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
  border: none;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:active {
  transform: translateY(0);
}
```

### Cards
```css
.card {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-lg);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
}

.card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}
```

### Form Inputs
```css
.input {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid var(--border);
  border-radius: 12px;
  font-size: 16px;
  transition: border-color 0.2s;
}

.input:focus {
  border-color: var(--primary);
  outline: none;
}

.input:invalid:not(:placeholder-shown) {
  border-color: var(--error);
}
```

### Loading States
```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--border) 25%,
    var(--background) 50%,
    var(--border) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

## 🎭 Feedback Patterns

### Toast Notifications
```javascript
// Position: bottom-center or top-right
// Duration: 4-6 seconds
// Max width: 400px
```

| Type | Icon | Background | Text Color |
|------|------|-----------|------------|
| Success | ✅ | Success Light | Text Primary |
| Error | ❌ | Error Light | Text Primary |
| Warning | ⚠️ | Warning Light | Text Primary |
| Info | ℹ️ | Info Light | Text Primary |

### Progress Indicators
- **Determinate**: Show exact progress (0-100%)
- **Indeterminate**: Unknown duration, show animation
- **Loading skeleton**: Content placeholder

## 📐 Layout Principles

### Mobile-First
1. Design for smallest screen first
2. Progressive enhancement for larger screens
3. Use relative units (rem, %, vh/vw)

### Safe Areas
```css
/* iOS notch, home indicator */
padding:
  env(safe-area-inset-top),
  env(safe-area-inset-right),
  env(safe-area-inset-bottom),
  env(safe-area-inset-left);
```

### Grid System
```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-md);
}

.grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}
```

## 🎨 Animation Guidelines

### Duration Scale
| Duration | Use Case |
|----------|----------|
| 150ms | Micro-interactions (hover, toggle) |
| 200-300ms | UI state changes |
| 400-500ms | Panel slides, modals |
| 600ms+ | Page transitions |

### Easing Curves
```css
/* Snappy (buttons, toggles) */
--ease-snappy: cubic-bezier(0.2, 0, 0, 1);

/* Smooth (navigation, panels) */
--ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);

/* Bouncy (celebrations) */
--ease-bouncy: cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

## 👶 Child-Friendly Design Patterns

### 1. Clear Visual Hierarchy
- Big, readable text
- Distinct button shapes
- Meaningful icons with text labels

### 2. Encouraging Language
- ✅ "Great job!"
- ✅ "You did it!"
- ❌ Avoid: "Error", "Failed", "Wrong"

### 3. Touch-Friendly
- Large tap targets (minimum 56px)
- Generous spacing
- Swipe gestures when natural

### 4. Visual Feedback
- Celebrate achievements with animations
- Show progress clearly
- Use emoji and icons

### 5. Parental Controls
- Clear demarcation for kid vs parent areas
- Confirmation dialogs for actions
- Easy exit for kids

## 📋 Implementation Checklist

- [ ] Color contrast meets WCAG AA
- [ ] Minimum touch target 44x44px
- [ ] Focus states visible
- [ ] Reduced motion respected
- [ ] Line length 60-75 characters
- [ ] Mobile layout tested
- [ ] Loading states for async operations
- [ ] Error messages are friendly
- [ ] Success feedback is celebratory
- [ ] Icons have text labels
- [ ] Animation under 400ms for UI
- [ ] Test with real users (kids + parents)
