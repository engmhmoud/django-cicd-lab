"""Every flag in the code base, with an owner and an expiry date (flag debt is inventory)."""

import datetime as dt

FLAGS = {
    "new_pricing": {
        "type": "release",  # release | experiment | ops | permission (Fowler's four toggle types)
        "owner": "orders-team",
        "expires": dt.date(2026, 12, 31),  # remove the flag and the old code path by then (a test enforces it)
        "description": "Tiered discount engine for quotes (pricing v2).",
    },
}
