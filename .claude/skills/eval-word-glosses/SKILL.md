---
name: eval-word-glosses
description: Run rounds of the word gloss prompt eval. Each round generates glosses for the eval words, scores them against the answer key, has the gloss-prompt-analyst agent diagnose the failures and recommend a prompt revision, records the round in rounds.md, then applies the revision. Use when the user wants to run the word gloss eval or iterate on the gloss generation prompt. Runs one round unless a number is given.
argument-hint: "[number of rounds]"
---

# Eval word glosses

Runs rounds of the eval that optimises `SYSTEM_PROMPT` in `backend/db/seed/build_word_glosses.py`. The argument is the number of rounds. With no argument, run one.

Everything lives in `backend/evals/word_glosses/`:

- `eval_words.txt` and `answer_key.csv`: the words and what counts as right for each entry
- `score_word_glosses.py`: the deterministic scorer
- `rounds.md`: one row per round
- `rounds/round_NN_prompt.txt` and `rounds/round_NN_results.json`: each round's prompt and results

## Rules for every round

- **Never edit `answer_key.csv`, `eval_words.txt` or the scorer.** The key is the fixed target the rounds are measured against, so changing it mid-run makes the scores incomparable. When the analyst or the unjudged extras suggest the key is wrong, collect that and put it to the user at the end. Only the user approves a change to the key.
- **Never commit.** The snapshots are the only record of each round's prompt, which is why a snapshot is never overwritten.
- **Only `SYSTEM_PROMPT` changes.** Leave the rest of the generator alone, including the model and effort.
- Each generator run is a paid Batch API call and can take a while. Run it once per round, and don't rerun a round to get a better score.

## Before the first round

1. Check `WORDS_FILE_PATH` in the generator is `backend/evals/word_glosses/eval_words.txt`. If it is anything else, stop and tell the user, since `None` would generate all 5,400 words.
2. Work out the round number: one more than the highest `round_NN_prompt.txt` in `rounds/`, or 1 if there are none.
3. Note `GENERATION_MODEL` from the generator. The failures and errors files are named after it.

## One round

Run from the project root, in the `language-app` conda env.

1. **Generate.** Count the lines in `backend/db/seed/data/word_gloss_errors_{model}.jsonl` first (zero if it doesn't exist). Then run the generator in the background and wait for it to finish rather than polling:

   ```
   conda run -n language-app python -m backend.db.seed.build_word_glosses
   ```

   Its last lines give the path of the CSV it wrote and the words with invalid model output.

2. **Check the run was complete.** The raw results file is append-only and the last result per word wins, so a word whose request failed this round is silently scored on an earlier round's glosses. Stop the round and tell the user if `word_gloss_failures_{model}.txt` is not empty or the errors file has grown. Words listed as invalid model output are fine to continue with: they have no rows in the CSV, so they score zero, which is the correct result.

3. **Snapshot the prompt.**

   ```
   conda run -n language-app python -m backend.evals.word_glosses.snapshot_prompt N
   ```

4. **Score.**

   ```
   conda run -n language-app python -m backend.evals.word_glosses.score_word_glosses <generated csv> --round N
   ```

   This saves `rounds/round_NN_results.json` and prints the metrics, the failures, the unjudged extras, and the entries fixed and regressed since the previous round. If it raises because the key is invalid, stop and tell the user.

5. **Analyse.** Spawn the `gloss-prompt-analyst` agent. Give it the round number and the paths to this round's results JSON and prompt snapshot, `answer_key.csv` and `rounds.md`. It replies with the failure patterns, one recommended change as an `old_string` and `new_string` pair, and any key concerns.

6. **Check the change generalises** before accepting it:
   - `old_string` occurs exactly once in the current `SYSTEM_PROMPT`
   - `new_string` contains no word from `eval_words.txt`, and no gloss the key lists for the entries it is meant to fix
   - It is one change, stated as a rule or explanation that would apply to words outside the eval

   If it fails a check, send it back to the analyst once with the reason. If the second attempt also fails, or the analyst recommends no change, apply nothing and record that in the row.

7. **Record the round.** Append a row to `rounds.md` using the metrics from the results JSON:

   ```
   | N | YYYY-MM-DD | model | score | primary accuracy | tolerate recall | must-not hits | unjudged count | fixed | regressed | change |
   ```

   Fixed and regressed are the entry labels from the scorer (`word#entry_number`), or `-` when there are none or no previous round. Change is the analyst's one-line summary, or `No change` with the reason.

8. **Apply the change** to `SYSTEM_PROMPT` in `backend/db/seed/build_word_glosses.py` with a single edit. Do this after every round, including the last, so the working prompt is always the latest and the next run of this skill tests it.

Then start the next round if any remain.

## When the rounds are done

Report to the user:

- The rows added to `rounds.md`, and the score across the rounds
- The change applied after the final round, noting it is untested until the next run
- Every unjudged extra from each round, by entry. These are where gaps in the key show up, and the user decides which to promote
- The analyst's key concerns from each round, for the user to approve or reject

If a round was stopped early, say at which step and what was and wasn't written, so the user knows whether a snapshot or a row exists for it.
