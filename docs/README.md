# Docs conventions

Reference files: Abstracted overview of the feature's state, flow, edge cases, and design ideas.
The log: A timestamped record of the reasoning and decisions

## Reference files (`{feature}.md`, e.g. `sentences.md`)

- One reference file per feature describing current state
- Code names (functions, tables, variables) verbatim as they appear in the code
- Includes planned work as `TODO`s
- Planned work link to a description under `Design ideas`
- Numbered lists for sequences, and bullets for unordered list
- Headings in sentence case. Bullets start capitalised unless it has specific casing

## The log (`log.md`)

- One file for all features in reverse chronological order
- One entry per decision: `### YYYY-MM-DD - {feature}: {title}`
- The body captures why the change was made and any rejected alternative worth noting
- Entries are often written before implementing, and the entry doubles as the implementation plan
- Once implemented, an `Outcome:` is added at the end of the record
- Amendments are added to keep the original reasoning intact with subsequent changes

## Workflow

Rough notes made in Notion, distilled in the log, then implemented, then append outcome, finally update the reference to reflect the changes
