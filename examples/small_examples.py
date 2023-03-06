from solver.constants import QUALITY_MONO


"""
Contains small and handbuild models with statements, which can be used to inspect 
statements when activating the visualization process
"""


def get_model_0() -> tuple[list[tuple], tuple]:
    model_0: list[tuple] = [
        ("a", (0, 2), QUALITY_MONO, (3, 3.5), "b"),
        ("a", (2, 3.3), QUALITY_MONO, (2.1, 3.2), "b"),
        ("a", (3, 4.5), QUALITY_MONO, (1.4, 2.2), "b"),
        ("a", (4, 5.1), QUALITY_MONO, (1.2, 2), "b"),
        ("a", (5, 7), QUALITY_MONO, (1.1, 1.9), "b"),
        ("a", (7, 8), QUALITY_MONO, (1.7, 3), "b"),
        ("a", (7.9, 9), QUALITY_MONO, (1, 2), "b"),
        ("a", (8.6, 10.8), QUALITY_MONO, (1.5, 1.8), "b"),
        ("a", (8.6, 10.7), QUALITY_MONO, (1.6, 2.2), "b"),
        ("a", (0, 2.5), QUALITY_MONO, (1, 2), "b"),
        ("a", (10, 11), QUALITY_MONO, (1.3, 1.9), "b")
    ]

    statement_0: tuple = ("a", (5, 7), QUALITY_MONO, (1.7, 1.8), "b")

    return model_0, statement_0


def get_model_1() -> tuple[list[tuple], tuple]:
    model_1: set[tuple] = {
        ("a", (0, 5), QUALITY_MONO, (2, 4), "b"),
        ("a", (2, 3), QUALITY_MONO, (0, 3), "b")
    }

    statement_1: tuple = ("a", (0, 5), QUALITY_MONO, (2, 3), "b")

    return model_1, statement_1


def get_model_2() -> tuple[list[tuple], tuple]:
    model_2: set[tuple] = {
        ("a", (0, 1), QUALITY_MONO, (0, 1), "b"),
        ("b", (0, 1), QUALITY_MONO, (0, 1), "d"),
        ("d", (0, 1), QUALITY_MONO, (0, 1), "c"),
        ("a", (0, 1), QUALITY_MONO, (0, 1), "c"),
        ("d", (0, 1), QUALITY_MONO, (0, 1), "e"),
        ("b", (0, 1), QUALITY_MONO, (0, 1), "e")
    }

    statement_2: tuple = ("a", (0, 1), QUALITY_MONO, (0, 1), "e")

    return model_2, statement_2


def get_model_3() -> tuple[list[tuple], tuple]:
    model_3: set[tuple] = {
        ("a", (0, 0.5), QUALITY_MONO, (0, 1), "b"),
        ("a", (0.4, 0.6), QUALITY_MONO, (0.5, 1.8), "b"),
        ("a", (0.6, 1), QUALITY_MONO, (1, 2.5), "b"),
        ("a", (0.85, 1.4), QUALITY_MONO, (2.3, 2.7), "b"),
        ("a", (1.3, 1.7), QUALITY_MONO, (1.9, 2.4), "b"),
        ("a", (1.7, 2.5), QUALITY_MONO, (1.3, 2), "b"),
        ("a", (2.4, 3), QUALITY_MONO, (0.5, 1.5), "b"),
        ("b", (0, 1), QUALITY_MONO, (0, 2), "c"),
        ("b", (0.4, 2), QUALITY_MONO, (0.4, 1.8), "c"),
        ("b", (1.2, 2.1), QUALITY_MONO, (0.2, 1.5), "c"),
        ("b", (1.9, 2.5), QUALITY_MONO, (1.3, 2), "c"),
        ("b", (2.4, 3), QUALITY_MONO, (1.7, 3), "c")
    }

    statement_3: tuple = ("a", (1, 2), QUALITY_MONO, (1, 2), "c")

    return model_3, statement_3
