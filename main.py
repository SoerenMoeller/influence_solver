from examples.current import current_model, current_model_statements
from solver.solver import Solver


def main():
    solver: Solver = Solver(current_model)
    solver.solve(current_model_statements[3], v=3)


if __name__ == '__main__':
    main()
