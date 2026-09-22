from datetime import timedelta, datetime

# Converts an ISO 8601 duration returned by the YouTube API (for example,
# "PT1H23M45S") into a Python timedelta object.
def parse_duration(duration_str):

    # The P and T characters describe the ISO 8601 format but do not hold a
    # numeric value, so remove them before reading each duration component.
    duration_str = duration_str.replace("P", "").replace("T", "")

    # Process the units in their expected order. `values` gives omitted units
    # a zero value; for example, "PT45S" has no days, hours, or minutes.
    components = ['D', 'H', 'M', 'S']
    values = {'D':0, 'H':0, 'M':0, 'S':0}

    for component in components:
        if component in duration_str:
            # Split off the number immediately before this unit and retain
            # the remaining units for the next pass through the loop.
            value, duration_str = duration_str.split(component)
            values[component] = int(value)
    
    # Build one standard duration value so callers can compare and convert it
    # without manually handling days, hours, minutes, and seconds.
    total_duration = timedelta(
        days = values['D'],
        hours = values['H'],
        minutes = values['M'],
        seconds = values['S']
    )

    return total_duration


# Normalizes one warehouse row after it has been read from the source data.
def transform_data(row):

    # Parse the source's ISO 8601 duration before replacing it in the row.
    duration_td = parse_duration(row["Duration"])

    # A timedelta has no time-of-day representation by itself. Adding it to
    # midnight and taking `.time()` produces a database-friendly time value.
    # datetime.min is the earliest time of the day - 00:00:00
    row["Duration"] = (datetime.min + duration_td).time()

    # YouTube classifies videos lasting 60 seconds or less as Shorts here.
    row["Video_Type"] = "Shorts" if duration_td.total_seconds() <= 60 else "Normal"

    # Return the same dictionary, now with normalized Duration and Video_Type.
    return row
