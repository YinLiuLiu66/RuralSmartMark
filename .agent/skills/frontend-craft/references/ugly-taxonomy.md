# Seven Ugliness Tests

"Ugly" in an AI-built interface is usually one of seven failures. Each has a recognizable symptom, a structural cause, and rules that can be checked in code. Run them in order; the later ones are cheaper to fix but easier to notice.

## Triage

| The user says | Start with |
|---|---|
| "说不上哪里怪" | 1 Uncanny, 3 Detached |
| "点一下猜不到会发生什么" | 2 Unexpected |
| "字/数字挤出去，一屏放不下" | 4 Fragile |
| "信息都有，但找不到重点" | 5 Unorganized |
| "像两个产品拼的" | 6 Inconsistent |
| "就是不好看" | 7 Plain ugly |

## 1. Uncanny — violates learned habits

**Looks like.** Every element is familiar, yet the flow feels slightly wrong. Users pause, misclick, or ask why something is where it is.

**Cause.** Placement and behavior were chosen for visual balance, not platform habit. Familiar parts in an unfamiliar order.

**Rules.**

- **Numbers are right-aligned and tabular.** In tables and ledgers, labels go left, quantities and money go right. Use `font-variant-numeric: tabular-nums` and one fixed precision per column; format with `Intl.NumberFormat`, never by string concatenation.
- **Navigation answers "where did I come from".** Back sits top-left on mobile; browser back works on routed screens; a modal can be dismissed with Esc and the overlay unless the decision is destructive. Do not put a "返回" button at the bottom or make users hunt for a close affordance.
- **Destructive actions confirm only when data is lost**, and the message names the object and amount: `删除 7 月 30 日「采购支出 ¥3,608.00」？`. Use a destructive verb, a neutral cancel, and do not focus the destructive button by default.
- **Form submission lives at the end of the form.** On mobile it is a full-width primary button above the safe area. A top-right text action is acceptable on a settings screen with explicit save; if rows save immediately, omit it. Do not show both patterns on one screen.
- **Labels sit above fields, hints below, errors adjacent.** Validate on blur or submit, keep the user's input on error, and focus the first invalid field.
- **One primary action per screen.** Every other action is secondary (text, ghost, overflow). No primary button at both the top and bottom.
- **Feedback does not move the layout.** Toast or inline status for "已复制", inline text for validation. Do not use a modal to confirm success.
- **Do not fight the browser.** No `user-scalable=no`, no custom scroll containers around the whole page, no `100vh` on mobile (use `100dvh`), no disabled pinch zoom.
- **Time is local and legible.** Relative time ("3 分钟前") within a day, absolute date beyond; never an invented `MM/DD/YY` format when the locale is known.

```css
.num { text-align: right; font-variant-numeric: tabular-nums; }
```

## 2. Unexpected — control does not match the data

**Looks like.** Each step surprises. The user cannot predict what a control will do or what the next state will be, so they test the interface instead of using it.

**Cause.** The control was chosen by appearance, not by the data's cardinality, precision, frequency, or reversibility.

**Rules.**

- **Money and precise quantities use direct input.** A text field with `inputmode="decimal"` and a numeric keypad, formatted on blur. Use `type="text"` rather than `type="number"` (no scroll-wheel changes, consistent decimals), keep the raw value in state, and strip grouping before parsing so formatting never breaks the next save. Never `− 0 +` steppers or sliders for an amount.
- **Steppers are for small integer counts with a natural step** (quantity 1–9), and even then a direct input path stays available.
- **Dates use a date picker or segmented date input.** No free-text date with a custom format, no slider.
- **2–5 exhaustive options are visible** (segmented control or radios). **6–15** use a select. **More** use a searchable combobox. Do not hide three options in a dropdown or show forty chips.
- **Booleans follow effect:** a switch applies immediately (settings), a checkbox is included in a later submit (form). Choose per context and keep it across the app.
- **Sliders are for approximate ranges only**, with a visible current value, a sensible step, and a direct input fallback.
- **Every press gives feedback within 100 ms** (pressed state, then spinner). Success names the result ("已保存 3 条"); failure preserves input and offers retry. A silent click is a bug.
- **States are visible:** selected, expanded, disabled, loading, error. Hover is never the only cue; touch has no hover.
- **Navigation shape matches depth:** tabs for peer sections, a stack for drill-down, a dialog for a short focused subtask. A dialog that opens another dialog means the flow should be a page.

## 3. Detached — reinventing platform primitives

