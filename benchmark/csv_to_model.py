import bisect
import csv
import os
from statistics import mean

from solver.constants import QUALITY_CONS, QUALITY_ARB, QUALITY_ANTI, QUALITY_MONO


def build_model_from_csv(name: str, granularity: float) -> list[tuple]:
    data: list[tuple[tuple, list[tuple]]] = _read_csv(name)

    model: list[tuple] = []
    for influence in data:
        a, b = influence[0]
        points: list[tuple] = influence[1]
        assert points, "Empty data"

        x_points: list[float] = [p[0] for p in points]
        y_points: list[float] = [p[1] for p in points]
        greatest_end: float = x_points[-1]
        current: float = points[0][0]
        statements: list[tuple] = []
        building: bool = True
        while building:
            end: float = current + granularity
            if current + granularity > greatest_end:
                end = greatest_end
                building = False

            first_index: int = bisect.bisect_left(x_points, current)
            last_index: int = bisect.bisect_right(x_points, end)
            if first_index == last_index:
                if last_index + 2 < len(x_points):
                    last_index += 2
                else:
                    last_index = len(x_points)
            if first_index == last_index - 1:
                if last_index + 1 < len(x_points):
                    last_index += 1
                else:
                    last_index = len(x_points)

            quality: str = QUALITY_CONS
            for i in range(first_index, last_index):
                if quality == QUALITY_ARB:
                    break
                for j in range(i + 1, last_index):
                    if y_points[i] < y_points[j]:
                        if quality in [QUALITY_CONS, QUALITY_MONO]:
                            quality = QUALITY_MONO
                        elif quality == QUALITY_ANTI:
                            quality = QUALITY_ARB
                            break
                    elif y_points[i] > y_points[j]:
                        if quality in [QUALITY_CONS, QUALITY_ANTI]:
                            quality = QUALITY_ANTI
                        elif quality == QUALITY_MONO:
                            quality = QUALITY_ARB
                            break

            y_mean: float = mean(y_points[first_index:last_index])
            half_gran: float = granularity // 2
            statement: tuple = (a, (current, end), quality, (y_mean - half_gran, y_mean + half_gran), b)
            statements.append(statement)

            current += 2 / 3 * granularity

        for i in range(len(statements) - 1):
            current: tuple = statements[i]
            neighbor: tuple = statements[i + 1]

            if current[3][1] < neighbor[3][0]:
                statements[i] = (current[0], current[1], current[2], (current[3][0], neighbor[3][0] + granularity // 2),
                                 current[4])
            elif current[3][0] > neighbor[3][1]:
                statements[i] = (current[0], current[1], current[2], (neighbor[3][1] - granularity // 2, current[3][1]),
                                 current[4])

        model.extend(statements)
    return model


def _read_csv(name: str):
    dir_name = os.path.dirname
    parent_dir: str = dir_name(dir_name(os.path.realpath(__file__)))
    path: str = os.path.join(parent_dir, "data", f"{name}.csv")
    data: list[tuple[tuple[str, str], list[tuple[float, float]]]] = []
    with open(path, encoding="utf-8-sig") as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for i, row in enumerate(reader):
            clean_row: list[str] = [elem.strip() for elem in row]
            assert len(clean_row) % 2 == 0, "Couldn't read csv correctly"

            for j in range(0, len(clean_row), 2):
                if i == 0:
                    data.append(((clean_row[j], clean_row[j + 1]), []))
                    continue
                index = j // 2
                data[index][1].append((float(clean_row[j]), float(clean_row[j + 1])))

    for influence in data:
        influence[1].sort(key=lambda x: x[0])
    return data
