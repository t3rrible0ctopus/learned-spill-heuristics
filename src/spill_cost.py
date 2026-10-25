def heuristic_spill_cost(feature):
    """Hand-designed baseline cost: high-use, long-lived values are expensive."""
    return (
        (feature["use_frequency"] + 1)
        * (feature["live_range_length"] + 1)
        / (feature["degree"] + 1)
    )
