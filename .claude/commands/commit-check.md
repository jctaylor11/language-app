Check the current git diff and recent commit history (`git log --oneline -10`).

- Is this a good stage to commit?
- Are there any obvious errors I should fix.

For it be ready:

- There must not be any obvious errors that should be fixed
- It must be a good stage to commit, without a more obvious stage in sight

Also cross-reference `docs/`:

- Identify which `docs/{feature}.md` reference file(s) cover the changed files (match by feature area, e.g. `sentence.py`/`SentenceSession.tsx` → `docs/sentences.md`)
- Read the relevant reference doc(s) and flag anything the diff now contradicts (stated current state, flow, or an edge case that's no longer true)
- If the diff looks decision-worthy (a new design choice, a rejected alternative, a non-obvious tradeoff) rather than routine, flag if `docs/log.md` doesn't have a matching entry — per `docs/README.md`, entries are normally written before implementing
- Check if any updates to the docs are sound and appropriate

Respond concisely. Output format:

- Ready: [yes/no]
- Issues: [list any issues, or "none"]
- Docs: [contradiction(s)/missing log entry flagged, or "none"]
- Commit: [message, or "not ready"]

Must not elaborate on "none". The commit message should be in the same style as my recent commit history.
