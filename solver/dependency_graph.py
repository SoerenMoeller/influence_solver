from collections import deque


class DependencyGraph:
    _start: str
    _end: str

    def __init__(self):
        self._dependency_graph: dict[str, set[str]] = {}

    def setup(self, start: str, end: str) -> list[str]:
        self._start = start
        self._end = end

        # find all nodes between start and end and remove the others
        vars_on_path: set[str] = self._dsf(start, set(), set())
        self._remove_nodes(set(self._dependency_graph.keys()) - vars_on_path)

        # build an order on the variables
        order: list[str] = self._bfs()

        return order

    def add(self, a: str, b: str, check: bool = True):
        if a not in self._dependency_graph:
            self._dependency_graph[a] = set()
        if b not in self._dependency_graph[a]:
            self._dependency_graph[a].add(b)
            if check:
                self._check_for_cycle(a, b)

    def _check_for_cycle(self, a: str, b: str):
        for node in self._dependency_graph:
            if self._dsf_cycle_check(node, set()):
                raise Exception(f"Couldn't add rule ({a}, {b})-dependency, because it destroys the implicit partial "
                                f"order.\n This can be fixed by checking the dependency graph.\n"
                                f"{self._dependency_graph}")

    def _dsf_cycle_check(self, current: str, stack: set[str]):
        if current in stack:
            return True

        stack.add(current)

        if current in self._dependency_graph:
            for node in self._dependency_graph[current]:
                if self._dsf_cycle_check(node, stack.copy()):
                    return True
        return False

    def get_vars_on_path(self) -> set[str]:
        return self._dsf(self._start, set(), set())

    def get_pre(self, node: str) -> set[str]:
        return {key for key, value in self._dependency_graph.items() if node in value}

    def _bfs(self) -> list[str]:
        assert self._start != self._end, "No need to search an order when start == end"

        order: list = []
        visited: set[str] = {self._start, self._end}
        queue: deque = deque()
        queue.append(self._start)

        while len(queue) > 0:
            node = queue.popleft()
            if node not in self._dependency_graph:
                continue
            for child in self._dependency_graph[node]:
                if child not in visited:
                    order.append(child)
                    queue.append(child)
                    visited.add(child)

        return order[::-1]

    def _dsf(self, current: str, stack: set[str], nodes: set) -> set:
        if current in stack:
            return nodes

        stack.add(current)

        if current == self._end:
            nodes.update(stack)
            return nodes
        if current in self._dependency_graph:
            for node in self._dependency_graph[current]:
                self._dsf(node, stack.copy(), nodes)
        return nodes

    def _floyd_warshall(self):
        for k in self._dependency_graph.keys():
            for i in self._dependency_graph.keys():
                for j in self._dependency_graph.keys():
                    if k in self._dependency_graph[i] and j in self._dependency_graph[k]:
                        self._dependency_graph[i].add(j)

    def _remove_nodes(self, vars_on_path: set[str]):
        for node in vars_on_path:
            self.remove_node(node)

    def remove_node(self, node: str):
        if node in self._dependency_graph:
            del self._dependency_graph[node]
        for value in self._dependency_graph.values():
            value.discard(node)
