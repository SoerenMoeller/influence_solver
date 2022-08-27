import time

from csv_to_model import build_model_from_csv
from solver.constants import QUALITY_ANTI
from solver.solver import Solver

BORDER: int = 10


def main():
    print("========== Starting Benchmark... ==========")
    print("< Starting Altitude-Barometer-Pressure Benchmark...")
    gran: int = 20
    for i in range(1, BORDER):
        start_time: float = time.time()
        statements: list[tuple] = build_model_from_csv("altitude_pressure", gran, 7)
        solver: Solver = Solver(statements, v=0 if i != BORDER - 1 else 4)
        result: bool = solver.solve(("Altitude", (914, 1500), QUALITY_ANTI, (-10, 130), "Atmospheric Pressure"))
        print(f"Model with {len(statements)} statements took {time.time() - start_time} seconds ", end="")
        print(f"and {'could' if result else 'could not'} be solved.")

        gran *= 2
    print("> Finished Altitude-Barometer-Pressure Benchmark!")


if __name__ == "__main__":
    main()
