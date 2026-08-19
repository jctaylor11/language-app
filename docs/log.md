### 2026-08-18 - session log: session overview is one endpoint unioning both results tables

The expanded row shows what was done in a session, however a session is either vocab or sentences which sit in different tables. I decided on a single endpoint with one query that UNION ALLs which combines the vocab and sentences, which both have the `target` column, albeit of different type (words vs sentences). Since both branches have effectively the same column, nulls are not needed, and since sentences and vocab are mutually exclusive for one session, each session maps to only one.

Rejected alternatives:

- Two separate endpoints conditioned on type, with type passed in as a prop. However, this creates redundancy with two endpoints and adds more moving parts with the parameters. Not clean design.
- A conditional inside the endpoint which triggers one of two queries. Makes the frontend cleaner, but requires a roundtrip server side to know which query to run.
- Conditional inside JOINed table with CASE WHEN on the session type. However the multiple JOIN and CASE syntax is less readable than a UNION ALL with two easily readable branches, and returns null for session with no results rather than dropping them

Outcome: Implemented.

### 2026-08-15 - sessions table: add a column specifically for session type

Previously the type was inferred by the bounds (bound my time is a vocab session, bound by count was a sentence session). I decided to change it to an explicit column in the table for the type, which removes its dependency.

Rejected alternative: Infer session type from the bound type. Having it dependent on the bound type value makes it fragile to future decisions, and may seem confusing later seeing conditionals on the bound type to label the session type in the sessions log.

Outcome: Implemented.

### 2026-08-14 - session log: specific sessions can be fetched as a route

The specific session date (for example, the words pertaining to a certain session) are valuable to see, but of a different granularity to the table of the sessions themselves. As per the previous decision also, it would not be helpful to include these on the session page itself. Therefore, each session has its own dedicated page where the session details create the fetch route and page. This also makes the data predicatable in terms of where it can be found (e.g editing the url directly). It is also suitable having it own page, given it gives room for extra data and future decisions regarding what data is helpful to be displayed.

Rejected alternatives: Dropdown list or floating component. However this confines how much information can be usefully displayed, and makes it more difficult to find the session contents themselves if they are not addressable with their own route and page as one would first have to load and look through the sessions list.

Amendment 2026-08-17: A summary of the details expand into a row in the log table rather than a separate page, while also updating the URL. The user then has an option to click to see a more advanced view which takes them to another page. This keeps the addressability mentioned above with the `session-log/:sessionId` route, and keeps the log in view to move between sessions rather than getting redirected.

### 2026-08-14 - session log: dashboard page added for sessions

It's important that the user can see more granular progress build over time aside from just aggregated metrics, such as total words and total reviewed. This can be achieved with a session log, which displays all the session they have done over time.

Rejected alternative: It was considered to have a log show the date, followed by the contents of each session for that day, with a divider between sessions. In this way, there would be all of the words/sentences done in each session, in order of their session position, with a divider with each new session. This was rejected due to scale - for example, 5 sessions a day (10 minutes) with 50 words per session would be 7,500 words in a month. There is no useful way to organise this data, and deeper pages would never been seen. It would get unwiedly. It's therefore better to abstract each session into just one.

Outcome: Implemented.

### 2026-08-12 - sentences: session completed_at time is updated each flush

Every time a result is input, the completed_at time for the respective session is updated with the current time. By updating on insert, the last update remains accurate as the completed time since nothing overwrites it afterwards. This same pattern applies in vocab. It catches sessions that may have been interrupted, and bases it on the final insert rather than making any assumptions as in the rejected alternatives.

Rejected alternative: Assuming the done time based on when the timer is reached, or once a sentence count is reached.

Outcome: Implemented.

### 2026-08-12 - sentences: summary screen is only the total words reviewed

The main purpose of the sentences session is to review words in context, while the main purpose of vocab is both review and new word exploration. Therefore, though vocab shows both new words and word exploration, the summary for the sentences session is only the total words reviewed.

One of the main purposes of this summary screen also is for psychology: They divide session such to close the loop for each session, they provide immediate feedback, and show visible progress through the metrics.

Outcome: Implemented.

### 2026-08-12 - sentences: sentence session is five correct sentences

