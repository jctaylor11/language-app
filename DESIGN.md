---
name: Sanggi
description: Light, calm, hairline-built UI for a Korean vocabulary typing app. One accent colour, no gradients, no emoji.
colors:
  canvas: "#ffffff"          # page and card ground
  surface-muted: "#f7f7f5"   # tiles, revealed-answer fill, expanded rows, row hover
  surface-sunken: "#efefec"  # progress track, sidebar hover
  line: "#e7e7e3"            # 1px decorative dividers only
  line-control: "#8a8a84"    # 1px edge of controls, resting chart bars (3:1)
  ink: "#0f0f0e"             # primary text, numbers, primary button fill
  ink-muted: "#55554f"       # secondary text, table headers, inactive nav
  ink-subtle: "#6b6b65"      # mono labels, chart ticks
  accent: "#1d4fe0"          # the one accent
  accent-hover: "#153ec0"
  on-accent: "#ffffff"
colors-dark:                 # not designed yet; apply via data-theme="dark" when it is
  canvas: "#101110"
  surface-muted: "#161715"
  surface-sunken: "#1f201e"
  line: "#272826"
  line-control: "#74756f"
  ink: "#f3f3f0"
  ink-muted: "#a9aaa4"
  ink-subtle: "#92938d"
  accent: "#7b9dff"
  accent-hover: "#9bb5ff"
  on-accent: "#0a0e1c"
typography:                  # weight size/line-height family
  display: "600 56/60 sans"       # never inside a session
  title: "600 36/42 sans"
  heading: "600 24/32 sans"
  subheading: "500 18/28 sans"
  body: "400 15/24 sans"
  body-strong: "500 15/24 sans"
  small: "400 13/20 sans"
  eyebrow: "500 12/16 mono"
  data: "400 13/20 mono"       # tabular figures
  prompt-word: "500 48/60 ko"
  prompt-sentence: "500 28/42 ko"
  answer: "400 24/32 sans"
  timer: "500 20/28 mono"      # tabular figures
  stat: "600 40/44 sans"       # tabular figures
fonts:
  sans: 'Geist, "Noto Sans KR", system-ui, sans-serif'      # 400/500/600
  mono: 'Geist Mono, ui-monospace, "SF Mono", Menlo, monospace'  # 400/500
  ko: '"Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'  # 400/500, always lang="ko"
spacing: { 1: 4px, 2: 8px, 3: 12px, 4: 16px, 5: 24px, 6: 32px, 7: 48px, 8: 64px, 9: 96px }
radii: { sm: 3px, md: 6px, lg: 10px }   # sm chart bars, md buttons/sidebar items, lg tiles and answer field
sizes:
  control-md: 36px
  control-lg: 44px          # Start, New session, sign-in
  answer: 64px              # answer field height
  measure-session: 640px
  measure-page: 1120px
  sidebar: 240px
shadows:
  popover: "0 0 0 1px rgba(15,15,14,0.06), 0 8px 24px -8px rgba(15,15,14,0.12)"  # chart tooltips only
  focus: "0 0 0 2px #ffffff, 0 0 0 4px #1d4fe0"                                    # keyboard focus ring
---

# Sanggi design system

Read this before any UI work. Use the tokens above; never hard-code hex values, sizes or fonts. Add no copy, features, states or decoration that are not described here or in the product. If something is missing, ask.

## Feel

Light, airy, sharp, focused. Structure comes from 1px hairlines and quiet fills, not colour or shadow. One accent does the work. Data is the decoration: no imagery, no illustrations, no emoji, no gradients. If a screen feels full, remove something.

## How the app behaves (design must not contradict this)

- The user types the English meaning of a Korean word or sentence. The answer is checked on **every keypress**; a match advances to the next word automatically.
- **No submit button, no "correct"/"incorrect" state, no error styling, no feedback copy.** Wrong or partial input looks like any other typing.
- Tab skips. Holding Esc reveals the accepted answers (joined with " / ") for as long as it is held.
- Vocab session: 2 minutes, timer and score top right. Sentence session: five sentences with a progress indicator.
- Skipped and peeked words never count towards progress metrics.

## Colour

- `canvas` ground with `ink` text. `surface-muted` is the only second ground.
- Exactly one accent. Use it on only a few elements per screen: answer-field edge, header rule, progress fill, Start / New session fills, the latest bar and the line in charts. Never a second hue, a red or a green.
- Text colour: `ink` primary and numbers, `ink-muted` headers/labels/inactive nav, `ink-subtle` mono labels and ticks. Never body text in the accent.
- Contrast: text 4.5:1, control edges / focus rings / chart marks 3:1.

