from examples.current import current_model, current_model_statements
from examples.intersect import model, statement
from solver.solver import Solver


def main():
    solver: Solver = Solver(current_model)
    result: bool = solver.solve(current_model_statements[3])


if __name__ == '__main__':
    main()