A sentence session is a fixed number of sentences submitted, as decided in [Decision Log](log.md#2026-08-02---sessions-vocab-sessions-are-bound-by-time-sentences-are-bound-by-count). Skipped sentences don't count towards the five since it's 'any five sentences', rather than any specific five. Five was chosen since the commitment is small, similar to two minutes for vocab. A session of ten sentences feels like more a commitment, whereas a user can simply do ten sentences over two sessions.

Outcome: Implemented.

### 2026-08-11 - vocab: score incremented and displayed for each non-skipped word answered

A score universally increments one for every non-skipped word, and is saved client-side rather than dependent on server side. Decided to keep it client-side to make feedback immediate and low latency (rather than waiting for a request to round trip), and it decouples it from any batching logic for sending results. The tradeoff is that a failed POST will cause the summary to disagree with the live running score, though this is unlikely, and unlikely to be noticed given it occurs on another screen. If it happens to occur often, I can add a retry.

Incrementing client side is different logic to the final summary score, which is fetched from the server, since it's acceptable for a slight delay in loading the summary, combines external data (e.g new word calculation), and is more important to be faithful than the live on-screen running count.

Outcome: Implemented.

### 2026-08-10 - vocab: word index advances at the end of a session

Since the words list is held in cache, when another session starts (after timer expires) the same queued words are shown to the user. Previously, this would mean that the final (not-done) word as the timer expired from the previous session is shown to the user as the first word on the next session. It was changed to advance the word onFinish as the timer expires so the last word is not shown as the first. Two main reasons: If the user has already seen the word, they would have already subconsciously thought of it, therefore the first word is systematically faster than usual. Additionally, it could feel as though the next session is just a continuation, which could make each session feel less like a 'closed loop' and lower session integrity.

Outcome: Implemented.

### 2026-08-10 - vocab: results are sent through useMutation so in-flight flushes are observable

Results were sent with an awaited fetch inside the event handler, and therefore was not possible for anything else to see if the promise had been resolved. Since the summary query fires immediately as the timer ends, it could beat the last query to the database and therefore undercount the metrics. This is especially the case that users could be rushing to get the last word in. Decided to change it to go through useMutation, which records each flush in the shared mutation cache. This can be accessed by useIsMutating, so that SessionSummary gates its query on the number of in-flight requests being 0.

Outcome: Implemented.

### 2026-08-08 - vocab: summary results count the same word seen twice as two reviews

The 'total reviews' metric for that session is simply a count for the number of words reviewed in that session, whether they are repeated or not. It excludes words that have been skipped, since they get totally ignored. This is better than the rejected alternative of making it count only the distinct words reviewed in that session, and therefore double as a way for user's to gauge their relative overall speed of churning through words. However, for the 'new words' metric, it only counts distinct words to represent the new words that have been added to their vault from that session.

Outcome: Implemented.

### 2026-08-08 - vocab: summary data is pulled from database at end of session

At the end of the session, the frontend requests the words that have actually been added to their database in that session. This allows data outside of the session to be considered (e.g all their known words) so metrics like new words that session can be determined, as well as metrics relative to previous session (for example, "up x% since last week" style metrics). It also maintains data integrity by pulling from the source of truth, rather than assuming

Rejected alternative: Building and storing the data client-side. However, this wouldn't allow comparisons to see which words are new.

Outcome: Implemented.

### 2026-08-07 - vocab: custom timer built with timestamps instead of third party timer package

Decided to build my own custom timer using setInterval and the useEffect hook dependent on the sessionStartTime updating. Rejected the alternative of using the established react-timer-hook since it would add a dependency without adding value. It additionally does not abstract away logic keeping everything understood, there are no unnecessary imports, and the edge cases it would resolve are handled (e.g drift) since it's a function of timestamps.

Outcome: Implemented.

### 2026-08-07 - vocab: timer takes sessionStart time as a prop and derives countdown from this

Decided to strictly calculate all time related variables as a function of timestamps (current and session start time) by passing the sessionStart as a prop. The rejected alternative was to deduct 1 from the countdown timer on every iteration of the setInterval's 1000ms interval. This would seem to deliver the same result, but could drift such that 120 seconds becomes longer than 120 seconds since it does not guarantee precise intervals, execution is not guaranteed to run on schedule (e.g main thread may be busy), throttling etc.

Outcome: Implemented.

### 2026-08-07 - vocab: onSuccess used for all logic to start the session

Previously a startSession function was called when the user clicked the start button. This would handle all the start game logic (e.g mutation to fetch session, session position counter, timer, first word shown time). However, this could cause drift - for example, if the mutation failed the other functions would still run. Therefore it was changed that button would call the mutation, and the startSession logic was moved to the onSuccess handler of the useMutation hook.

Outcome: Implemented.

### 2026-08-05 - vocab: session does not persist over refreshes

The user refreshing the page most likely implies they are wanting to restart the session. Therefore the session should not be saved in sessionStorage - it should be closed, ready for a new one to start on click. The session can therefore just be set and stored with useMutation hook - the state is required so updates cause a re-render, and removing session storage means it will not persist through a refresh.

Outcome: Implemented.

### 2026-08-02 - vocab: summary provided at the end of the session

The summary screen closes the psychological loop and is the feedback from the session which serves as the 'reward' - especially considering Mihaly Csikszentmihalyi emphasises the immediate feedback is necessary for engagement and deep work/flow. The summary screen should feel like a reward - visible progress, words added, some sort of metric added.

### 2026-08-02 - vocab: vocab session kept only at 2 minutes

A user wanting to do 10 minutes can easily do 5x 2 minute sessions. In doing so, they get 5x rewards, and are likely to stay engaged and build a habit. Rewards stay proportional to effort input. On the contrary, if someone can select their timer, and chooses 10 minutes - they could get bored and leave early, and the habit breaks. It also makes sessions comparable - sessions of different lengths aren't necessarily equal. There will be a clear CTA in the summary for the user to seamlessly repeat the session if they want longer.

Rejected alternatives:

- Letting the user choose the session length. This adds friction at exactly the point where inertia to start should be removed, and sessions of different lengths are no longer comparable.

Updates:

- When I was doing mental maths training, I found it almost addictive to do since

Outcome: Implemented.

### 2026-08-02 - sessions: vocab sessions are bound by time, sentences are bound by count

I think vocab and sentence sessions need a defined start and finish to close the loop psychologically, with feedback shown at the end (e.g result summary). Closing the loop makes effort and reward feel connected. If you complete something and there's no acknowledgement, the brain doesn't get a clean signal that the work is done - the effort feels like it disappeared, and a habit isn't likely to develop. This bounding will define a 'session' - and therefore changes the current definition of 'session' from a browser tab, to a bound and measured session.

- Vocab session bound by time:
  - Lowers activation energy to get started as there is no uncertainty with the user's commitment. It's a lot easier to commit to doing 2 minutes, than it is to do 40 words, even if the two are ultimately the same.
  - Response time data is less likely to be influenced: the user is more likely to go at their natural pace since their session time is fixed. Hence also, the UI should not encourage time pressure (e.g countdown should not be obvious. It should still exist to track time - just not as a central component to compete against). It's possible the user may rush near the end of the session, though this is detectable since time-into-session is derivable from vocab_results.answered_at and sessions.started_at - [design idea](vocab.md#assess-response-time-with-time-into-session)
  - Releases a progress metric regarding words done per session on the dashboard - this way the user more-so sees progress from time investment, rather than time saved from time investment (e.g "34 words in 2 minutes, up from 26 last week" is more rewarding than something like "2 minutes for 30 words, down from 3 minutes last week").

- Sentences bound by count:
  - Sentences are less-so something to bash through, and instead take ones time with and internalise the vocab/review any unknown words and piece together the grammar. The most rewarding metric also from sentences is seeing the review count increase rapidly since multiple words are seen at once.
  - Sentence generation costs, therefore less churn is more cost effective, and setting count targets makes each one more likely to be valued by the user.

Consequences:

- Definition of session changes from an active browser tab to a session bound by time/count.
- Migration required to add bound_type and bound_value as a column in sessions table.
- The sentence flow must start creating sessions. SentenceResult.session_id is currently nullable and no session row is ever created in the sentences path - a bound run of sentences is now a session, so insert_session applies there too.
- completed_at changes meaning. It is currently re-stamped on every result flush, so it holds 'last activity' rather than 'finished'. It should now be set when the bound is reached, which also requires distinguishing a completed session from one the user abandoned early (otherwise the two are indistinguishable in every dashboard metric).

Rejected alternatives:

- Unbounding session: Considered that timed session could feel too forced if someone wants to go at their own pace without pressure. However, the closed loop/feedback/reward seems necessary to maintain engagement.

### 2026-08-01 - sentences: queued sentence in frontend get sent in payload to sentences API

When finding eligible sentences, the SQL query first looks at sentences in the cachewhich contain a target percentage of known words from the user's word vault and excludes the sentences they've already done by looking at the user's sentence results. The eligible sentences are then queued in the frontend. As the user works through the sentences, another batched is refetched when then remaining sentences in the queue hit a threshold number (e.g 3 remaining). The sentences in the queue will not be in the sentence results, and therefore the refetch could still select these queued sentences. In doing so, the user would see the same sentence twice. Therefore, the payload for the fetchSentencePairs client API must be changed to send the IDs of sentences which are in the queue, and these will be excluded in the cache path query when fetching sentences.

Outcome: Implemented.

### 2026-07-31 - sentences: filter generated sentences based on known percent request using same cache query, after generated sentences are cached

The LLM is unrealiable, especailly since it only sees a sample of known words rather than the full thing. The generated sentences therefore cannot be returned directly, and they must be evaluated deterministically. More sentences than required are therefore generated and the eligible ones are returned. Since the generated sentences are processed and added to the sentences cache with their words mapped in sentence_words table, the same cache path that previously returned no results (calling get_eligible_sentences) will now surface the generated sentences (assuming they are eligible). This same function therefore serves as an evaluation to filter the eligible sentences, which keeps the sentence eligibility logic in one place, and keeping the vocab in the SQL.

Consequences: The connection to the function was changed from read_conn to write_conn, since it must be the same connection as the one that writes the generated sentences to the database - since the transaction is only committed when the endpoint returns.

Rejected alternatives:

- A dedicated function that would count the proportion of known lemmas, taking the user's full vocab vault into consideration. This would create two different implementations of the same rule, and would require all vocab to be queried from the database and compared in python.

Outcome: Implemented.

### 2026-07-31 - sentences: generation prompt keeps a sampled vocabulary

The generation prompt only sees a sample of the user's words, while the eligibility check measures the known proportion against all of their user_words. The LLM fills the rest of each sentence from general Korean, and some of those words will happen to be ones the user already knows, so actual coverage lands at or above the requested percentage. As the user's vault grows,the number of chance of general collision colliding with user words outside of the sample increases, especailly at the low end of the slider (e.g 0-20% known requested). Generating words a user does not know requires knowing which words they do know, which the LLM does not have a complete picture of. The solution to this is an open question, with considerations in [design ideas](sentences.md#known-percent-band-accuracy-for-generated-sentences)

The rejected consideration was to add more context by sending the full vocabulary in the prompt. This is not viable since it increases cost and reduces instruction adherence since. LLMs (especially cheap and fast models) are not optimised for counting and selectively focus attention (e.g they'll ingore words at the end of the list). Design consideration for resolving this are in [Known percent band accuracy for generated sentences](sentences.md#known-percent-band-accuracy-for-generated-sentences).

### 2026-07-28 - sentences: generation slider input kept as integer

Generation target percentage is kept as an integer instead of a float and evaluated as integers (by multuiplying by 100 instead of dividing). This avoids floating point imprecision when adding/substracting the bounds, which would cause proportions to be incorrectly evaluated. For example, a lower bound of 0.7 would be marginally higher with the floating point imprecision, and therefore a sentence with 70% known lemmas would return false (e.g 0.700000000 < 0.700000001).

Outcome: Implemented.

### 2026-07-28 - sentences: generation slider shifts inwards

At the extreme ends of the slider, e.g at 100% known words in the generated sentence, the bounds should slide inwards so that that lower bound is -20, instead of -10 (since the upper bound cannot +10 to 110%). By making it shift inwards by another 10 it keeps the band constant at 20%. The rejected alternative was to truncate the band, but this would make the width inconsistent.

Outcome: Implemented.

### 2026-07-23 - dashboard: add page to display sentences seen by user

All sentences seen by the user are displayed in the Sentence Vault page of the dashboard. Sentences are currently not shown again once they're already seen, and sentence accuracy/time data isn't their purpose - vocab is the main driver of data, whereas sentences are just intended as a way to review those individual vocab words in context (with 'comprehensible input'). Therefore this page just serves as a collection/reference of sentences the user should be familiar with, rather than for any analysis, and there is no real need to display anything more than the sentences themselves. Possibly 'answered_at' field could be added though.

Outcome: Implemented.

### 2026-07-21 - sentences: control slider has wide step

The step for the slider for proportion of known words for the sentence generation has a wide step of 20 due to precision. Anything lower would imply more precision of what we can gaurantee. A tolerance of ±10% seems feasible. 20 was also chosen since it covers 80% - which research suggests is the optimal percentage for comprehensible input.
Update: Step changed to 10, band set to 20. The band slider of width 20% dropped the 80% midpoint, and setting a step of 10 now restores it.

Outcome: Implemented.

### 2026-07-19 - sentences: sentence cache path as single query

I can just keep the fetching applicable user words and searching for eligible sentences all to just one SQL query. This also works better to keep everything in the database, remove a moving part, and the match runs as a hash join instead of passing a list of keys (more efficient than two queries, one to fetch, and searching with that list). The query look something like this:

1. A CTE that contains all the of the user's words - (user_words where user_id = :user_id)
2. JOIN sentences + sentence_words + user_words: There will be one row per (sentence, matched word from user_words CTE)
3. WHERE to filter for the NOT EXISTS in the user’s current sentences
4. COUNT the rows, aggregated by sentence ID (ie, it will collapse sentence ID and show a count for how many user_words matched up with sentence_words for that table)
5. `HAVING COUNT(*) >= 0.8 * s.lemma_count` - this avoids division to avoid division by zero error and integer division, and filters for sentences with over threshold proportion of known words

Outcome: Implemented.

### 2026-07-19 - sentences: cache search uses all user words

The cache search should not take a certain number of words. I should take as many words as are applicable and then use that to search the cache for any sentences. To start, I will take ALL the words in their user_words. Later, I can whittle it down weighted by whatever the algorithm I build considers are the best words to be reviewed by the user.

However, I should still constrain the user words for the sentence generation path, since it is unnecessary to pass excessive words and costs credits for the API.

Outcome: Implemented.
