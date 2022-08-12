from examples.current import current_model, current_model_statements
from examples.intersect import model, statement
from solver.solver import Solver


def main():
    solver: Solver = Solver(model)
    result: bool = solver.solve(statement)


if __name__ == '__main__':
    main()
