import time

from csv_to_model import build_model_from_csv
from solver.constants import QUALITY_ANTI
from solver.solver import Solver
from transitive import create_transitive_test

BORDER: int = 10
STEPS: int = 500


def main():
    print("============================== Starting Benchmark... ==============================\n")
    print("< Starting Altitude-Barometer-Pressure Benchmark...")
    gran: int = STEPS
    for i in range(1, BORDER):
        start_time: float = time.time()
        statements: list[tuple] = build_model_from_csv("altitude_pressure", gran, 7)
        solver: Solver = Solver(statements, v=0)
        result: bool = solver.solve(("Altitude", (914, 1500), QUALITY_ANTI, (-10, 130), "Atmospheric Pressure"))
        print(f"Model with {len(statements)} statements took {time.time() - start_time} seconds ", end="")
        print(f"and {'could' if result else 'could not'} be solved.")

        gran += STEPS
    print("> Finished Altitude-Barometer-Pressure Benchmark!\n")

    print("< Starting Angle-Intensity Benchmark...")
    gran: int = STEPS * 2
    for i in range(1, BORDER):
        start_time: float = time.time()
        statements: list[tuple] = build_model_from_csv("angle_intensity", gran, 7)
        solver: Solver = Solver(statements, v=0)
        result: bool = solver.solve(("Angle", (30, 75), QUALITY_ANTI, (4, 1036), "Light Intensity"))
        print(f"Model with {len(statements)} statements took {time.time() - start_time} seconds ", end="")
        print(f"and {'could' if result else 'could not'} be solved.")

        gran += STEPS * 2
    print("> Finished Angle-Intensity Benchmark!\n")

    print("< Starting Transitivity Benchmark...")
    for i in range(1, 40, 4):
        start_time: float = time.time()
        statements, statement = create_transitive_test(i, STEPS, 3)
        solver: Solver = Solver(statements, v=0)
        result: bool = solver.solve(statement)
        print(f"Model with {len(statements)} statements took {time.time() - start_time} seconds ", end="")
        print(f"and {'could' if result else 'could not'} be solved.")
        
    print("> Finished Transitivity Benchmark!\n")
    print("=============================== Finishes Benchmark! ===============================")


if __name__ == "__main__":
    main()
