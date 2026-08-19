# Session log feature reference (current state)

## Frontend

- SessionLog fetches session log data through getSessionLog on page mount with useQuery and returns the SessionLogTable component with the log data passed in as a prop
- SessionLogTable returns a table with fields Date, Type, Total Reviewed, and loops through the session log data to render each session as a row with the respective fields
- Each row can be clicked to expand a session summary, and which row is expanded is derived from URL rather than state to keep the session addressable
- Clicking the row passes that row's sessionId to toggleSession which navigates to the corresponding session's URL
- The expanded sessionId is pulled from the URL using useParams with the corresponding sessionId parameter defined in App.tsx route paths
- When looping through the session logs in the table, if the entry.session_id matches the clicked sessionId (saved as expandedSessionId), the SessionOverview component renders
- SessionOverview extracted as a component to enable useQuery, which pulls and returns the overview data on mount

## Backend (GET /sessions/log, GET /sessions/overview/{session_id})

### GET /sessions/log

1. user_id is injected server side via decode_access_token
2. get_session_log_data UNION ALLs vocab_results and sentence_results, excluding skipped and grouped by session, so one row is returned per session whichever table it came from
3. Selects session_id, started_at, session_type, and total_reviewed count
4. Ordered by newest first, then session_id, and returned as session_log

### GET /sessions/overview/{session_id}

1. user_id is injected from decode_access_token, session_id comes from the URL path to filter results
2. get_session_overview_data UNION ALLs the target from vocab and sentences, excluding skipped items
3. Returns the vocab and sentences targets under the same dict key as session_overview
