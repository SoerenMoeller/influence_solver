import time

from csv_to_model import build_model_from_csv
from solver.constants import QUALITY_ARB, QUALITY_ANTI
from solver.solver import Solver
from transitive import create_transitive_test

BORDER: int = 10
STEPS: int = 125


def main():
    print("============================== Starting Benchmark... ==============================\n")
    print("< Starting Altitude-Barometer-Pressure Benchmark...")

    gran: int = STEPS
    for i in range(1, BORDER):
        start_time: float = time.time()
        statements: list[tuple] = build_model_from_csv("altitude_pressure", gran, 7)
        solver: Solver = Solver(statements, v=0)
        result: bool = solver.solve(("Altitude", (-100, 15100), QUALITY_ANTI, (-10, 122), "Atmospheric Pressure"))
        print(f"Model with {len(statements)} statements took {time.time() - start_time} seconds ", end="")
        print(f"and {'could' if result else 'could not'} be solved.")

        gran += STEPS
    print("> Finished Altitude-Barometer-Pressure Benchmark!\n")

    print("< Starting Angle-Intensity Benchmark...")
    gran: int = 30
    for i in range(1, BORDER):
        start_time: float = time.time()
        statements: list[tuple] = build_model_from_csv("angle_intensity", gran, 7)
        solver: Solver = Solver(statements, v=0)
        result: bool = solver.solve(("Angle", (0, 360), QUALITY_ARB, (-50, 1100), "Light Intensity"))
        print(f"Model with {len(statements)} statements took {time.time() - start_time} seconds ", end="")
        print(f"and {'could' if result else 'could not'} be solved.")

        gran += STEPS * 15
    print("> Finished Angle-Intensity Benchmark!\n")

    print("< Starting Transitivity Benchmark...")
    for i in range(10, 50, 4):
        start_time: float = time.time()
        statements, statement = create_transitive_test(i, STEPS * 8, 3)
        solver: Solver = Solver(statements, v=0)
        result: bool = solver.solve(statement)
        print(f"Model with {len(statements)} statements and {i} transitive steps took {time.time() - start_time} "
              f"seconds ", end="")
        print(f"and {'could' if result else 'could not'} be solved.")

    print("> Finished Transitivity Benchmark!\n")
    print("=============================== Finishes Benchmark! ===============================")


if __name__ == "__main__":
    main()
