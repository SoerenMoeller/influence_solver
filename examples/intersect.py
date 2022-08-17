from solver.constants import QUALITY_CONS, QUALITY_MONO, QUALITY_ANTI

a: str = "a"
b: str = "b"

model: set[tuple] = {
    (a, (0, 1), QUALITY_MONO, (0, 3), b),
    (a, (3, 4), QUALITY_ANTI, (0, 3), b),
    (a, (0.5, 3.5), QUALITY_ANTI, (0.5, 2.5), b),
    (a, (0.75, 3.25), QUALITY_MONO, (1, 2), b)
}

statement: tuple = (a, (-0.5, 4.5), QUALITY_CONS, (-0.25, 3.25), b)
