# PROJECT_CONTEXT.md — Korean Language App

> Source of truth for what this project is, how it works, and where it stands.
> Last updated: 2026-06-10.

## 1. What is being built

An **intelligent vocab manager** for learning Korean. The thesis: mainstream language apps are bloated; this app strips learning down to the user's own vocabulary and uses an LLM/sentences corpus to put their specific vocab into context (sentences that match the vocab in their vocab vault (user_words)).

The cleverest structural idea is **corpus amortization**: every LLM-generated sentence is saved into a shared, user-agnostic corpus (`sentences` + `sentence_words` tables). Before calling the LLM, the app first serves sentences from the corpus that the user hasn't seen yet. As the corpus grows, LLM request volume — and cost — diminishes over time.

The core unique selling point is that the app captures per-response data — response time, correctness status, and keystroke patterns — and feeds it back to a scheduling engine to determine which words to surface next. Word selection is currently random; the scheduling engine (likely SRS-based, exact mechanism undecided) is not yet implemented. From the user's perspective the experience is intentionally simple: translate the words shown, and trust the system to optimise for them over time.

A key insight driving the eventual scheduler: a fast correct answer and a slow correct answer are not the same signal. Fast correct = consolidated knowledge. Slow correct = fragile knowledge. The scheduler will treat them differently — this is what separates the app conceptually from fixed-interval tools like Anki, where a correct answer always produces the same outcome regardless of how long it took.

### Goals and context

**Developer profile:** Python is the primary language and strongest technical layer; backend and data engineering is where depth is invested. Frontend is not strong, therefore leaning more on AI guidance. Calibrate accordingly — go deep on backend and data architecture, be more deliberate on frontend guidance.

The project is a deliberate dual-purpose bet by the developer (jctaylor11):

1. **Product path** — ship it, get real users, climb the active-users ladder to gain exposure and traction.
2. **Career path** — use it as the portfolio + narrative to land a tech role, positioning above "new grad".

Practical implication: shipping speed, user feedback, and portfolio-readiness matter as much as code polish. Avoid the engineer's trap of perfecting schema/code before validating demand.

**Plan order:** data modelling → dashboard → auth → get users. As of June 2026, data modelling is done done; **dashboard is the current milestone being worked towards**.

## 2. Core user flows

1. **Vocab flashcards** (`/` route): the user is shown a Korean word and types the English translation. Per-response data is captured: raw keystrokes, response time (ms), status (`correct_first_try` / `corrected` / `skipped` — skip via Esc/Tab), and position in the session. Answering correctly auto-advances; results post to the backend per word.
2. **Sentence practice** (`/sentences` route): "Generate Sentences" serves unseen corpus sentences or generates new ones via LLM. The user translates the Korean sentence; matching (case/punctuation-insensitive) auto-advances and records a `sentence_results` row (`correct` / `skipped`).
3. **Dashboard** (`/dashboard` route): As a starting point, this includes hero metrics (such as words answered, words practised, sentences completed, day streak), a GitHub-style activity heatmap (vocab answers per day), and a filterable/sortable per-word stats table, and a collapsible answered-sentences list.

## 3. Tech stack

| Layer    | Tech                                                                                                    |
| -------- | ------------------------------------------------------------------------------------------------------- |
| Backend  | Python, FastAPI, SQLAlchemy (raw SQL via `text()` mostly), uvicorn                                      |
| Database | PostgreSQL, migrations via Alembic                                                                      |
| LLM      | Anthropic API, `claude-haiku-4-5-20251001`, structured output via `messages.parse` into pydantic models |
| NLP      | `kiwipiepy` (Kiwi) Korean tokenizer for lemmatisation                                                   |
| Frontend | React + TypeScript, Vite, TanStack Query, React Router, Tailwind CSS v4                                 |

Python deps are **not pinned in any file** (no requirements.txt/pyproject.toml). Key packages: `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg2`, `alembic`, `anthropic`, `kiwipiepy`, `pydantic`, `python-dotenv`.

**Why not Next.js:** Next.js serves JS developers who want backend capabilities without learning a new language. Adopting it would abandon Python — the strongest layer — for the convenience of a single language.

## 4. Repository layout

