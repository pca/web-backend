from datetime import timedelta

DNF = -1
DNS = -2
NO_RESULT = 0

# Events with Average of 5 calculation
Ao5_EVENTS = [
    "333",
    "222",
    "444",
    "555",
    "333oh",
    "clock",
    "minx",
    "pyram",
    "skewb",
    "sq1",
]


def parse_time(value):
    data = []
    time = timedelta(seconds=value)
    total_seconds = time.seconds
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        data.append(f"{hours:d}")
    if minutes:
        data.append(f"{minutes:d}")
    if seconds:
        if time.microseconds:
            microseconds = f"{int(time.microseconds/10000):02}"
        else:
            microseconds = "00"
        if minutes:
            data.append(f"{seconds:02d}.{microseconds}")
        else:
            data.append(f"{seconds:d}.{microseconds}")
    elif time.microseconds:
        if minutes:
            data.append(f"00.{int(time.microseconds/10000)}")
        else:
            data.append(f"0.{int(time.microseconds/10000)}")

    return ":".join(data)


def parse_value(value, format, rank_type="best"):
    if value == DNF:
        return "DNF"
    if value == DNS:
        return "DNS"
    if value == NO_RESULT:
        return None

    if format == "time":
        return parse_time(value / 100)

    if format == "number":
        if rank_type == "average":
            return f"{value/100}"
        else:
            return f"{value}"

    if format == "multi":
        value = str(value)

        # New format
        if len(value) == 9:
            difference = 99 - int(value[0:2])
            seconds = int(value[2:7]) if value[2:7] != "99999" else None
            missed = int(value[7:])
            solved = difference + missed
            total = solved + missed

            if seconds:
                time = parse_time(seconds / 1)

            return f"{time}; {solved} solved, {missed} missed, {total} total"

        # Old format
        if len(value) == 10 and value[0] == "1":
            solved = 99 - int(value[1:3])
            total = int(value[3:5])
            seconds = int(value[2:7]) if value[2:7] != "99999" else None

            if seconds:
                time = parse_time(seconds / 100)

            return f"{time}; {solved} solved, {total} total"


def parse_solves(result, rank_type):
    if (
        rank_type == "average"
        and result.average != DNF
        and result.event.id in Ao5_EVENTS
    ):
        return parse_ao5_solves(result)
    format_type = result.event.format
    return {
        "value1": parse_value(result.value1, format_type),
        "value2": parse_value(result.value2, format_type),
        "value3": parse_value(result.value3, format_type),
        "value4": parse_value(result.value4, format_type),
        "value5": parse_value(result.value5, format_type),
    }


def parse_ao5_solves(result):
    """ Average of 5 solves """
    solves = [
        result.value1,
        result.value2,
        result.value3,
        result.value4,
        result.value5,
    ]
    min_solve = min(solves)

    # Regulation 9f9 allows one DNF/DNS to count as the worst solve
    if min_solve in [DNS, DNF]:
        max_solve = min_solve
        complete_solves = solves.copy()
        complete_solves.pop(max_solve)
        min_solve = min(complete_solves)
    else:
        max_solve = max(solves)

    min_removed = False
    max_removed = False
    for index, solve in enumerate(solves):
        value = parse_value(solve, result.event.format)
        if solve == min_solve and not min_removed:
            solves[index] = f"({value})"
            min_removed = True
        elif solve == max_solve and not max_removed:
            solves[index] = f"({value})"
            max_removed = True
        else:
            solves[index] = value
    return {f"value{index+1}": solve for index, solve in enumerate(solves)}
