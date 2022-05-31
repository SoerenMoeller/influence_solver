from intervaltree import Interval, IntervalTree
from constants import *


def quality_add(quality_a: str, quality_b: str) -> str:
    return ADD[quality_a][quality_b]


def is_stronger_as(quality_a: str, quality_b: str) -> bool:
    if quality_b == QUALITY_ARB or quality_a == QUALITY_CONS:
        return True
    elif quality_a == QUALITY_ARB:
        return True if quality_b == QUALITY_ARB else False
    elif quality_a == QUALITY_MONO:
        return True if quality_b in [QUALITY_MONO, QUALITY_ARB] else False
    elif quality_a == QUALITY_ANTI:
        return True if quality_b in [QUALITY_ANTI, QUALITY_ARB] else False
    else:
        assert False, "error"


def turn_interval(interval: Interval) -> Interval:
    # returns interval where borders in data field and begin/end are swapped
    # needed since x and y borders might be switched
    data: tuple = interval.data
    return Interval(data[1][0], data[1][1], (data[0], (interval.begin, interval.end)))


def get_quality(interval: Interval) -> str:
    return interval.data[0]


def get_y_begin(interval: Interval) -> float:
    return interval.data[1][0]


def get_y_end(interval: Interval) -> float:
    return interval.data[1][1]


def add_to_tree(model: tuple[IntervalTree, IntervalTree], statement: Interval, v=False) -> bool:
    x_tree: IntervalTree = model[0]
    if statement in x_tree:
        return False

    overlap: set[Interval] = x_tree[statement.begin: statement.end]
    enveloping: set[Interval] = {i for i in overlap if i.begin >= statement.begin and i.end <= statement.end}
    enveloped_by: set[Interval] = {i for i in overlap if i.begin <= statement.begin and i.end >= statement.end}

    # if new statement envelops interval with less width and more height and weaker quality, we can remove the old one
    for interval in enveloping:
        if is_stronger_as(get_quality(statement), get_quality(interval)) and \
                get_y_begin(statement) >= get_y_begin(interval) and get_y_end(statement) <= get_y_end(interval):
            # remove old interval (not needed anymore)
            model[0].remove(interval)
            model[1].remove(turn_interval(interval))

            model[0].add(statement)
            model[1].add(turn_interval(statement))

            if v:
                print(f"=== removed interval -{interval}- for stronger interval -{statement}- ===")

            return True

    for interval in enveloped_by:
        if is_stronger_as(get_quality(interval), get_quality(statement)) and \
                get_y_begin(interval) >= get_y_begin(statement) and get_y_end(interval) <= get_y_end(statement):
            if v:
                print(f"=== did not include interval -{statement}- because of stronger interval -{interval}- ===")
            return False

    model[0].add(statement)
    model[1].add(turn_interval(statement))
    return True
