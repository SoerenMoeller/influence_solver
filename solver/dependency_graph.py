dependency_graph: dict[str, set[str]] = {}


def get_dependency_graph():
    return dependency_graph


def setup_graph(start: str, end: str) -> list[str]:
    # find all nodes between start and end
    vars_on_path: set[str] = dsf(start, end, set(), set())

    # build an order on the variables
    order: list[str] = topological_sort(vars_on_path)

    # build transitives
    floyd_warshall()

    return order


def topological_sort(nodes):
    visited: set = set()
    stack: list = []

    for node in nodes:
        if node not in visited:
            _topological_recursive(node, visited, stack)

    return stack[::-1]


def _topological_recursive(current, visited, stack):
    visited.add(current)

    if current in dependency_graph:
        for node in dependency_graph[current]:
            if node not in visited:
                _topological_recursive(node, visited, stack)

    stack.append(current)


def dsf(current: str, end: str, stack: set[str], nodes: set) -> set:
    global dependency_graph

    if current in stack:
        return nodes

    stack.add(current)

    if current == end:
        nodes.update(stack)
        return nodes
    if current in dependency_graph:
        for node in dependency_graph[current]:
            dsf(node, end, stack.copy(), nodes)
    return nodes


def add_to_graph(dependency: tuple):
    global dependency_graph

    a: str = dependency[0]
    b: str = dependency[4]

    if a not in dependency_graph:
        dependency_graph[a] = set()
    if b not in dependency_graph[a]:
        dependency_graph[a].add(b)
        check_for_cycle(dependency)


def floyd_warshall():
    for k in dependency_graph.keys():
        for i in dependency_graph.keys():
            for j in dependency_graph.keys():
                if k in dependency_graph[i] and j in dependency_graph[k]:
                    dependency_graph[i].add(j)


def check_for_cycle(dependency: tuple):
    for node in dependency_graph:
        if dsf_cycle_check(node, set()):
            raise Exception(f"Couldn't add rule {dependency}, because it destroys the implicit partial order.\n"
                            f"This can be fixed by checking the dependency graph.\n"
                            f"{dependency_graph}")


def dsf_cycle_check(current: str, stack: set[str]):
    global dependency_graph

    if current in stack:
        return True

    stack.add(current)

    if current in dependency_graph:
        for node in dependency_graph[current]:
            if dsf_cycle_check(node, stack.copy()):
                return True
    return False
