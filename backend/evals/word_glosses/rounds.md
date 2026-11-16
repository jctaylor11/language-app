# Word gloss prompt eval rounds

One row per round of the `eval-word-glosses` skill. Each round's prompt is saved as `rounds/round_NN_prompt.txt` and its per-entry results as `rounds/round_NN_results.json`.

- Score, primary, recall, must-not and unjudged describe the prompt in that round's snapshot
- Fixed and regressed compare against the previous round, so they show the effect of the previous row's change
- Change is the revision recommended from this round's failures. It is applied after the round, so the next row tests it

| Round | Date | Model | Score | Primary | Recall | Must-not | Unjudged | Fixed | Regressed | Change |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-11-14 | claude-haiku-5-5 | 91.2 | 95.1% | 84.4% | 7 | 6 | - | - | Collocation explanations only identify the sense: gloss the word itself, not the phrase or a verb that fits only its noun (idioms excepted) |
