# Dashboard index feature reference (current state)

## Frontend

- The page itself only composes HeroMetrics, ReviewsChart and WordsChart as self-contained components
- Each component is colocated in the parent folder, and each acts as a container with their own useQuery hook. They pass the specifically scoped data to a returned UI component
- The three components fetch independently
- HeroMetrics maps the wire shape onto named props (total_words to totalWords, words_reviewed to wordsReviewed), and HeroMetricsUI renders a tile per entry of its tiles array
- ReviewsChart renders daily reviews as a BarChart, and WordsChart renders the cumulative total as a LineChart, each inside a ResponsiveContainer
- Both hand the rows to Recharts untouched, which reads them by dataKey (series_date on the XAxis, against reviews or cum_words)
- Plot dates are formatted through formatSessionDate utility function

## Backend

For all endpoints, user_id is injected server side via decode_access_token and takes get_read_connection. Every count excludes 'skipped' and 'peeked', since progress metrics must be earned, as per [Principles](principles.md).

### GET /dashboard/hero-metrics

get_hero_metrics returns the user's lifetime totals under metrics as total_words (their introduced_words) and words_reviewed (their **earned** reviews).

- words_reviewed includes one count for each word in the sentence, rather than one review per sentence
- Every earned review is counted rather than every distinct word, so the same word reviewed twice counts twice

### GET /dashboard/review-chart-data

get_daily_reviews_bar_chart_data returns earned reviews per day over a fixed 30 day window ending today

- Combines both vocab and sentence reviews, where each word in a sentence counts as one review
- The date is derived by session start date, rather than the answered date

### GET /dashboard/word-chart-data

get_cumulative_word_chart_data returns the running total of the user's words per day, from before their first word up to today

- The series starts one day before their first word, so the line is zero indexed

## Open questions

- The dashboard needs to address what it shows when the user has no data
- How should the YAxis be shown - currently a value can only be read through tooltip
- Alignment between the two charts? Currently they show different time domains, and therefore don't line up. This can seem confusing. Perhaps they could at least originally line up on mount - or be fixed to sync together. Currently reviews chart is a fixed 30 day window, whereas the word chart is since their first result
- Staletime for the tanstack query
