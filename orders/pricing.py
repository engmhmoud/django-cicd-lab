BULK_THRESHOLD_CENTS = 10_000  # orders of 100.00 or more get the bulk discount
BULK_DISCOUNT_PERCENT = 10


def discount_cents(total_cents):
    """Bulk discount: 10% off orders of BULK_THRESHOLD_CENTS or more, rounded down to whole cents."""
    if total_cents >= BULK_THRESHOLD_CENTS:
        return total_cents * BULK_DISCOUNT_PERCENT // 100
    return 0
