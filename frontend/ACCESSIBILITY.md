# Accessibility Guide

This document outlines the accessibility features implemented in the SoftBankCashWire frontend application to ensure WCAG 2.1 AA compliance.

## Overview

The application has been designed with accessibility as a core requirement, implementing comprehensive features to support users with disabilities including:

- Screen reader compatibility
- Keyboard navigation support
- High contrast mode
- Responsive design for mobile and tablet devices
- Touch-friendly interface elements
- Reduced motion preferences

## Accessibility Features

### 1. WCAG 2.1 AA Compliance

All components have been designed and tested to meet WCAG 2.1 AA standards:

- **Perceivable**: Content is presented in ways users can perceive
- **Operable**: Interface components are operable by all users
- **Understandable**: Information and UI operation are understandable
- **Robust**: Content can be interpreted by assistive technologies

### 2. Screen Reader Support

#### ARIA Attributes
- Proper use of `aria-label`, `aria-labelledby`, and `aria-describedby`
- Live regions for dynamic content updates (`aria-live`)
- Role attributes for semantic meaning
- State attributes (`aria-expanded`, `aria-selected`, `aria-checked`)

#### Screen Reader Announcements
```typescript
import { useAccessibility } from '../contexts/AccessibilityContext'

const { announceToScreenReader } = useAccessibility()
announceToScreenReader('Transaction completed successfully', 'assertive')
```

#### Semantic HTML
- Proper heading hierarchy (h1, h2, h3, etc.)
- Semantic landmarks (`main`, `nav`, `section`, `article`)
- Form labels and fieldsets
- Table headers and captions

### 3. Keyboard Navigation

#### Focus Management
- Visible focus indicators on all interactive elements
- Logical tab order throughout the application
- Focus trapping in modals and dialogs
- Skip links for main content

#### Keyboard Shortcuts
- **Tab**: Navigate forward through interactive elements
- **Shift + Tab**: Navigate backward through interactive elements
- **Enter/Space**: Activate buttons and links
- **Escape**: Close modals and dropdowns
- **Arrow Keys**: Navigate within lists and tables

#### Custom Hook Usage
```typescript
import { useKeyboardNavigation } from '../hooks/useKeyboardNavigation'

const { containerRef, focusFirst, focusNext } = useKeyboardNavigation({
  onEscape: () => closeModal(),
  onEnter: () => selectItem(),
  trapFocus: true
})
```

### 4. Visual Accessibility

#### High Contrast Mode
The application supports high contrast mode for users with visual impairments:

```css
[data-theme="high-contrast"] {
  --hc-bg: #000000;
  --hc-text: #ffffff;
  --hc-border: #ffffff;
  --hc-focus: #ffff00;
}
```

#### Color Contrast
- All text meets WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text)
- Color is not the only means of conveying information
- Focus indicators have sufficient contrast

#### Font Scaling
Users can adjust font sizes through accessibility settings:
- Default size (1rem)
- Large text (1.2rem)
- Extra large text (1.4rem)

### 5. Responsive Design

#### Mobile-First Approach
- Responsive breakpoints: xs (475px), sm (640px), md (768px), lg (1024px), xl (1280px)
- Touch-friendly interface elements (minimum 44px touch targets)
- Optimized layouts for different screen sizes

#### Touch Accessibility
```css
.touch-target {
  min-height: 44px;
  min-width: 44px;
}

.touch-target-sm {
  min-height: 36px;
  min-width: 36px;
}
```

### 6. Motion and Animation

#### Reduced Motion Support
Respects user's motion preferences:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

#### Animation Controls
Users can disable animations through accessibility settings.

## Component Accessibility

### AccessibleButton
- Proper ARIA attributes
- Loading states with screen reader feedback
- Keyboard activation support
- Touch-friendly sizing

```typescript
<AccessibleButton
  variant="primary"
  loading={isLoading}
  loadingText="Saving..."
  aria-describedby="button-help"
>
  Save Changes
</AccessibleButton>
```

### AccessibleInput
- Associated labels and error messages
- ARIA validation states
- Helper text support
- Required field indicators

```typescript
<AccessibleInput
  label="Email Address"
  type="email"
  required
  error={errors.email}
  helperText="Enter your work email address"
/>
```

### AccessibleModal
- Focus trapping and restoration
- Escape key handling
- Proper ARIA attributes
- Background scroll prevention

```typescript
<AccessibleModal
  isOpen={isOpen}
  onClose={handleClose}
  title="Confirm Action"
  aria-describedby="modal-description"
>
  <p id="modal-description">Are you sure you want to proceed?</p>
</AccessibleModal>
```

### AccessibleTable
- Proper table structure with headers
- Sortable columns with keyboard support
- Row and column navigation
- Screen reader friendly content