```
language-app/
├── Makefile                  # `make dev` runs uvicorn + Vite concurrently
├── CLAUDE.md                 # Claude Code instructions (commands, architecture, gotchas)
├── .env                      # DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME + ANTHROPIC_API_KEY
├── backend/
│   ├── main.py               # FastAPI app + ALL endpoints
│   ├── config.py             # assembles DATABASE_URL from .env
│   ├── enums.py              # VocabResultStatus, SentenceResultStatus (stored as PG enums)
│   ├── llm.py                # generate_sentences() — Anthropic call, retry w/ backoff, returns 3 pairs
│   ├── lemmatiser.py         # extract_lemmas() — Korean sentence → citation/dictionary forms
│   ├── alembic/versions/     # 8 migrations (initial schema → sentence_results)
│   └── db/
│       ├── connection.py     # get_engine(), echo=True (all SQL logged to stdout)
│       ├── models.py         # ORM models = source of truth for Alembic autogenerate
│       └── seed_words.py     # seeds starter Korean vocab (NOT idempotent)
└── frontend/
    └── src/
        ├── main.tsx          # mounts app in QueryClientProvider
        ├── App.tsx           # routes: / → VocabSession, /sentences → SentenceSession, /dashboard → Dashboard
        ├── Layout.tsx        # nav + <Outlet/>
        ├── api.ts            # all fetch calls (BASE_URL = http://127.0.0.1:8000)
        ├── types.ts          # shared TS types incl. dashboard types
        ├── utils.ts          # calcIncorrectInput()
        ├── config.ts         # DEV_USER_ID = 1 (temporary until auth)
        └── pages/            # VocabSession.tsx, SentenceSession.tsx, Dashboard.tsx
```

## 5. Data model (PostgreSQL, see `backend/db/models.py`)

- **`words`** — global Korean vocab: `target` (Korean, citation form), `source` (English), `part_of_speech`.
- **`users`** — `username`, `created_at`. No auth yet; user 1 is the dev user.
- **`user_words`** — (user_id, word_id) composite PK; the user's personal vocab list, with `added_at`.
- **`sessions`** — `user_id`, `started_at`, `completed_at`. A "session" currently equals a browser tab (`sessionId` in sessionStorage). Only the vocab flow creates sessions; the sentence flow does not yet.
- **`vocab_results`** — one row per flashcard answer: `user_id`, `session_id`, `word_id`, `response_time_ms`, `answered_at`, `raw_keystrokes`, `status` (PG enum `result_status`: `correct_first_try`/`corrected`/`skipped`), `session_position`.
- **`sentences`** — the shared corpus: `target` (unique), `source`, `lemma_count`, `created_at`. **User-agnostic by design.**
- **`sentence_words`** — (sentence_id, word_id) mapping of which tracked vocab words appear in each sentence.
- **`sentence_results`** — one row per sentence the user answered: `user_id`, `sentence_id`, `session_id` (nullable — not wired yet), `status` (PG enum `sentence_result_status`: `correct`/`skipped`), `answered_at`.

History note: `vocab_results` was previously `session_results`; `sentence_results` replaced an earlier `user_sentences` table.

## 6. API endpoints (`backend/main.py`)

All take `user_id` as a query parameter (temporary, pre-auth).

| Endpoint                     | Purpose                                                          |
| ---------------------------- | ---------------------------------------------------------------- |
| `POST /sessions`             | Create a `sessions` row, return `session_id`                     |
| `GET /words`                 | Random batch of 5 of the user's words                            |
| `POST /vocab-results`        | Bulk-insert per-word answer rows; stamps `sessions.completed_at` |
| `GET /sentences?num_words=N` | The sentence pipeline (below)                                    |
| `POST /sentence-results`     | Record one answered sentence                                     |

### The `/sentences` pipeline (most involved flow)

1. Query the corpus for up to 50 sentences the user has **not** answered (`NOT EXISTS` against `sentence_results`). If more than 3 exist, return them — **no LLM call**.
2. Otherwise sample `num_words` random words from the user's vocab.
3. `generate_sentences()` → 3 Korean/English pairs from the LLM (count fixed in prompt regardless of `num_words`).
4. `extract_lemmas()` reduces each Korean sentence to citation forms (Korean is agglutinative — words appear conjugated with particles, but `words` stores citation forms; lemmatisation maps sentences back to known vocab).
5. Insert sentences (Core `insert(...).returning(...)`), map lemmas to `words.id` in one query (unknown lemmas dropped), insert `sentence_words` rows (`ON CONFLICT DO NOTHING`).

### The `/dashboard` endpoint

