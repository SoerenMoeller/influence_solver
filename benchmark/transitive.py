from solver.constants import QUALITY_MONO, QUALITY_ANTI, QUALITY_CONS


def create_transitive_test(amount: int, amount_per_step: int, width: int) -> tuple[set[tuple], tuple]:
    initial: str = "a"
    last: str = "c"

    statements: set[tuple] = set()
    prev: list[str] = []
    for i in range(width):
        quality: str = QUALITY_MONO if i % 2 == 0 else QUALITY_ANTI
        var: str = f"b(0, {i})"
        prev.append(var)
        for j in range(amount_per_step):
            iv: tuple = (initial, (j, j + 1), quality, (0, 1), var)
            statements.add(iv)

    for i in range(1, amount):
        for j in range(width):
            quality: str
            if i % 2 == 0:
                quality = QUALITY_MONO if j % 2 == 0 else QUALITY_ANTI
            else:
                quality = QUALITY_ANTI if j % 2 == 0 else QUALITY_MONO
            var: str = f"b({i}, {j})"
            for k in range(amount_per_step):
                iv: tuple = (prev[j], (k, k + 1), quality, (0, 1), var)
                statements.add(iv)
            prev[j] = var

    for i in range(width):
        quality: str
        if amount % 2 == 0:
            quality = QUALITY_MONO if i % 2 == 0 else QUALITY_ANTI
        else:
            quality = QUALITY_ANTI if i % 2 == 0 else QUALITY_MONO
        var: str = f"b({amount - 1}, {i})"
        prev.append(var)
        for j in range(amount_per_step):
            iv: tuple = (var, (j, j + 1), quality, (0, 1), last)
            statements.add(iv)

    return statements, (initial, (0, 1), QUALITY_CONS, (0, 1), last)
