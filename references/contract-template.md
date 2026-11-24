# <Project>: variant contract

Fill every <...>. Delete lines that do not apply. Agents follow this file exactly.

## What we are building
<one paragraph: product, audience, goal, what was wrong with the old version>
You are one of <N> agents working in parallel. There is NO review round after you:
you review and fix your own work before you finish.

## Your files
`variants/<NN-flow>/<V>/` where V is A, B, C (D, E... allowed).
- `NOTES.md` (required): line 1 = title, 3-6 words (shown on the square); lines 2-3 = what makes this variant different.
- Preview (required, one of): `preview.html`, `preview.png`, `preview.pdf`, `preview.md` ... (see below).
- `thumb.png` (required for anything visual): small screenshot of the variant, shown on its square in the picker. Command in the self-check below.
- Source files: <e.g. section.html + style.css + script.js | slide.html | component.tsx | draft.md>.
- Touch nothing outside your own flow folder. Never edit CONTRACT.md, facts.md, shared/, picks.json.

## Slot rules (so any variant drops in)
<web: root element carries data-v="<flow>-<V>" and id="<anchor>"; every CSS selector scoped under [data-v="<flow>-<V>"]; @keyframes prefixed <flow><V>-; JS wrapped in an IIFE that finds its root and returns if missing; no globals>
<deck: 1920x1080 slide, uses shared/deck.css master, fonts <...>>
<code: exports <interface>, no new dependencies, runnable with <command>>

## Shared base
<path to tokens / master / components and what they provide. Use them; do not redefine them.>

## Facts and copy
- `facts.md` is the only source for numbers, names, dates. Not in facts.md = do not claim it.
- Run the `humanizer` skill on all copy if it is installed. No em or en dashes. No hype words, no overclaims. <language>.

## Quality bar (self-review before you return)
- <Web: works at 360, 390, 768, 1024, 1366, 1920 px; no horizontal scroll; tap targets >= 44 px; reduced motion respected; keyboard and focus; alt text; IntersectionObserver to pause offscreen animation; lazy images; no innerHTML with untrusted data; rel=noopener.>
- <Deck: nothing overflows the slide; text readable at 50% zoom; one idea per slide.>
- <Code: tests/lint pass; no secrets; input validated at boundaries.>
- No external CDNs or trackers unless listed here: <...>.

## Self-check (run it, then look at the output)
`<build command>`, then screenshot your previews:
`google-chrome --headless=new --disable-gpu --hide-scrollbars --window-size=390,2400 --screenshot=<scratchpad>/<flow>-<V>-390.png http://127.0.0.1:<PORT the picker printed, not a guess>/<preview path>`
and again at 1440 wide. The picker server is already running on that port; do not start your own.
Last, after the fixes, write the square's thumbnail (720 x 540, the top of the desktop view) into your variant folder:
`google-chrome --headless=new --disable-gpu --hide-scrollbars --window-size=1440,1080 --force-device-scale-factor=0.5 --screenshot=<ABSOLUTE ROOT>/variants/<NN-flow>/<V>/thumb.png http://127.0.0.1:<PORT>/<preview path>`
<If the project build writes gallery.json: run the build once more after this, or the square stays without its picture.> Read the PNGs and fix what looks off. PDFs: `pdftoppm -r 60 -png`.