```typescript
<AccessibleTable
  data={transactions}
  columns={columns}
  caption="Transaction history"
  aria-label="Your recent transactions"
  onSort={handleSort}
/>
```

## Testing Accessibility

### Automated Testing
The application includes comprehensive accessibility tests using jest-axe:

```typescript
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(toHaveNoViolations)

test('should not have accessibility violations', async () => {
  const { container } = render(<Component />)
  const results = await axe(container)
  expect(results).toHaveNoViolations()
})
```

### Manual Testing Checklist

#### Keyboard Navigation
- [ ] All interactive elements are reachable via keyboard
- [ ] Tab order is logical and intuitive
- [ ] Focus indicators are visible and clear
- [ ] No keyboard traps (except intentional focus trapping)

#### Screen Reader Testing
- [ ] Content is announced correctly
- [ ] Form labels and errors are associated properly
- [ ] Dynamic content updates are announced
- [ ] Navigation landmarks are present

#### Visual Testing
- [ ] Text has sufficient color contrast
- [ ] Content is readable at 200% zoom
- [ ] High contrast mode works correctly
- [ ] No information is conveyed by color alone

#### Mobile Testing
- [ ] Touch targets are at least 44px
- [ ] Content is accessible on small screens
- [ ] Gestures have keyboard alternatives
- [ ] Orientation changes work correctly

### Testing Tools

#### Browser Extensions
- **axe DevTools**: Automated accessibility testing
- **WAVE**: Web accessibility evaluation
- **Lighthouse**: Accessibility audit included

#### Screen Readers
- **NVDA** (Windows): Free screen reader
- **JAWS** (Windows): Popular commercial screen reader
- **VoiceOver** (macOS/iOS): Built-in screen reader
- **TalkBack** (Android): Built-in screen reader

#### Keyboard Testing
- Unplug your mouse and navigate using only the keyboard
- Use Tab, Shift+Tab, Enter, Space, and Arrow keys
- Ensure all functionality is accessible

## Accessibility Settings

Users can customize their accessibility preferences through the settings panel:

### Theme Options
- Default theme
- High contrast theme

### Text Size Options
- Default size
- Large text
- Extra large text

### Motion Preferences
- Enable/disable animations and transitions
- Respect system motion preferences

### Screen Reader Options
- Enable/disable announcement features
- Control announcement priority levels

## Implementation Guidelines

### For Developers

#### 1. Semantic HTML First
Always use semantic HTML elements before adding ARIA:
```html
<!-- Good -->
<button>Submit</button>

<!-- Avoid -->
<div role="button" tabindex="0">Submit</div>
```

#### 2. Progressive Enhancement
Build functionality that works without JavaScript, then enhance:
```typescript
// Ensure forms work without JavaScript
<form action="/submit" method="post">
  <input type="submit" value="Submit" />
</form>
```

#### 3. Test Early and Often
- Run automated tests with every build
- Test with keyboard navigation regularly
- Use screen readers during development

#### 4. Follow ARIA Best Practices
- Use ARIA to enhance, not replace, semantic HTML
- Ensure ARIA attributes are properly associated
- Test with actual assistive technologies

### Code Review Checklist

- [ ] Semantic HTML elements used appropriately
- [ ] All interactive elements have accessible names
- [ ] Form inputs have associated labels
- [ ] Images have appropriate alt text
- [ ] Color contrast meets WCAG standards
- [ ] Keyboard navigation works correctly
- [ ] ARIA attributes are used properly
- [ ] Focus management is implemented
- [ ] Error messages are accessible
- [ ] Dynamic content updates are announced

## Resources

### WCAG Guidelines
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM WCAG Checklist](https://webaim.org/standards/wcag/checklist)

### Testing Tools
- [axe-core](https://github.com/dequelabs/axe-core)
- [WAVE Web Accessibility Evaluator](https://wave.webaim.org/)
- [Lighthouse Accessibility Audit](https://developers.google.com/web/tools/lighthouse)

### Screen Reader Guides
- [NVDA User Guide](https://www.nvaccess.org/documentation/)
- [VoiceOver User Guide](https://support.apple.com/guide/voiceover/)
- [JAWS Documentation](https://www.freedomscientific.com/products/software/jaws/)

### Development Resources
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [A11y Project](https://www.a11yproject.com/)
- [WebAIM Resources](https://webaim.org/resources/)

## Support

For accessibility-related questions or issues:

1. Check this documentation first
2. Review the component examples and tests
3. Test with actual assistive technologies
4. Consult WCAG guidelines for specific requirements

Remember: Accessibility is not a feature to be added later—it should be considered from the beginning of the design and development process.