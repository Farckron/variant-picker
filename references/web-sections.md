# Websites: section variants assembled into one page

First used on a two-site event landing build: 14 flows, 44 variants, all agents back 38.5 minutes after launch.

## Layout
```
variants/<NN-flow>/<V>/section.html   root element: data-v="<flow>-<V>" + fixed anchor id
                       style.css      every selector under [data-v="<flow>-<V>"]
                       script.js      (() => { const root = document.querySelector('[data-v="..."]'); if (!root) return; ... })();
                       NOTES.md       line 1 title, lines 2-3 difference
shared/base.css                       tokens + utilities, loaded first on every page
picks.json                            written by the picker
build.py                              you write this (about 100 lines)
dist/                                 output, served by gallery.py <root> --on-pick "python3 build.py"
```

## build.py (write it per project)
1. `order = [flow keys in page order]`; `defaults[flow] = picks.get(flow)` if that variant exists, else the first one
   (this also covers a `"none"` pick). Runs again on every pick through `--on-pick`, so keep it fast and idempotent.
2. `page(picks, name)`: concatenate section.html bodies in order; concatenate CSS; wrap each script in
   `try { ... } catch (e) { console.error(tag, e) }`; write `dist/<name>.html/.css/.js`.
   Link CSS/JS with `?v=<sha1[:8]>` of their content (cache bust).
3. `page(defaults, "index")`, then for every flow and variant `page({**defaults, flow: v}, f"v-{flow}-{v}")`
   and append `document.querySelector('[data-v="<flow>-<v>"]')?.scrollIntoView()` so the preview opens on it.
   This is the in-context preview: the variant sits inside the current picks.
4. Write `<root>/gallery.json` with `href: "/dist/v-<flow>-<v>.html"` per card, plus
   `thumb: "/variants/<flow>/<v>/thumb.png"` when that file exists. The picker then shows the
   in-context previews instead of the raw folders.
5. Symlink `dist/assets -> ../assets`. Write files atomically (tmp + os.replace): agents build in parallel.
6. Placeholders like `{{OTHER_SITE_URL}}` replaced at build, with a `--prod` flag for real hostnames.

## Rules worth putting in the contract
- Production CSP `default-src 'self'`: no inline `<script>`, no `on*=` attributes, no CDNs. Inline `style=""` is fine.
- Only nav and hero may hold the `<h1>`.
- Video: `preload="none"`, poster, a 720p encode next to the 1080p, YouTube only as a click-to-load facade.
- Popups and modals: IntersectionObserver trigger, focus trap, Esc closes, iOS-safe scroll lock,
  always show on its own preview page (path contains `v-<flow>-`) so it can be judged.
- Images < 300 KB, WebP/JPG, `loading="lazy"` below the fold.

## Ship
Read picks.json, rebuild, screenshot index at 390 and 1440, check console for errors,
then deploy. Behind a CDN use content-hashed URLs and `Cache-Control: no-store` on authenticated HTML.
