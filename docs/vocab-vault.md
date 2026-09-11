# Vocab vault feature reference (current state)

## Frontend

- VocabVault only composes WordTable, which acts as the container with the data layer. It fetches through getWordEntries with useQuery and passes the rows to WordTableUI as the presentation layer
- WordTableUI returns early with a message when the list is empty, otherwise renders a row per entry with fields Target, Source, Times Reviewed, Avg Time/Syllable and Accuracy

## Backend

user_id injected server side via decode_access_token and get_read_connection

### GET /dashboard/words

get_word_table_data returns one row per word in the user's vault

- Currently shows all user_words since user_words are assumed to be words the user has seen at least one (still need to develop user_words insertions)
- times_reviewed excludes 'skipped' and 'cheated', a review must be earned as per principles
- av_s_per_syllable divides average response_time_ms by the character length of the target, so words of different lengths are comparable
- accuracy is 'correct_first_try' over **every** result, so skipping and cheating count against it rather than raising it

## Design Ideas

The user should be able to edit their vault by deleting words, or assert words they know as a prior for the algorithm

## Open questions

- How to organise - the whole vault is fetched and rendered in one unsorted table. There is no sorting/filtering/pagination
- Staletime for the tanstack query
