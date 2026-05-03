"""Standalone MongoDB migration scripts (CLI ops tools, not part of the FastAPI request path).

Modules in this package are invoked manually (e.g.
`python -m app.migrations.dual_venue_indexes`) and exercised by tests; they are
intentionally NOT imported by app/main.py or any runtime route. Reachability
analysis from main.py will (correctly) flag them as unreachable — that's by design.
"""
