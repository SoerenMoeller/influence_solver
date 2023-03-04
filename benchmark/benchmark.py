import time

from benchmark.csv_to_model import build_model_from_csv
from solver.constants import QUALITY_ARB, QUALITY_ANTI
from solver.solver import Solver
from benchmark.transitive import create_transitive_benchmark


MAX_STEPS: int = 10


def run_benchmark():
    print("============================== Starting Benchmark... ==============================\n")
    print("< Starting Altitude-Barometer-Pressure Benchmark...")

    initial_amount_of_statements: int = 250
    amount_per_step: int = 250
    amount_of_statements: int = initial_amount_of_statements

    for i in range(1, MAX_STEPS):
        start_time: float = time.time()
        statements: list[tuple] = build_model_from_csv("altitude_pressure", default_amount_of_statements=amount_of_statements, default_overlap=1/3)
        solver: Solver = Solver(statements, v=0)
        result: bool = solver.solve(("Altitude", (-100, 15100), QUALITY_ANTI, (-10, 122), "Atmospheric Pressure"))
        print(f"Model with {len(statements)} statements took {time.time() - start_time} seconds ", end="")
        print(f"and {'could' if result else 'could not'} be solved.")

        amount_of_statements += amount_per_step
    print("> Finished Altitude-Barometer-Pressure Benchmark!\n")
    
    print("< Starting Angle-Intensity Benchmark...")

    initial_amount_of_statements: int = 30
    amount_per_step: int = 15 * initial_amount_of_statements
    amount_of_statements: int = initial_amount_of_statements

    for i in range(1, MAX_STEPS):
        start_time: float = time.time()
        statements: list[tuple] = build_model_from_csv("angle_intensity", default_amount_of_statements=amount_of_statements, default_overlap=1/3)
        solver: Solver = Solver(statements, v=0)
        result: bool = solver.solve(("Angle", (0, 360), QUALITY_ARB, (-50, 1100), "Light Intensity"))
        print(f"Model with {len(statements)} statements took {time.time() - start_time} seconds ", end="")
        print(f"and {'could' if result else 'could not'} be solved.")

        amount_of_statements += amount_per_step
    print("> Finished Angle-Intensity Benchmark!\n")
    
    print("< Starting Transitivity Benchmark...")
    for i in range(10, 50, 4):
        start_time: float = time.time()
        statements, statement = create_transitive_benchmark(i, 1000, 3)
        solver: Solver = Solver(statements, v=0)
        result: bool = solver.solve(statement)
        print(f"Model with {len(statements)} statements and {i} transitive steps took {time.time() - start_time} "
              f"seconds ", end="")
        print(f"and {'could' if result else 'could not'} be solved.")

    print("> Finished Transitivity Benchmark!\n")
    print("=============================== Finishes Benchmark! ===============================")
