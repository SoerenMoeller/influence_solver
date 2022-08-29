import time

from csv_to_model import build_model_from_csv
from solver.constants import QUALITY_ANTI
from solver.solver import Solver
from transitive import create_transitive_test

BORDER: int = 10
STARTING_GRAN: int = 20


def main():
    print("============================== Starting Benchmark... ==============================")
    print("< Starting Altitude-Barometer-Pressure Benchmark...")
    gran: int = STARTING_GRAN
    for i in range(1, BORDER):
        start_time: float = time.time()
        statements: list[tuple] = build_model_from_csv("altitude_pressure", gran, 7)
        solver: Solver = Solver(statements, v=0)
        result: bool = solver.solve(("Altitude", (914, 1500), QUALITY_ANTI, (-10, 130), "Atmospheric Pressure"))
        print(f"Model with {len(statements)} statements took {time.time() - start_time} seconds ", end="")
        print(f"and {'could' if result else 'could not'} be solved.")

        gran *= 2
    print("> Finished Altitude-Barometer-Pressure Benchmark!")

    print("< Starting Angle-Intensity Benchmark...")
    gran: int = STARTING_GRAN
    for i in range(1, BORDER):
        start_time: float = time.time()
        statements: list[tuple] = build_model_from_csv("angle_intensity", gran, 7)
        solver: Solver = Solver(statements, v=0)
        result: bool = solver.solve(("Angle", (30, 75), QUALITY_ANTI, (4, 1036), "Light Intensity"))
        print(f"Model with {len(statements)} statements took {time.time() - start_time} seconds ", end="")
        print(f"and {'could' if result else 'could not'} be solved.")

        gran *= 2
    print("> Finished Angle-Intensity Benchmark!")

    print("< Starting Transitivity Benchmark...")
    for i in range(1, 20, 2):
        start_time: float = time.time()
        statements, statement = create_transitive_test(i, 500, 3)
        solver: Solver = Solver(statements, v=0)
        result: bool = solver.solve(statement)
        print(f"Model with {len(statements)} statements took {time.time() - start_time} seconds ", end="")
        print(f"and {'could' if result else 'could not'} be solved.")

        gran *= 2
    print("> Finished Transitivity Benchmark!")


if __name__ == "__main__":
    main()
