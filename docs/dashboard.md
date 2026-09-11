# Dashboard feature reference (current state)

The dashboard is the read-only view over the user's data. Each page has its own reference doc:

- [Overview](dashboard-index.md)
- [Vocab Vault](vocab-vault.md)
- [Sentence Vault](sentence-vault.md)
- [Session Log](session-log.md)

## Routing

- `/dashboard` is a layout route rendering DashboardLayout inside ProtectedRoute, with the pages as children
- The two session-log paths render the same page, so an expanded session is addressable by URL rather than state

## Frontend

- DashboardLayout renders a fixed sidebar from a module-level links array with Outlet for the active page
- Pages only compose components - they hold no data, state, or logic themselves
- The components are colocated with the pages. Each component contains its own data layer, and passes the specifically scoped data to a UI component as props

## Backend

All dashboard endpoints live in `routers/dashboard.py`, take get_read_connection, and inject user_id server side via decode_access_token. The client is never trusted. Computation is done in SQL, and the service function returns plain dicts under a single named key.
