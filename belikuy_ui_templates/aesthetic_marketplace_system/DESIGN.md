---
name: Aesthetic Marketplace System
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#514345'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#847375'
  outline-variant: '#d6c2c3'
  surface-tint: '#874e58'
  primary: '#874e58'
  on-primary: '#ffffff'
  primary-container: '#ffb6c1'
  on-primary-container: '#7b444e'
  inverse-primary: '#fcb3be'
  secondary: '#715572'
  on-secondary: '#ffffff'
  secondary-container: '#f8d5f7'
  on-secondary-container: '#755977'
  tertiary: '#6d5a58'
  on-tertiary: '#ffffff'
  tertiary-container: '#ddc4c1'
  on-tertiary-container: '#63504e'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffd9de'
  primary-fixed-dim: '#fcb3be'
  on-primary-fixed: '#360c17'
  on-primary-fixed-variant: '#6b3741'
  secondary-fixed: '#fbd8fa'
  secondary-fixed-dim: '#debcde'
  on-secondary-fixed: '#29132c'
  on-secondary-fixed-variant: '#583e5a'
  tertiary-fixed: '#f7ddda'
  tertiary-fixed-dim: '#dac1be'
  on-tertiary-fixed: '#261817'
  on-tertiary-fixed-variant: '#544341'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
typography:
  h1:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  h2:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.3'
  h3:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
  container-max: 1200px
  gutter: 24px
---

## Brand & Style

The visual identity of this design system centers on "kawaii-chic"—a sophisticated blend of playful charm and high-end minimalism. It is designed to evoke feelings of warmth, safety, and inspiration, catering to a demographic that values both curation and cuteness. 

The style is a hybrid of **Minimalism** and **Soft-Neomorphism**. It utilizes a "Pinterest-inspired" layout logic (visual-first, airy) combined with the functional clarity of Notion. The interface avoids harsh lines and high-contrast aggression, opting instead for tactile softness and organic shapes. Every interaction should feel like a soft click or a gentle transition, maintaining a premium "boutique" atmosphere.

## Colors

The palette is anchored by "Pastel Romance." The **Primary Pink** (#FFB6C1) is used for active states and brand moments, while the **Secondary Purple** (#CBAACB) provides a calming counterpoint for secondary actions and categorization.

A custom **Soft Gradient** is the signature accent for high-intent actions (like "Buy Now" or "Checkout"). The neutral scale is deliberately warm; we avoid pure blacks, using a deep charcoal for text to maintain the soft aesthetic. Surfaces use an off-white tint to reduce eye strain and enhance the "airy" feel of the marketplace.

## Typography

This design system uses a two-tier typographic scale. **Plus Jakarta Sans** provides a friendly, geometric personality for headlines, featuring open counters that feel welcoming. **Inter** is used for body copy and UI labels to ensure maximum legibility and a systematic, modern feel.

To maintain the "premium" aesthetic, line heights are generous (1.6x for body text). Headings should use tight letter-spacing to appear more curated and editorial, reminiscent of high-end lifestyle magazines.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy for the main storefront to ensure content feels centered and intentional, like an art gallery. Dashboards utilize a fluid sidebar model. 

We employ a "Generous White-Space" rule: internal padding within components (like cards and modals) should always lean towards the `lg` (24px) or `xl` (48px) units to create an "airy" breathing room. Vertical rhythm is strictly enforced using an 8px baseline grid to keep the "clean" Notion-style alignment intact despite the soft visual language.

## Elevation & Depth

Hierarchy is established through **Ambient Shadows** and **Tonal Layers**. Instead of harsh drop shadows, we use "Shadow Glows"—diffused, low-opacity blurs that are slightly tinted with the primary pink color (`rgba(255, 182, 193, 0.2)`).

- **Level 0 (Floor):** The main background (`#FFFFFF`).
- **Level 1 (Subtle):** Off-white surfaces (`#F8F9FA`) with no shadow, used for secondary sections.
- **Level 2 (Floating):** Product cards and navigation bars, using a soft, wide-spread shadow.
- **Level 3 (Overlay):** Modals and dropdowns, using a deeper shadow and a subtle backdrop blur (glassmorphism) on the scrim to maintain context without visual clutter.

## Shapes

The shape language is strictly **Rounded**. Sharp corners are non-existent in the design system. 
- Standard components (Cards, Modals) use `rounded-lg` (16px).
- Interactive elements (Buttons, Inputs) use `rounded-xl` (24px) or full pill-shapes.
- Images should always feature a soft radius to match the container.

This high level of roundedness communicates friendliness and safety, essential for a cute and modern aesthetic.

## Components

### Buttons
Buttons are high-affordance elements. Primary buttons use the **Soft Gradient** with a subtle lift on hover. They are pill-shaped (full rounding) and use `label-caps` for text to provide a sophisticated contrast to the soft shapes.

### Product Cards
Cards feature a "Float" state. They have no visible borders. Instead, they sit on a white surface with a Level 2 shadow. The product image is nested within with a 12px radius, and price tags are highlighted in the Primary Pink.

### Input Fields
Inputs are "Airy"—defined by a light gray background (`#F8F9FA`) rather than a border. On focus, the background turns white, and a 2px soft pink glow (shadow) appears. Icons (Lucide style) are placed at the start to guide the eye.

### Navigation
- **Storefront Nav:** A top-fixed, glassmorphic bar (backdrop-blur: 10px) that keeps the focus on the products while providing essential search and cart access.
- **Dashboard Nav:** A clean sidebar with plenty of vertical spacing between links. Active states are indicated by a soft pink "blob" background behind the icon.

### Status Badges & Modals
Badges (e.g., "New," "Sale") use highly desaturated versions of the primary/secondary colors with high-saturation text for a "pastel-pop" look. Modals enter with a scale-in transition and utilize large corner radii and generous internal padding.