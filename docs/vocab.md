# Vocab feature reference (current state)

## Frontend

## Backend (GET /words, POST /vocab-results)

## Edge cases

## Design ideas

### Add vocab control

- Similar to the sentence generation control in Sentences. Bounding the start has benefits:
  - Informs about the page/purpose of so the user understand the program better (ie algorithm automatically selects which word - either review word or a new work - based on their data, SRS etc. They just need to focus on what it throws at them and the algorithm handles the rest)
  - Hides the 'loading' transition which fetching from database - words could be fetched the moment the page mounts.
  - Provides scope for options. [Open question known split](#session-known-vs-unknown-option)

### Assess response time with time-into-session

- It's possible the time into the session may influence the user's response - e.g rushing at the end to get more words in, or feeling fresh at the start to go faster. This data should be considered - and if there are negative patterns (e.g rushing at the end), could neglect this data.

### Clear 'Go again' CTA along with the session summary

- It's very easy to do just a 2 minute session, less easy to commit to a 10 minute session. However, someone who starts the 2 minutes is likely to continue - and they could do 10 minutes with 5x 2 minutes. Which also equate to 5 summaries (ie 5 rewards), which will likely keep them engaged.

## Open questions

### Session known vs unknown option?

Should there be an option for a user to just cycle through words to review, or to only get new words? If only the algorithm can decide, then progress could feel too fast or too slow. There needs to be some way to calibrate or control this.

### User editing vocab vault

The user should be able to alter the data in their vocab vault - they should have full access to add or delete words, make assertions etc on confidence, and the algorithm adapts.
