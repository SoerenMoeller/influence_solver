import math

from solver.constants import *
from solver.solver import Solver


def main():
    ################################################################
    # AC current as an influence model with time influencing voltage
    # and voltage causing current via some resistance
    # modelled at arbitrary degrees of granularity

    resistance = 300
    phase_granularity = 1.57
    top_ac_voltage = 230
    voltage_granularity = 100

    peak_voltage = top_ac_voltage * math.sqrt(2)
    peak_current = peak_voltage / resistance
    pi = 3.1415
    twopi = pi * 2
    points = range(int(twopi / phase_granularity))
    l = len(points)
    tpoints = [t / l * twopi - pi for t in points]
    current_model = set()
    for t in tpoints:
        t1 = t - phase_granularity
        t2 = t + phase_granularity
        v1 = math.sin(t1) * peak_voltage
        v2 = math.sin(t2) * peak_voltage
        if v1 < v2:
            current_model.add(('time', (t1, t2), QUALITY_MONO, (v1, v2), 'voltage'))
        elif v2 > v1:
            current_model.add(('time', (t1, t2), QUALITY_ANTI, (v2, v1), 'voltage'))
        else:
            current_model.add(('time', (t1, t2), QUALITY_CONS, (v1, v1), 'voltage'))
    points = range(int(2 * peak_voltage / voltage_granularity))
    l = len(points)
    vpoints = [v / l * 2 * peak_voltage - peak_voltage for v in points]
    for v in vpoints:
        v1 = v - voltage_granularity
        v2 = v + voltage_granularity
        c1 = v1 / resistance
        c2 = v2 / resistance
        if c1 < c2:
            current_model.add(('voltage', (v1, v2), QUALITY_MONO, (c1, c2), 'current'))
        elif c2 > c1:
            current_model.add(('voltage', (v1, v2), QUALITY_ANTI, (c2, c1), 'current'))
        else:
            current_model.add(('voltage', (v1, v2), QUALITY_CONS, (c1, c1), 'current'))

    current_model_statements = \
        [('time', (-pi, -pi / 2), QUALITY_ANTI, (-peak_current, 0), 'current'),
         ('time', (-pi / 2, pi / 2), QUALITY_MONO, (-peak_current, peak_current), 'current'),
         ('time', (pi / 2, pi), QUALITY_ANTI, (0, peak_current), 'current')]

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
        ("a", (10, 11), QUALITY_MONO, (1.3, 1.9), "b")
    ]
    statement_0: tuple = ("a", (5, 7), QUALITY_MONO, (1.7, 1.8), "b")

    model_1: set[tuple] = {
        ("a", (0, 5), QUALITY_MONO, (2, 4), "b"),
        ("a", (2, 3), QUALITY_MONO, (0, 3), "b")
    }
    statement_1: tuple = ("a", (0, 5), QUALITY_MONO, (2, 3), "b")

    model_2: set[tuple] = {
        ("a", (0, 1), QUALITY_MONO, (0, 1), "b"),
        ("b", (0, 1), QUALITY_MONO, (0, 1), "d"),
        ("d", (0, 1), QUALITY_MONO, (0, 1), "c"),
        ("a", (0, 1), QUALITY_MONO, (0, 1), "c"),
        ("d", (0, 1), QUALITY_MONO, (0, 1), "e"),
        ("b", (0, 1), QUALITY_MONO, (0, 1), "e")
    }
    statement_2: tuple = ("a", (0, 1), QUALITY_MONO, (0, 1), "e")

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

    solver: Solver = Solver(model_3)
    result: bool = solver.solve(statement_3)

    """ testing forked version
    x = "x"
    a = [Interval(1, 2, x, 3, 4),
         Interval(1, 3, x, 3, 4),
         Interval(0, 1, x, 3, 4),
         Interval(0, 0, x, 3, 4),
         Interval(0, 4, x, 3, 4),
         Interval(2, 2, x, 3, 4),
         Interval(2, 4, x, 3, 4)]

    t = IntervalTree(a)
    print(t[1:2])
    print(t.overlap_exclusive(1, 2))
    print(t[1:2] - t.overlap_exclusive(1, 2))
    """


if __name__ == '__main__':
    main()
