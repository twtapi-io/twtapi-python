"""Endpoint resources, grouped by domain.

Each resource takes a `Transport` (sync) or `AsyncTransport` (async) and
exposes one method per HTTP endpoint, plus `*_iter` helpers for paginated
endpoints. Resources are dumb passthroughs — all retry / cookie / error
logic lives in the transport.
"""
