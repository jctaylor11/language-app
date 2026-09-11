# Sentence vault feature reference (current state)

## Frontend

- SentenceVault only composes SentenceTable, which acts as the container - it fetches through getSentenceEntries with useQuery and passes the rows to SentenceTableUI
- SentenceTableUI renders a row per entry with fields Target and Source
- Designed as simple a record of sentences they have done, rather than a way to farm data

## Backend

user_id injected server side via decode_access_token and get_read_connection.

### GET /dashboard/sentences

get_sentences_table_data returns the sentences the user has results for

- Joins sentences to sentence_results on user_id - hence the sentence corpus is user-agnostic and it simply pulls the ones for that user

## Open questions

- Organisation - how should it be sorted/filtered/paginated
- Staletime for the tanstack query
