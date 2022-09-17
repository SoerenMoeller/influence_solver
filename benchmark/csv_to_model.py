import bisect
import csv
import os

from solver.constants import QUALITY_CONS, QUALITY_ANTI, QUALITY_MONO
from solver.util import quality_add


def create_linear_function(x_1: float, y_1: float, x_2: float, y_2: float):
    pitch: float = (y_2 - y_1) / (x_2 - x_1)

    def f(x: float) -> float:
        return pitch * x + y_2 - pitch * x_2

    return f, pitch


def get_quality_from_pitch(pitch: float) -> str:
    if pitch == 0:
        return QUALITY_CONS
    elif pitch < 0:
        return QUALITY_ANTI
    return QUALITY_MONO


def get_y(points: list[tuple[float, float]], current: float, end: float) -> tuple[float, str]:
    lower_bound: int = bisect.bisect_left(points, current, key=lambda e: e[0])
    upper_bound: int = bisect.bisect_right(points, end, key=lambda e: e[0])
    x: float = (current + end) / 2
    index: int = bisect.bisect_left(points, x, key=lambda e: e[0])

    if x != points[lower_bound][0] and lower_bound > 0:
        lower_bound -= 1
    if x != points[index][0] and index > 0:
        index -= 1
    if end == points[upper_bound - 1][0] and upper_bound - 1 > 0:
        upper_bound -= 1

    quality: str = QUALITY_CONS
    for i in range(lower_bound, upper_bound):
        x_1, y_1 = points[i]
        x_2, y_2 = points[i + 1]
        f, pitch = create_linear_function(x_1, y_1, x_2, y_2)

        other_quality: str = get_quality_from_pitch(pitch)
        quality = quality_add(quality, other_quality)

    x_1, y_1 = points[index]
    x_2, y_2 = points[index + 1]
    f, pitch = create_linear_function(x_1, y_1, x_2, y_2)

    return f(x), quality


def build_model_from_csv(name: str, width_amount: int, height_amount: int) -> list[tuple]:
    data: list[tuple[tuple, list[tuple]]] = _read_csv(name)

    model: list[tuple] = []
    for influence in data:
        a, b = influence[0]
        points: list[tuple] = influence[1]
        assert points, "Empty data"

        x_points: list[float] = [p[0] for p in points]
        greatest_end: float = x_points[-1]
        smallest_start: float = x_points[0]
        granularity_x: float = (greatest_end - smallest_start) / width_amount
        granularity_y: float = 300
        current: float = smallest_start
        statements: list[tuple] = []
        while True:
            end: float = current + granularity_x
            if end > greatest_end:
                end = greatest_end
            if current > greatest_end or current == end:
                break

            y, quality = get_y(points, current, end)
            half_gran: float = granularity_y // 2
            statement: tuple = (a, (current, end), quality, (y - half_gran, y + half_gran), b)
            statements.append(statement)

            current += 2 / 3 * granularity_x
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