**Looks like.** A themed web page pasted inside a system app: a custom modal with the wrong radius, shadow, typography, and button order. It feels unofficial even when it works.

**Cause.** Platform primitives were rebuilt as `div`s, and no shared component layer carries the platform's behavior.

**Rules.**

- **Use native and accessible primitives.** `<dialog>` + `showModal()` for modals, `<details>` for disclosure, native `<select>`, the popover API where supported. On mobile, choices belong in a bottom action sheet and destructive confirmation in a platform alert or action sheet.
- **A dialog needs:** a labelled title, focus trap, Esc and overlay close (unless destructive), focus returned to the trigger, locked background scroll, and one primary action. More than two actions or a form with more than four fields belongs on a page.
- **Match the feedback channel to the weight of the event:** toast for confirmation that needs no decision, inline banner for errors that need one, dialog only for a blocking decision.
- **Loading matches the region.** Skeleton for content that is arriving, spinner inside the pressed button for an action, no full-screen branded loader for a fast request.
- **One icon family, one stroke width, one optical size.** No emoji as status icons in serious UI (`✅ ❌ ⚠️`), no hand-drawn system glyphs.
- **Respect platform chrome:** safe-area insets, status bar, keyboard avoidance, native scroll and overscroll. Do not fake an iOS or Android navigation bar.
- **Exception:** games, campaign pages, and immersive canvases may invent controls, provided every invented control still has a label, a visible focus state, and a keyboard path.

## 4. Fragile — content breaks the container

**Looks like.** Names clip at the card edge, the amount column jumps, long text overlaps a button, an empty state is a blank void, and the whole layout feels one record away from collapse.

**Cause.** The screen was designed with average data. No extremes entered the fixture, and containers were sized by their content instead of constraining it.

**Rules.**

- **Build a stress fixture before styling:** longest realistic name, 12-digit amount, 0 / 1 / 500 rows, three-line error, unbroken URL or email, CJK + Latin mix, 320px width, 200% zoom, and inputs at 16px minimum (prevents iOS auto-zoom).
- **Flex and grid children need `min-width: 0`.** Otherwise long content pushes the layout wider instead of wrapping.
- **Truncate only where the full value is recoverable.** A title may clamp with a tooltip or detail page; an order ID or amount may not silently disappear.
- **Lists reserve space:** two lines for the title, one for meta, stable row height while loading. Use `-webkit-line-clamp` or allow wrapping; do not let rows change height when data arrives.
- **Tables:** explicit column widths (`table-layout: fixed`), numeric columns right-aligned and `nowrap`, the name column wraps, and the wrapper scrolls horizontally instead of compressing cells below readable width.
- **Buttons:** at least 44×44px touch target; labels wrap to two lines or shorten; text never escapes the padding.
- **Cards:** set min-heights for header and meta, `aspect-ratio` for media, `object-fit: cover` for images with a background color.
- **Every data region designs four states:** loading, empty (with the next action), error (with retry and preserved input), and partial/extreme content. Empty is a state, not an absence of design.
- **Break only user-generated strings.** `overflow-wrap: anywhere` for names and URLs; do not `word-break: break-all` prose; `hyphens: auto` only with the right `lang`.
- **Viewport:** `min-height: 100dvh`, safe-area padding, no fixed content heights, no horizontal scroll at 320px.

```css
.row { display: grid; grid-template-columns: minmax(0, 1fr) auto; }
.name { overflow-wrap: anywhere; }
.amount { white-space: nowrap; font-variant-numeric: tabular-nums; }
```

## 5. Unorganized — every piece of information has equal weight

**Looks like.** Eight identical KPI cards, every field visible, no answer on the first screen. The user must read everything to find the one number that matters.

**Cause.** The data model drove the layout. The screen mirrors the schema instead of the user's decision.

**Rules.**

- **One lead value per screen**, at 1.8–2.5× the next type size. It answers the screen's question: today's net income, outstanding count, current balance.
- **Two to four supporting metrics** on one line, with the same period and unit. The rest goes under "详情" or a secondary tab.
- **Order is a narrative:** answer → change and context (delta, period, comparison) → breakdown → actions → metadata. Not alphabetical, not schema order, not "everything we have".
- **Use position and spacing before boxes.** A card per field is the most common AI tell. Group by decision, not by database table.
- **Progressive disclosure for rare or dangerous fields.** Advanced settings collapse; they do not disappear.
- **Dashboard rule:** eight metrics become one big, three small, and a link. A uniform 2×4 grid says "I had eight values" and nothing else.
- **Every chart answers a question**, with a labelled axis and unit, and a written takeaway. No decorative sparkline without values.
- **Zero data is not eight zeros.** Show the next action ("记第一笔") instead.

