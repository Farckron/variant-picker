---
name: variant-picker
description: Orchestrate a fast "many options, I pick" workflow. Split the work into flows (sections, slides, screens, components, copy blocks, API designs...), fan out one self-reviewing agent per flow that builds 3+ genuinely different variants, show them all as numbered squares (1A, 1B, 1C) in a local picker page where the user clicks to preview and picks, then assemble the picks. No judge or review round. Use when the user says variant-picker, "give me options", "several versions", "let me pick", "squares to choose from", "variants per section", or wants to iterate on a website, deck, UI, document or design by choosing rather than reviewing. Skip for small tasks with one obvious answer.
---

# Variant picker

The user decides by looking, not by reading reviews. Your job as orchestrator:
cut the work into flows, give every agent the same contract and facts, let each one
build several real alternatives and check its own work, then put everything in
front of the user as clickable squares. The user picks. You assemble. Repeat only
on what they picked.

Speed comes from three rules: **no judge round** (agents self-review), **facts
before fan-out** (no mid-run corrections), **one shared contract** (variants plug
in without merge work).

## Update first

Run this once per use, before anything else:

```bash
D=~/.claude/skills/variant-picker
if [ -d "$D/.git" ]; then
  old=$(git -C "$D" rev-parse HEAD)
  GIT_TERMINAL_PROMPT=0 git -C "$D" -c http.lowSpeedLimit=1 -c http.lowSpeedTime=10 pull --ff-only -q || echo "not updated, using the local version"
  [ "$old" = "$(git -C "$D" rev-parse HEAD)" ] || echo "updated: read SKILL.md again"
fi
```

If it prints `updated`, read SKILL.md again and follow the new version. If it fails (offline, local edits, pinned to
a tag), go on with what is there: no reset, stash or force. Skip it when the user asked not to update.

## 0. Gate

Use this only when there are 2+ independent parts with real design choices. One
function, one bug, one paragraph: just do it.

## 1. Intake (one round of questions)

Read the inputs first (folder, old version, docs, references). Then ask at most
8 short questions in one AskUserQuestion batch (4 per call, 2 calls max), only
about what you cannot infer: audience, must-keep and must-kill elements, hard
facts and claims, look-and-feel reference, target platform/sizes, deadline,
how many variants per flow (default 3, 4 for flows the user cares most about),
where it ships. Default everything else and state the defaults in one line.

## 2. Plan the flows

A flow = one independently swappable unit with a fixed slot. Examples:
- website: nav, hero, about, pricing, faq, footer, popup (one flow per section or user flow)
- deck: title, problem, solution, demo, numbers, ask (one flow per slide or act)
- app UI: onboarding, empty state, settings, checkout
- document or copy: headline set, intro, email subject lines
- code: API shape, data model, CLI UX (each variant = runnable demo or a short design note)

Number them in display order. Pick N variants per flow. Count agents:
flows + prep agents. Tell the user the count before launching. One agent per flow
up to 16 agents in total: invoking this skill is the opt-in to that scale. More
than 16: say the count and ask before launching.

## 3. Write the shared files (you, before any agent starts)

Pick the root: a work folder of its own, not the root of an existing repo. The
picker serves everything under it over HTTP, and 40+ variant folders do not belong
in `git status`. Start the picker server on it now (step 5), before any agent, and
take the port it prints: agents need the real URL for their self-check screenshots.

In that root:
- `CONTRACT.md` from [references/contract-template.md](references/contract-template.md):
  folder layout, slot and scoping rules, tokens or style base, preview format,
  quality bar, self-check command with the real picker port. This is the only
  thing that keeps the variants compatible, so be exact.
- `facts.md`: the only source for numbers, names, dates, claims. Each fact with
  its source. Add a "do NOT claim" list. If the facts need research, run a facts
  agent first and **wait for it** before fanning out.
- Shared base (design tokens CSS, slide master, component library) that every variant uses.
- The assembly step (see section 6) if it is cheap to write now, so agents can
  preview in context.

### Direction round (only when the user gave no look-and-feel reference)

The overall look is the biggest taste call, so the user picks that too. Do not
invent the shared base yourself. Before the fan-out run one agent on flow
`00-direction`: 3 variants, each a complete shared base (tokens, type, spacing, or
a slide master) plus one sample built on it (hero, title slide, one screen) as the
preview. Give the user the picker URL and wait for the pick. Copy the picked base
into the shared base, then fan out. `00-direction` is not part of the output:
leave it out of the assembly order.

Skip this round when the user named a reference site, a brand or an existing
design system: write the base from that.

## 4. Fan out