This is currently being worked on.

## 7. Frontend patterns

- **Rolling batches via `useInfiniteQuery`**: both session pages keep a queue of words/sentences and `fetchNextPage()` when ≤3 remain. `useInfiniteQuery` is chosen because refetches **append** rather than replace; `staleTime: Infinity` prevents background refetch mid-session.
- **Refs, not state, for telemetry**: keystrokes and word-shown time live in refs to avoid re-renders while typing.
- **Ordering for UX accuracy** (VocabSession): results are built _before_ `advanceWord()` (which resets the timer); `sendVocabResults` is awaited _after_ advancing so the UI stays responsive and timing stays accurate.
- `session_position` is a running ordinal persisted in `sessionStorage`.
- Dashboard: single `useQuery`, all filtering/sorting client-side (vocab list is small). Heatmap is plain Tailwind divs (53×7 grid, intensity bucketed relative to busiest day) — no chart library.
- Styling: minimal/Apple-like on the dashboard (white cards, hairline borders, `rounded-2xl`); Tailwind v4 via the `@tailwindcss/vite` plugin.

## 8. Dev workflow

```bash
make dev                                          # both servers
uvicorn backend.main:app --reload                 # backend only — RUN FROM PROJECT ROOT (imports are backend.*)
cd frontend && npm run dev                        # frontend only (localhost:5173)
alembic -c backend/alembic.ini revision --autogenerate -m "<slug>"   # edit db/models.py FIRST
alembic -c backend/alembic.ini upgrade head
python -m backend.db.seed_words                   # seed vocab (re-running duplicates)
cd frontend && npm run build && npm run lint      # tsc + vite build; eslint
```

Conventions:

- **Raw SQL first** — endpoints use `text()` with bound params; ORM models exist mainly for Alembic autogenerate. Schema changes = edit `models.py` **and** generate a migration.
- Comments explain _why_, not _how_ (deliberate style throughout).
- Conventional-commit-style messages (`feat:`, `refactor:`, `fix:`, `chore:`).

## 9. Current state (2026-06-10)

- **Working:** vocab flashcards with full response telemetry, sentence generation with corpus-first caching, sentence result tracking.
- **Dev data:** ~19 words in user 1's vocab, ~229 vocab answers; `sentence_results` is empty as of the dashboard build.
- **Data quirk:** some `response_time_ms` values are huge (minutes) — likely tabs left open mid-word. The dashboard shows them as-is; aggregation may eventually want outlier trimming.

## 10. Known gaps / roadmap

In rough priority order, after dashboard is complete:

1. **Auth** — the next planned milestone after dashboard is complete. `DEV_USER_ID = 1` is hardcoded in `frontend/src/config.ts` and passed as a query param everywhere; after auth, the backend should stop accepting `user_id` from the client entirely (noted in config.ts TODO).
1. **No tests at all** — biggest quick ROI; `extract_lemmas()` is a perfect pure-function first target.
1. **Debug output left in** — `print()`/`console.log` scattered, and `get_engine()` has `echo=True` (all SQL logged). Replace with real logging.
1. **README is one line** — CLAUDE.md / this file could seed a real one (matters for the portfolio goal).
1. **Sessions not wired to sentence flow** — `sentence_results.session_id` is always NULL; sentence page never creates a session.
1. **Minor tech debt:** mixed async/sync endpoints with blocking DB calls; `sendSentenceResult` is fire-and-forget with a race-condition TODO (batch + beacon on page close is the noted plan); `seed_words.py` not idempotent; one pre-existing lint error in `VocabSession.tsx` (`Date.now()` in a ref initializer, `react-hooks/purity`).

### Data and ML roadmap

The captured telemetry (response time, correctness, keystrokes, session position) is the foundation for a tiered analytics build-out:

**Tier 1 — SQL, buildable once sufficient data exists**

- Response time distribution per word per user
- Accuracy decay over time (forgetting curves)
- Error clustering — which words get confused with each other

**Tier 2 — ML with modest data**

- Personalised SRS: fit intervals per user per word (logistic regression to start)
- Next-word difficulty prediction: P(correct) given days since seen, historical accuracy, response time trend, session position
- Session fatigue modelling: accuracy and RT degradation within a session

**Tier 3 — with real user scale**

- Word embedding clustering for semantic grouping
- User segmentation by learning profile
- Dropout/churn prediction from session frequency signals
