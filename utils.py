def format_elapsed(elapsed: float) -> str:
    """ Helper function for formatting the elapsed time in ms or s based on value

    Args:
        elapsed (float): Float of the elapsed time

    Returns:
        str: Formatted string with either time in ms or s
    """
    if elapsed < 1.0:
        ms = elapsed*1000
        return f"{ms:.3f} ms"
    else:
        return f"{elapsed:.3f} s"