One agent per flow. Each prompt = shared context + the flow brief + "read
CONTRACT.md and facts.md first". Brief = what the flow must do, what to keep and
remove from the old version, and 3-4 concrete, genuinely different concepts
(layout, interaction, structure, tone), never colour swaps. Ask for a short
structured result: `{variants: [{v, title, summary}], known_issues}`.

Every agent self-reviews before it returns: builds, renders and looks at its own
previews (screenshots at phone and desktop widths, PDF page renders...), fixes
bugs, security problems, overflow and copy. Human-facing copy goes through the
`humanizer` skill if it is installed; no em or en dashes.

How to launch:
- **Workflow tool**: only if the user invoked this skill by name, said "ultracode",
  or asked for a workflow. Start from [references/workflow-template.js](references/workflow-template.js).
  Up to 16 agents (step 2).
- **Otherwise**: parallel Agent calls in one message, one per flow.
- Independent prep (web research, asset conversion) runs alongside. Anything
  the flows depend on (facts) runs first.

The picker is already running (step 3). The page polls, so squares appear as
variants land. Hand it over in the order given at the end of step 5.

## 5. Picker

```bash
python3 ~/.claude/skills/variant-picker/scripts/gallery.py <root> [port] [--on-pick "python3 build.py"]   # Bash run_in_background
```

It prints the real URL (falls back to a free port if the one asked for is taken).
Open `http://127.0.0.1:<port>/_pick/`. It lists `variants/<NN-flow>/<V>/` (NOTES.md
line 1 = square title, lines 2-3 = description) and iframes the variant's preview
file: `preview.html | index.html | preview.png/jpg/webp/svg/pdf/mp4 | preview.md/txt`.
A `thumb.png` (or jpg/webp) in the variant folder is shown on the square, so the
user sees every variant before clicking anything.
The number on a square comes from the `NN-` prefix, so keep the prefixes fixed
once agents start. A project build may instead write `<root>/gallery.json` (same
shape the scan returns: `{title, flows: [{n, flow, key, cards: [{id, v, title, desc, href, thumb}]}]}`)
with hrefs pointing at in-context previews. That file wins over the scan.
`--on-pick` reruns the build each time the picks change, so in-context previews
show the variant inside what the user has picked so far.

User clicks a square, switches Phone/Tablet/Laptop/Full, turns on Compare (or C)
to see every variant of the flow side by side, presses Pick (or P, again to
unpick), types notes. The page writes `<root>/picks.json`:

```json
{"picks": {"01-hero": "B", "03-pricing": "none"},
 "notes": {"1B": "bigger CTA", "03-pricing": "all too corporate", "*": "less text everywhere"}}
```

- pick `"none"` = the user rejected every variant of that flow: redo it.
- note keys: a card id (`1B`) is about that variant, a flow key is about the whole
  flow (why none fit), `*` is about everything.

Hand-over, in this order:
1. When the first variant has landed: headless screenshot of the picker and of
   one preview, read them, fix what looks broken.
2. Then give the user the localhost URL and the `file://` path of picks.json.
   They can start looking while the other agents finish.
3. When all agents have returned: one short list of their `known_issues` (flow,
   variant, issue), so a broken variant is not a surprise.

Never publish the picker anywhere (no Artifact tool, no tunnel) unless asked.

## 6. Assemble

When the user says they picked (or pastes picks): read `picks.json`, assemble the
final output from the picked variants (page, deck, document), apply the notes, run
one final check over the whole thing (build, render, screenshot, links, console
errors). A flow picked `"none"` or not picked at all is not final: assemble with
its first variant as a placeholder and say so. Assembly is project-specific; for
websites follow [references/web-sections.md](references/web-sections.md). Only
the website path has been run end to end; for decks, documents and code you write
the assembly yourself.

## 7. Iterate

Next round only touches flows the user flagged: a `"none"` pick, no pick, or a
note. Either revise the picked variant from its note, or fan out new variants for
that flow only (`D`, `E`...). Put what this round showed about the user's taste
into the new briefs: which concepts won across all flows, every note, the `*`
note. Keep the losers on disk until the user says it is final. Fix factual errors
in `facts.md` first, then grep all variants for the wrong claim.

When the user says it is final, stop the picker server (TaskStop on the
background task).

## Pitfalls seen in practice

- A wrong fact in the shared context spreads to every agent. Facts first, verified.
- Variants that differ only in colour waste the user's time. Demand different concepts.
- Agents editing shared files collide. Each owns only its flow folder.
- Browser cache shows stale previews. The picker server sends `no-store`; production builds need content hashes.
- Heavy media in previews (50 MB video) makes picking slow on phone. Ask agents for web-sized assets.
