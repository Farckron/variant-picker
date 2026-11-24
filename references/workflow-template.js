// Template for the Workflow tool. Copy, fill the CAPS parts, pass inline as `script`.
// Shape: facts (and optional research) first, then one agent per flow in parallel.
// No judge round: each flow agent self-reviews.
export const meta = {
  name: 'variant-picker',
  description: 'Facts first, then one self-reviewing agent per flow building N variants for the picker',
  phases: [
    { title: 'Prep', detail: 'facts sheet (+ optional research)' },
    { title: 'Variants', detail: 'one agent per flow, N variants each' },
  ],
}

const ROOT = 'ABSOLUTE_PROJECT_ROOT'
const SCRATCH = 'ABSOLUTE_SCRATCHPAD_DIR'

const CONTEXT = `PROJECT_PARAGRAPH: what it is, who it is for, what the user disliked about the old version, look-and-feel reference.
You are one of several agents working in parallel. There is NO review round after you: you review and fix your own work before you finish.`

const RULES = `Read ${ROOT}/CONTRACT.md first and follow it exactly. Facts: ${ROOT}/facts.md, the only source for numbers and claims.
Build variants that are genuinely different concepts (layout, structure, interaction, tone), not colour swaps. Each must be finished quality on its own.
Write copy yourself, then run the humanizer skill over it if it is installed (Skill tool, skill "humanizer"). No em or en dashes in visible text.
Finish by running the self-check from CONTRACT.md: build, render every preview (screenshots at 390 and 1440 wide, or PDF page renders) into ${SCRATCH}, read the images, fix what is off.`

const SCHEMA = {
  type: 'object',
  properties: {
    variants: { type: 'array', items: { type: 'object', properties: { v: { type: 'string' }, title: { type: 'string' }, summary: { type: 'string' } }, required: ['v', 'title', 'summary'] } },
    known_issues: { type: 'string' },
  },
  required: ['variants', 'known_issues'],
}

// key = folder name under variants/, n = variant count, brief = what the flow must do + 3-4 concrete concepts
const FLOWS = {
  '01-FLOW': { n: 3, brief: `BRIEF` },
  '02-FLOW': { n: 3, brief: `BRIEF` },
}

phase('Prep')
// Skip this agent if you already wrote facts.md yourself.
const facts = await agent(`${CONTEXT}

YOUR JOB: write ${ROOT}/facts.md, the single source of truth for numbers and claims. Read: SOURCE_PATHS.
Sections: basics, numbers (each with its source path), audience, things we must NOT claim (and why). Mark conflicts between sources. Bullets only.
Return a 10-line summary.`, { label: 'facts', phase: 'Prep' })

phase('Variants')
const results = await parallel(Object.entries(FLOWS).map(([key, spec]) => () =>
  agent(`${CONTEXT}

YOUR JOB: the "${key}" flow. Build ${spec.n} variants (${'ABCDEFG'.slice(0, spec.n).split('').join(', ')}) in ${ROOT}/variants/${key}/<V>/.

${spec.brief}

${RULES}

Return the variants you built (letter, title, one-line summary) and anything you could not fix.`,
    { label: `flow:${key}`, phase: 'Variants', schema: SCHEMA }).then(r => ({ key, r }))))

return { facts, flows: results.filter(Boolean).map(x => ({ flow: x.key, variants: x.r?.variants?.map(v => `${v.v}: ${v.title}`), issues: x.r?.known_issues })) }
