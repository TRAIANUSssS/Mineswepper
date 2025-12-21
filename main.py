import cv2

from detect_fields import Detection
from get_field import screenshot_region, split_grid_np

from board_reader import detect_board_from_grid
from solver import solver_step_left_only
from debug_prints import print_field, print_mines, print_actions

pixel_area = {
    "small": [735, 427, 450, 360]  # LEFT, TOP, WIDTH, HEIGHT
}

field_count = {
    "small": [10, 8]  # COLS, ROWS
}


def run_once(preset="small"):
    LEFT, TOP, WIDTH, HEIGHT = pixel_area[preset]
    COLS, ROWS = field_count[preset]

    # 1) Скрин области игры
    img = screenshot_region(LEFT, TOP, WIDTH, HEIGHT)  # PIL.Image (RGB)
    img.save("region.png")
    print("Saved: region.png")

    # 2) Нарезка на клетки
    grid = split_grid_np(img, COLS, ROWS)  # [ROWS][COLS] numpy RGB
    print("Grid size:", len(grid[0]), "x", len(grid))  # cols x rows

    # 3) Распознавание поля
    detection = Detection()
    field, mine = detect_board_from_grid(grid, detection)

    print_field(field)

    # 4) Логический шаг: только левый клик
    actions, changed = solver_step_left_only(field, mine, LEFT, TOP, WIDTH, HEIGHT, COLS, ROWS)

    print_mines(mine)
    print_actions(actions, limit=10)

    return actions


if __name__ == "__main__":
    run_once("small")
