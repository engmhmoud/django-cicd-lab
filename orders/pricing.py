BULK_THRESHOLD_CENTS = 10_000  # orders of 100.00 or more get the bulk discount
BULK_DISCOUNT_PERCENT = 10


def discount_cents(total_cents):
    """Bulk discount: 10% off orders of BULK_THRESHOLD_CENTS or more, rounded down to whole cents."""
    if total_cents >= BULK_THRESHOLD_CENTS:
        return total_cents * BULK_DISCOUNT_PERCENT // 100
    return 0


TIERS_V2 = ((10_000, 10), (5_000, 5))  # pricing v2 (flag new_pricing): 5 % from 50.00, 10 % from 100.00


def discount_cents_v2(total_cents):
    """Tiered bulk discount, rounded down to whole cents."""
    for threshold, percent in TIERS_V2:
        if total_cents >= threshold:
            return total_cents * percent // 100
    return 0
