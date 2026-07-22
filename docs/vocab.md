# Vocab feature reference (current state)

## Frontend

## Backend (POST /sentences)

## Edge cases

## Design ideas

### Add vocab control

- Similar to the sentence generation control in Sentences. Bounding the start has benefits:
  - Informs about the page/purpose of so the user understand the program better (ie algorithm automatically selects which word - either review word or a new work - based on their data, SRS etc. They just need to focus on what it throws at them and the algorithm handles the rest)
  - Hides the 'loading' transition which fetching from database - words could be fetched the moment the page mounts.
  - Provides scope for options. For example, this could address the session time open question [Open question time](#session-time-vs-no-time), [Open question known split](#session-known-vs-unknown-option)

## Open questions

### Session time vs no time?

- Should a vocab session be timed (e.g a 2 minute sprint), or should it be a free input/exploration thing. Without bounding it with time, it could feel too much like an open loop and get boring quickly. However, bounding it with time could feel too forced if someone wants to go at their own pressure. Perhaps the user could choose an option between time sprints vs untimed free - however, this will influence the data (such as response time). Perhaps this could be solved by storing which setting was used in the results - then the raw data is there to calculate with.

### Session known vs unknown option?

Should there be an option for a user to just cycle through words to review, or to only get new words? If only the algorithm can decide, then progress could feel too fast or too slow. There needs to be some way to calibrate or control this.

### User editing vocab vault

The user should be able to alter the data in their vocab vault - they should have full access to add or delete words, make assertions etc on confidence, and the algorithm adapts.
