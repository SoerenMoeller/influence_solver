from examples.current_voltage import get_current_voltage_example
from solver.solver import Solver
from benchmark.benchmark import run_benchmark


def main():
    statements, mult_hypothsis = get_current_voltage_example()
    hypythesis = mult_hypothsis[1]
    solver = Solver(statements, v=2)
    solver.solve(hypythesis)

    # run a predefined benchmark with increasing model size and time measurements
    #run_benchmark()
    

if __name__ == '__main__':
    main()
