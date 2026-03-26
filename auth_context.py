import contextvars

# This creates an async-safe variable to hold our incoming token per-request.
# It ensures User A's token never accidentally leaks into User B's request.
sf_token_var = contextvars.ContextVar("sf_token", default=None)