## Type

- Geist for interface and English, Noto Sans KR for all Korean (`lang="ko"`), Geist Mono for labels, timer, chart ticks and table numbers. Tabular figures on numbers.
- Korean is always the largest text on a session screen.

## Shape and state

- Dividers 1px `line`. Control edges 1px `line-control`. Radii only 3 / 6 / 10px.
- No shadows except chart tooltips. Focus is the `focus` ring on every interactive element; the answer field shows focus as a 2px accent edge.
- Hover changes a fill (`surface-muted` / `surface-sunken`) or darkens ink/accent. Disabled is 40% opacity. Active sidebar item is ink on `surface-muted`.
- Motion: 120ms colour changes only.

## Layout

- Session: one centred column, max `measure-session` (640px), generous space above the prompt.
- Dashboard: fixed 240px sidebar, page column max 1120px, 32px between sections.
- App nav (every screen except a running session): 64px tall, 32px side padding, 1px `line` rule along the bottom. "Sanggi" wordmark left; links right, 4px apart. Links are `body`, `control-md` (36px) tall, 12px side padding, `radius-md`; `ink-muted` at rest, `ink` on `surface-muted` on hover and for the current page. "Log out" is a link-styled button with no current state. Hidden in focus mode.
- Icons: only two 16px chevrons (right, down) for expanding session-log rows, 1.5px stroke, `currentColor`. No logo file; "Sanggi" is plain type, 18px weight 600.

## Screens

### Vocab session (designed; this is the source of truth)

Desktop 1280x720, light theme. Header bar: timer and score right-aligned (mono, `timer` style; timer `ink`, score `ink-muted`, score is a bare number with no label), 32px padding, 2px `accent` rule along the bottom edge. Centred column below: Korean word (`prompt-word`), 48px gap, answer field (64px tall, `radius-lg`, 2px accent edge in all states, text `answer`, centred), 48px gap, key hint in `small`: "Tab to skip" and "Hold Esc to reveal the answer" with key names in mono `ink`, 24px apart. Layout never shifts between states.

| State | Input shows | Input fill |
| --- | --- | --- |
| Default | empty | `canvas` |
| Typing | typed text | `canvas` |
| Esc held | accepted answers joined with " / " | `surface-muted` |

A running session is in **focus mode**: the app nav is hidden and the page padding removed, so only the header bar and the column remain (the header rule spans the full width). There is no exit control yet; refreshing is the exit. The session summary shows the nav again.

Mockup values: word 사과, timer 1:48, score 5 are samples.

### Before session (designed)

Not a focused screen: the default app nav shows, and there is no session header, timer or accent rule. The centred column is the same. A bold line (24px, weight 600): "Type the English meaning of each Korean word." Below it, a full-width control styled like the answer field (2px accent edge, `ink-muted` text) reading "Press any key to start", then the same key hint. The first key press starts the session, and the screen becomes the Default state above, in focus mode.

### Not designed yet

Sentence session, session summary, dashboard (overview, vault tables, session log), login, landing, dark theme. Build these from the rules and tokens above and the component intents below; do not invent beyond them.

- **Session summary:** words reviewed, new words, a New session button (accent fill).
- **Overview:** two metric tiles (`surface-muted`, `radius-lg`, mono eyebrow label above a `stat` number: words learned, words reviewed), a bar chart of daily reviews over 30 days (grey bars, latest day accent), a line chart of cumulative words (one accent line). Charts ship a hidden data table.
- **Tables (vaults, session log):** hairline-ruled rows, no cards, `ink-muted` headers, mono numeric cells, rows may expand (session log).
- **Sentence progress:** a 2px segmented rule, five segments, accent fill.
- **Login:** Google sign-in only; needs Google's own button asset.

## Known deviations and open points

- The mockup sets the accent twice on session screens (answer edge and header rule). This is a deliberate exception to "a few elements".
- The 2px header rule was chosen over a 1px variant. It can read as a progress bar on a timed screen; consider shrinking it with the countdown or using 1px.
- The mockup's revealed state uses a `surface-muted` fill with the accent edge. This overrides the older component note that described an ink edge.
- "Press any key to start" replaces the Start button the app currently has. Implementing it means changing `VocabStart` behaviour, not only styling.
- The app nav spec (see Layout) was proposed without a mockup. Review it visually and adjust.
- Focus mode has no way out mid-session. An exit control (with confirm and timer pause) is to be designed.
- The current app shows the answer in the word card as a dev aid; this is removed at launch and is not part of the design.
