# Session log feature reference (current state)

## Frontend

- SessionLog composes the SessionLogTable component, which fetches its own session log data through getSessionLog on mount with useQuery
- SessionLogTable passes that data, the expanded session number, and toggleSession to SessionLogTableUI, which returns a table with fields Date, Type, Total Reviewed, preceded by an unlabelled index column holding session_number, and loops through the session log data to render each session as a row with the respective fields
- Each row can be clicked to expand a session summary, and which row is expanded is derived from URL rather than state to keep the session addressable
- Clicking the row passes that row's session_number to toggleSession which navigates to the corresponding session's URL
- The expanded session number is pulled from the URL using useParams with the corresponding sessionNumber parameter defined in App.tsx route paths
- When looping through the session logs in the table, if the entry.session_number matches the number in the URL (saved as expandedSessionNumber), the SessionOverview component renders
- SessionOverview is passed that row's session_id, not its number - each row holds both, so the URL can reference the number while the request still uses the ID
- SessionOverview extracted as a component to enable useQuery, which pulls the overview data on mount and passes the targets to SessionOverviewUI

## Backend (GET /sessions/log, GET /sessions/overview/{session_id})

### GET /sessions/log

1. user_id is injected server side via decode_access_token
2. get_session_log_data UNION ALLs vocab_results and sentence_results in the session_log CTE, excluding skipped and peeked and grouped by session, so one row is returned per session whichever table it came from. Only completed sessions (non-NULL completed_at) are included
3. Selects session_id, started_at, session_type, total_reviewed count, and session_number from ROW_NUMBER() window function ordered oldest first - numbered after the filter, so only completed sessions are counted
4. Ordered by session_number descending (newest first) and returned as session_log

### GET /sessions/overview/{session_id}

1. user_id is injected from decode_access_token, session_id comes from the URL path to filter results
2. get_session_overview_data UNION ALLs the target from vocab and sentences, excluding skipped items
3. Returns the vocab and sentences targets under the same dict key as session_overview

## Design Ideas

- Add a link in the session overview that navigates the user to a page which displays more in depth data on each session. Note - as in [Decision Log](log.md#2026-08-19---session-log-expanded-session-query-string-should-be-session-number-not-session-id) this may require sequential queries to get the session ID from the session number, if not already in cache (e.g direct hit or refresh)