## 6. Inconsistent — each screen is its own product

**Looks like.** The same "save" is a top-right text link on one page and a bottom blue pill on another. Radii alternate between 4, 8, and 12. Icons mix filled and outlined. Each screen looks plausible alone and wrong together.

**Cause.** Screens were generated independently, with no shared primitives or tokens to constrain them.

**Rules.**

- **Tokens first.** CSS variables for color roles, type scale, spacing, radii, shadow, and focus ring. No raw hex or magic pixel value outside the token block. If the project already has tokens, extend them; do not fork a second set.
- **One Button, one Input, one Dialog, one Card.** Same action means the same component and the same label everywhere: "保存", not "保存修改" / "确定" / "提交" for one operation.
- **Placement is a rule, not a mood.** Settings either auto-save per row or use one explicit save; forms submit at the end; detail pages keep the primary action in a fixed bottom bar. Write the rule in the contract and follow it.
- **One icon family and one illustration style**, with consistent stroke, corner radius, and optical size.
- **Define state styles once:** hover, `:focus-visible` (a 2px ring with offset), active, disabled, loading. Do not restyle per screen.
- **A small rhythm:** two radii (control, container) and a 4/8-based spacing scale. Odd values need an optical reason and a token.
- **Two screens that need the same thing: extract the component before styling the second.** Duplication is where inconsistency is born.

## 7. Plain ugly — no design system

**Looks like.** A purple-to-blue gradient header, five accent colors, gray text on gray, 12px body copy, content hugging the viewport edge. The interface is working and still looks cheap.

**Cause.** No design system. Decoration is doing the work that hierarchy should have done.

**Rules.**

- **Palette:** one neutral ramp (6–8 steps), one accent, and semantic colors (success, warning, danger). At most two saturated colors visible at once. Accent marks primary actions, selection, and focus — nothing else.
- **No default gradient.** If a gradient is genuinely required, keep it same-hue, low-contrast, and tokenized. Ban the indigo-to-purple "AI gradient" unless the brand owns it.
- **Contrast:** body text at least 4.5:1, large text at least 3:1. Placeholder text is not a label. Never gray-on-gray for essential data.
- **Type:** one family, at most three sizes per screen (for example 13 / 15 / 24), line-height 1.4–1.6, measure around 70 characters. No centered paragraphs longer than two lines. Tabular numerals for all data.
- **Spacing:** 4/8 scale; section gap 24–32; page padding 16–24 on mobile and 24–48 on desktop. Content does not touch the viewport edge.
- **Borders and shadows:** one hairline plus spacing beats nested cards; one shadow level, low opacity, single light direction.
- **Density:** rows 48–56px, targets 44px, at least 8px between adjacent targets.
- **Motion:** 150–250ms ease-out for state changes, no animation for layout jumps, respect `prefers-reduced-motion`, no gratuitous bounce.
- **Imagery:** real content or a neutral placeholder; no emoji as primary iconography, no clip-art, no random stock photo that fights the product's tone.

## Quick substitutions

| Instead of | Do |
|---|---|
| `128.5`, `9320.15`, `45` in one column, left-aligned | One precision, right-aligned, tabular numerals |
| `− 0 +` for money | `inputmode="decimal"` field, formatted on blur |
| Custom `<div>` modal | Native `<dialog>` or a platform action sheet |
| Fixed card width with a clipped name | Two-line clamp or wrap, amount `nowrap`, `min-width: 0` |
| Eight same-size KPI cards | One lead value + three support metrics + details |
| Save link top-right on one screen, pill at the bottom on another | One placement rule per screen type |
| Indigo-purple gradient header and five accents | Neutral surface, one accent, semantic colors |
| Emoji status icons | One icon family with text labels |
| Full-screen spinner for a button action | Spinner inside the button |
| 12px gray body text | 15–16px text at 4.5:1 contrast |

## Boundaries

- **Product consistency beats platform convention inside an existing product.** If the product deliberately uses a custom modal, match it; do not introduce a native one on a single screen.
- **Density is not ugliness when the job demands it.** Trading, spreadsheet, and ops tools may use 32px rows, as long as alignment and hierarchy hold.
- **Brand and requested styles bend the palette rules**, not the robustness rules. A brutalist or playful page still needs contrast, focus states, and overflow handling.
- **Stay in scope.** Fix the screen in front of you; note unrelated drift instead of refactoring the app around it.
