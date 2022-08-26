from csv_to_model import build_model_from_csv
from solver.constants import QUALITY_ANTI
from solver.solver import Solver


def main():
    statements: list[tuple] = build_model_from_csv("altitude_pressure", 20)
    solver: Solver = Solver(statements)
    solver.solve(("Altitude", (-1000, 3000), QUALITY_ANTI, (-10, 130), "Atmospheric Pressure"))


if __name__ == "__main__":
    main()
