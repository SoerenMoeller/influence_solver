from functools import reduce
from typing import Union

from statement_containers.statement import Statement
from solver.constants import *
from solver.util import quality_add, min_quality, quality_times, is_stronger_as


"""
Containing some basic rules of the rule set
"""


def interval_strength_right(statement_a: Statement, statement_b: Statement) -> Union[Statement, None]:
    """
    Implementation of the (R)-rules. Checks if statements overlap and creates new statement of possible

    Parameters:
        statement_a (Statement): left statement of the rule
        statement_b (Statement): right statement of the rule

    Returns:
        (Statement/None): Newly created statement or none, of it could not be created
    """

    if not (statement_b.begin <= statement_a.end <= statement_b.end):
        return None

    x, y = statement_a.begin_y, statement_a.end_y
    a, b = statement_b.begin_y, statement_b.end_y
    quality_a = statement_a.quality

    rule = None
    if x < b:
        if quality_a == QUALITY_CONS:
            rule = Statement(statement_a.begin, statement_a.end, QUALITY_CONS, max(x, a), min(y, b))
        elif quality_a == QUALITY_MONO and b < y:
            rule = Statement(statement_a.begin, statement_a.end, QUALITY_MONO, x, b)
    elif quality_a == QUALITY_ANTI and x < a < y:
        rule = Statement(statement_a.begin, statement_a.end, QUALITY_ANTI, a, y)

    if rule is not None and statement_a.stronger_as(rule):
        rule = None

    return rule


def interval_strength_left(statement_a: Statement, statement_b: Statement) -> Union[Statement, None]:
    """
    Implementation of the (L)-rules. Checks if statements overlap and creates new statement of possible

    Parameters:
        statement_a (Statement): left statement of the rule
        statement_b (Statement): right statement of the rule

    Returns:
        (Statement/None): Newly created statement or none, of it could not be created
    """

    if not (statement_a.begin <= statement_b.begin <= statement_a.end):
        return None

    x, y = statement_a.begin_y, statement_a.end_y
    a, b = statement_b.begin_y, statement_b.end_y
    quality_b = statement_b.quality

    rule = None
    if quality_b == QUALITY_CONS and x < b:
        rule = Statement(statement_b.begin, statement_b.end, QUALITY_CONS, max(x, a), min(y, b))
    elif quality_b == QUALITY_MONO and a < x < b:
        rule = Statement(statement_b.begin, statement_b.end, QUALITY_MONO, x, b)
    elif quality_b == QUALITY_ANTI and a < y < b:
        rule = Statement(statement_b.begin, statement_b.end, QUALITY_ANTI, a, y)

    if rule is not None and statement_b.stronger_as(rule):
        rule = None

    return rule


def interval_strength_multiple(begin: float, end: float, statements: set[Statement]) -> Statement:
    """
    Implementation of the (I+)-rule. Multiple usage on all statements, enveloping a given area.

    Parameters:
        begin (float): begin of the area 
        end (float): end of the area
        statements (set[Statement]): statements overlapping [begin, end]

    Returns:
        (Statement): Newly created statement 
    """

    begin_y: float = max(st.begin_y for st in statements)
    end_y: float = min(st.end_y for st in statements)
    quality: str = reduce(min_quality, (st.quality for st in statements))

    return Statement(begin, end, quality, begin_y, end_y)


def interval_join_multiple(statements: list[Statement]) -> Union[Statement, None]:
    """
    Implementation of the join rule. Joins all given statements from left to right, if they overlap

    Parameters:
        statements (list[Statement]): statements to join

    Returns:
        (Statement/None): Newly created statement or none, of it could not be created
    """

    if not statements:
        return None
    for i in range(len(statements) - 1):
        if statements[i].distance_to(statements[i + 1]) > 0:
            return None

    quality: str = reduce(quality_add, (st.quality for st in statements))
    begin_y: float = min(st.begin_y for st in statements)
    end_y: float = max(st.end_y for st in statements)

    return Statement(statements[0].begin, statements[-1].end, quality, begin_y, end_y)


def transitivity(statement_a: Statement, statement_b: Statement) -> Union[Statement, None]:
    """
    Implementation of the (T)-rule
    Parameters:
        statement_a (Statement): left statement of the rule
        statement_b (Statement): right statement of the rule

    Returns:
        (Statement/None): Newly created statement or none, of it could not be created
    """
    
    if not (statement_a.begin_y >= statement_b.begin and statement_a.end_y <= statement_b.end):
        return None

    quality: str = quality_times(statement_a.quality, statement_b.quality)
    return Statement(statement_a.begin, statement_a.end, quality, statement_b.begin_y, statement_b.end_y)


def rule_fact(hypothesis: tuple, statement: Statement) -> bool:
    """
    Implementation of the (F)-rule

    Parameters:
        hypothesis (tuple): current hypothesis to check
        statement (Statement): statement that (potentially) can be used to verify the hypothesis
    """

    if statement is None:
        return False

    quality: str = hypothesis[2]
    interval_x: tuple[float, float] = hypothesis[1]
    interval_y: tuple[float, float] = hypothesis[3]

    return statement.enveloping(interval_x[0], interval_x[1]) and statement.begin_y >= interval_y[0] \
        and statement.end_y <= interval_y[1] and is_stronger_as(statement.quality, quality)
