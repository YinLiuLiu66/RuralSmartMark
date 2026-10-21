# Design Contract and Starter Kit

The contract makes the invisible decisions visible before generated code hardens around them. Keep it short: six lines and a token set, not a specification document.

## The six-line contract

Write this in the task notes or at the top of the implementation file. If the user did not say, choose a sane default and mark it as an assumption.

```
Platform / surface:  mobile web, iOS-first / desktop admin / ...
User job:            record an expense in under 15 seconds / ...
Primary action:      save / create / confirm / ...
Lead value:          the one number or state this screen answers with
States:              loading / empty / error / partial / extreme content
Borrowed patterns:   numeric keypad, segmented control, native date picker,
                     confirm dialog, bottom action sheet, toast, ...
```

Then add, in one line: **Out of scope** — what this screen deliberately does not do. It prevents half-built orphan controls.

### Worked example

```
Platform / surface:  mobile web, iOS-first; quick-entry form
User job:            record one expense in under 15 seconds
Primary action:      save the entry
Lead value:          amount (large, first focus)
States:              default, invalid amount, saving, network error (keep input),
                     success (toast, reset the form)
Borrowed patterns:   native decimal keypad, segmented payment method,
                     native date picker, inline validation, fixed bottom CTA
Out of scope:        editing history, deleting entries, receipts
```

What this contract already decides, before any CSS:

- no `− 0 +` stepper for the amount; direct input with `inputmode="decimal"`
- category choices are a scrollable chip row only if they are few; otherwise a searchable picker
- date defaults to today and opens a picker
- the save button is fixed at the bottom and disabled only while invalid or saving
- deletion belongs to the detail screen, not here
- the success state is a toast plus a reset, not a dialog

## Token starter

Use only what the screen needs; delete unused roles rather than leaving dead variables. If the project has tokens, map these roles onto the existing names and stop.

```css
:root {
  color-scheme: light;

  /* color roles */
  --bg: #f7f7f5;
  --surface: #ffffff;
  --surface-2: #f1f1ee;
  --text: #1a1a18;
  --text-muted: #6b6b66;
  --text-faint: #9a9a94; /* non-essential only; fails body contrast */
  --border: #e3e3de;
  --border-strong: #8c8c86; /* 3:1 against surface for control edges */
  --primary: #1f6f4a; /* also carries success in this green-accent starter */
  --primary-hover: #185a3c;
  --primary-weak: #e6f1eb;
  --danger: #b3261e;
  --danger-weak: #fbeae8;
  --warning: #8a5a00;
  --focus: #1f6f4a;

  /* type */
  --font-sans: ui-sans-serif, system-ui, -apple-system, "Segoe UI",
    "PingFang SC", "Noto Sans CJK SC", sans-serif;
  --text-xs: 12px;
  --text-sm: 13px;
  --text-md: 15px; /* form input text stays 16px to avoid iOS zoom */
  --text-lg: 20px;
  --text-xl: 28px;
  --text-2xl: 40px;
  --leading-tight: 1.2;
  --leading-body: 1.55;

  /* space: 4px base */
  --s-1: 4px;
  --s-2: 8px;
  --s-3: 12px;
  --s-4: 16px;
  --s-6: 24px;
  --s-8: 32px;
  --s-12: 48px;

  /* radius: two, not five */
  --r-control: 10px;
  --r-card: 14px;
  --r-pill: 999px;

  /* elevation: one direction, one level */
  --shadow-1: 0 1px 2px rgb(0 0 0 / 0.06), 0 1px 3px rgb(0 0 0 / 0.08);
  --shadow-2: 0 8px 24px rgb(0 0 0 / 0.12);

  /* interaction */
  --ring: 0 0 0 3px color-mix(in srgb, var(--focus) 30%, transparent);
  --ease: cubic-bezier(0.2, 0.7, 0.2, 1);
  --dur: 180ms;
}
```

Rules of use:

- Components reference roles (`var(--text-muted)`), never raw hex.
- With Tailwind or a component library, map these roles onto its theme/config; do not hand-roll a parallel token set.
- Dark mode remaps the roles under `[data-theme="dark"]` or `prefers-color-scheme`; no filter inversion.
- Numbers use `font-variant-numeric: tabular-nums`, not a special "number font".
- Focus uses `outline: none` only when `--ring` or an equivalent visible style replaces it.
- If the brand accent fails contrast, add a darker shade for text and keep the brand color for fills. Do not shrink text to make it "less visible".

## State matrix

Fill the cells that this screen actually owns. A blank cell is a decision, not an oversight.

| Region | Loading | Empty | Error | Extreme content |
|---|---|---|---|---|
| List | 3 skeleton rows, same height as real rows | "还没有记录" + the primary next step | Inline banner + retry, keep filters | 2-line name clamp, stable row height |
| Detail | Skeleton for title + 3 fields | "记录不存在" + back | Banner + retry, keep cached view | Long notes wrap; amount steps down one size instead of clipping |
| Form | Submit disabled only while saving | Not applicable | Field-level + summary, preserve input | 320px width, keyboard open, 200% zoom |
| Dashboard metric | Placeholder block, no layout shift | "记第一笔" instead of zeros | Stale-data timestamp + retry | 8 metrics collapse to 1 + 3 + link |
| Media | `aspect-ratio` box + shimmer | Neutral placeholder | Broken-image fallback | `object-fit: cover`, reserved space |

## Control selection

| Need | Use | Avoid |
|---|---|---|
| Exact money or decimal quantity | Text input, `inputmode="decimal"`, format on blur | Stepper, slider |
| Small integer count with a natural step | Direct input, optional stepper | Stepper alone |
| 2–5 exhaustive options | Segmented control or radios | Dropdown |
| 6–15 options | Select | Wall of chips |
| Many options, search needed | Combobox with filter | Long dropdown |
| Date or time | Native picker; segmented presets for ranges | Free-text date |
| Boolean, immediate effect | Switch | Checkbox |
| Boolean, submitted with form | Checkbox | Switch |
| Transient confirmation | Toast | Dialog |
| Irreversible deletion | Confirm naming the object | Generic "确定吗？" |
| Short focused subtask | Dialog or a page | Nested dialogs |
| Multi-step flow | Stepper with progress, back, resume | One long form with hidden required fields |

## Platform deltas

- **iOS:** back chevron top-left plus swipe-back; choices in an action sheet; destructive confirmation in an alert; tab bar at the bottom; safe-area insets; 44pt targets; large titles only at the root of a stack.
- **Android:** system back gesture and top app bar; Material dialog or bottom sheet; 48dp targets; a FAB only for the single create action of the screen.
- **Mobile web:** `100dvh`, safe-area padding, inputs at least 16px, correct `inputmode`/`autocomplete`, tap highlight, keyboard avoidance, hover only as an enhancement.
- **Desktop web:** visible focus, logical tab order, hover states, max content width (do not stretch a form to 1600px), sticky table headers for long lists.

## Scope dial

| | Prototype | Production |
|---|---|---|
| Contract | Six lines | Six lines + out of scope + success criteria |
| Tokens | 6–8 core roles | Full roles, dark mode, states |
| States | Default + one failure | Full matrix |
| Verification | One target width | 375 / 768 / 1440, zoom, keyboard |
| Components | Inline | Extract after the second use |

Scale up only when the user asks for production quality or the screen is going into a real product. A prototype still needs the seven tests; it does not need every state documented.
