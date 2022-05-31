from itertools import chain


def build_graph(dependencies: set[tuple], goal: tuple) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}

    # dependency has form (a, b)
    for dependency in dependencies:
        a: str = dependency[0]
        b: str = dependency[1]

        if a not in graph:
            graph[a] = set()
        graph[a].add(b)

        if b not in graph:
            graph[b] = set()
        graph[b].add(a)

    # search all paths that lead from the starting variable to the ending variable
    begin, end = goal

    # use dsf but remove counter edges if path succeeds, break if circle is detected
    graph = floyd_warshall(graph)
    dsf(graph, begin, end, [])

    # check all used variables
    variables: set = set(chain.from_iterable(paths))
    print(paths)

    return graph


def floyd_warshall(graph: dict) -> dict:
    for k in graph.keys():
        for i in graph.keys():
            for j in graph.keys():
                if k in graph[i] and j in graph[k]:
                    graph[i].add(j)

    return graph


paths: list[list[str]] = []


def dsf(graph: dict, current: str, end: str, path: list[str]):
    global paths
    if current in path:
        return

    path.append(current)
    if current == end:
        paths.append(path)
        return

    for node in graph[current]:
        dsf(graph, node, end, path[:])
