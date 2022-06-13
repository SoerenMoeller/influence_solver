from intervaltree.interval import Interval
from intervaltree.intervaltree import IntervalTree
from .constants import *


def min_quality(quality_a: str, quality_b: str) -> str:
    if quality_a == quality_b:
        return quality_a
    elif quality_a == QUALITY_ARB and quality_b != QUALITY_ARB:
        return quality_b
    elif quality_b == QUALITY_ARB and quality_a != QUALITY_ARB:
        return quality_a
    elif quality_a == QUALITY_MONO and quality_b == QUALITY_ANTI or \
            quality_b == QUALITY_MONO and quality_a == QUALITY_ANTI:
        return QUALITY_CONS
    elif (quality_a == QUALITY_ANTI or quality_a == QUALITY_ANTI) and quality_b == QUALITY_CONS:
        return quality_a
    elif (quality_b == QUALITY_ANTI or quality_b == QUALITY_ANTI) and quality_a == QUALITY_CONS:
        return quality_b
    else:
        assert False, f"Tried to minimize unknown quality pair: {quality_a}, {quality_b}"


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
        assert False, f"Tried to strengthen unknown quality pair: {quality_a}, {quality_b}"


def add_to_tree(model: tuple[IntervalTree, IntervalTree], statement: Interval, v=0) -> bool:
    if statement is None:
        return False

    x_tree: IntervalTree = model[0]
    if statement in x_tree:
        return False

    overlap: set[Interval] = x_tree[statement.begin: statement.end]
    enveloping: set[Interval] = {i for i in overlap if i.begin >= statement.begin and i.end <= statement.end}
    enveloped_by: set[Interval] = {i for i in overlap if i.begin <= statement.begin and i.end >= statement.end}

    # if new statement envelops interval with less width and more height and weaker quality, we can remove the old one
    for interval in enveloping:
        if is_stronger_as(statement.quality, interval.quality) and \
                statement.begin_other >= interval.begin_other and statement.end_other <= interval.end_other:
            # remove old interval (not needed anymore)
            model[0].remove(interval)
            model[1].remove(interval.turn_interval())

            model[0].add(statement)
            model[1].add(statement.turn_interval())

            if v >= 2:
                print(f"=== removed interval -{interval}- for stronger interval -{statement}- ===")

            return True

    for interval in enveloped_by:
        if is_stronger_as(interval.quality, statement.quality) and \
                interval.begin_other >= statement.begin_other and interval.end_other <= statement.end_other:
            if v >= 2:
                print(f"=== did not include interval -{statement}- because of stronger interval -{interval}- ===")
            return False

    model[0].add(statement)
    model[1].add(statement.turn_interval())
    return True
