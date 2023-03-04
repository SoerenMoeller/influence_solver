from solver.constants import QUALITY_MONO, QUALITY_ANTI


def create_transitive_benchmark(amount_of_inner_variables: int, amount_per_step: int, 
                                amount_of_rows: int) -> tuple[set[tuple], tuple]:
    """
    Create a transitive benchmark with increasing amounts of variables in the model. 
    Creates disjoint paths of a fixed length (in the dependency graph). 

    Parameters:
        amount_of_inner_variables (int): path length in the dependency graph
        amount_of_rows (int): amount of paths in the dependency graph
        amount_per_step (int): amount of statements in each sub-model

    Returns:
        Created statements and a hypothesis
    """

    initial: str = "a"
    last: str = "c"

    statements: set[tuple] = set()
    prev: list[str] = []
    offset: float = 0.1

    # build first variable of the dependency graph
    for i in range(amount_of_rows):
        quality: str = QUALITY_MONO
        var: str = f"b(0, {i})"
        prev.append(var)
        for j in range(amount_per_step):
            y_interval = (j - offset, j + 1 + offset)
            iv: tuple = (initial, (j - offset, j + 1 + offset), quality, y_interval, var)
            statements.add(iv)

    # build inner rows of the dependency graph
    for i in range(1, amount_of_inner_variables):
        for j in range(amount_of_rows):
            quality: str = QUALITY_MONO
            var: str = f"b({i}, {j})"
            for k in range(amount_per_step):
                y_interval = (k - offset, k + 1 + offset)
                iv: tuple = (prev[j], (k - offset, k + 1 + offset), quality, y_interval, var)
                statements.add(iv)
            prev[j] = var

    # build final variable of the dependency graph
    for i in range(amount_of_rows):
        quality: str = QUALITY_MONO if i % 2 == 0 else QUALITY_ANTI
        var: str = f"b({amount_of_inner_variables - 1}, {i})"
        for j in range(amount_per_step):
            y_interval = (j - offset, j + 1 + offset)
            iv: tuple = (var, (j - offset, j + 1 + offset), quality, y_interval, last)
            statements.add(iv)

    return statements, (initial, (0, amount_per_step), QUALITY_MONO, (0, amount_per_step), last)
