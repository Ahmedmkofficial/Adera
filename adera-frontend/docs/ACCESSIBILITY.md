# Accessibility

Target: WCAG 2.2 level AA as it applies to this project.

## Built in

- Every field has a real label; every icon-only button has a name.
- Keyboard: everything works with Tab, Enter, Space and Escape. There is a "Skip to content" link. After a page change, focus moves to the page content and the browser tab title changes, so screen readers announce the new page.
- Visible focus outline on every control.
- The risk sheet is a dialog: focus moves into it, Escape closes it.
- "Hold to send anyway" works with the keyboard (hold Space or Enter).
- The relationship graph has a text list of every node, so it can be used without a mouse.
- The risk-history chart has a text description and a hidden list of its values.
- Status changes and errors are announced (`role="alert"`, `role="status"`, `aria-live`).
- Motion is short and is turned off when the system asks for reduced motion (the score count-up and the sheet animation).
- No text smaller than 11 px. Risk is never shown by color alone: every colored item also has a word (Critical, High...).
- Page language is set; the Ethiopic font is loaded for Amharic text.

## Contrast (measured)

| Text | Ratio | Result |
|---|---|---|
| Ink `#1c1c1e` on paper `#f6f5f1` | 15.6 : 1 | pass |
| Muted `#6e6e73` on paper / white | 4.65 / 5.07 | pass |
| Risk text, low `#2a7352` | 5.2 on paper | pass |
| Risk text, moderate `#9c5f12` | 4.7 on paper | pass |
| Risk text, high `#b84a14` | 4.8 on paper | pass |
| Risk text, critical `#b3261e` | 6.0 on paper | pass |

The lighter brand colors (`#c9852b` amber, `#d9622b` orange) measure about 2.8 to 3.7 and are used **only for fills and lines** (dots, ruler markers, chart line), where a word label always sits next to them.

## Automated checks

`npm test` runs an axe-core structure check on the sign-in page, the payment page, the dashboard, an alert investigation and a case page. It found and led to fixes for unlabeled landmarks and a skipped heading level.

## Check by hand before the demo

- [ ] Use the whole customer flow with only the keyboard.
- [ ] Zoom the browser to 200%: nothing should be cut off.
- [ ] Open the customer app on a real phone (small screen, touch, the hold button).
- [ ] Turn on a screen reader (NVDA on Windows) and open the risk sheet once.
- [ ] Turn on "reduce motion" in the system settings: the score should appear without counting.
