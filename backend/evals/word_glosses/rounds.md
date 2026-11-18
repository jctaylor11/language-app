# Word gloss prompt eval rounds

One row per round of the `eval-word-glosses` skill. Each round's prompt is saved as `rounds/round_NN_prompt.txt` and its per-entry results as `rounds/round_NN_results.json`.

- Score, primary, recall, must-not and unjudged describe the prompt in that round's snapshot
- Fixed and regressed compare against the previous round, so they show the effect of the previous row's change
- Second key revision after round 4 (rounds 1-4 re-scored): 인사#1 acceptable "notable figure"; 저#3 and 올#2 must-tolerate dropped as redundant with sibling entries; 예쁘다#1 must-not "lovely"
- Rounds 1-3 were re-scored on 2026-11-16 against the revised key (17 entries changed: unjudged extras promoted or added to must-not, and must-tolerate words that are not exact equivalents dropped), so their scores are comparable with each other but not with earlier numbers
- Change is the revision recommended from this round's failures. It is applied after the round, so the next row tests it

| Round | Date | Model | Score | Primary | Recall | Must-not | Unjudged | Fixed | Regressed | Change |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-11-14 | claude-haiku-5-5 | 92.5 | 95.1% | 92.0% | 7 | 6 | - | - | Collocation explanations only identify the sense: gloss the word itself, not the phrase or a verb that fits only its noun (idioms excepted) |
| 2 | 2026-11-16 | claude-haiku-5-5 | 94.1 | 95.9% | 90.7% | 4 | 0 | 달다#1, 쓰다#2, 쓰다#3, 묻다#3, 뜨다#3 | 네#2, 남#2, 치다#4, 인사#3, 양#3 | State the other side of the tolerated-list trade-off: a correct synonym left out also marks the learner wrong, so list every interchangeable word and the one-word form of a multi-word primary |
| 3 | 2026-11-16 | claude-haiku-5-5 | 89.8 | 94.3% | 89.3% | 11 | 1 | 배#1, 치다#2, 인사#3, 양#3, 약#1 | 하다#1, 시원하다#1, 달다#3, 배#3, 쓰다#2, 이르다#2, 정말#3, 연기#2, 맞다#3, 철#2, 전#3 | Revert round 2's "leaving out a true equivalent costs too" sentence: it added near-miss and unjudged tolerated words (must-not 4 to 8, unjudged 2 to 8) with no recall gain |
| 4 | 2026-11-16 | claude-haiku-5-5 | 94.4 | 96.7% | 92.0% | 4 | 0 | 하다#1, 시원하다#1, 달다#3, 배#3, 이르다#2, 정말#3, 연기#2, 맞다#3, 철#2, 올#2 | 맞다#2, 양#2, 약#1 | Add a swap test to the tolerated-list rule (replace the primary with the candidate in the sentences where the learner meets the word; if the meaning changes it is broader, narrower or related), so overlapping general words are not listed as synonyms |
| 5 | 2026-11-16 | claude-haiku-5-5 | 91.1 | 94.3% | 86.7% | 7 | 1 | 맞다#2, 양#2, 약#1, 전#3 | 시원하다#1, 타다#3, 달다#1, 달다#3, 남#1, 늦다#2, 쓰다#3, 이르다#1, 이르다#2, 올#2, 전#2 | Tighten the swap test to use the plainest everyday sentences that use the primary in this sense, not sentences picked to suit the candidate, so candidates that fit only some uses are dropped |
