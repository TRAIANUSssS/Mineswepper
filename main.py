import time
import pyautogui

from detect_fields import Detection
from get_field import screenshot_region, split_grid_np

from board_reader import update_board_from_grid
from solver import solver_step_left_only
from debug_prints import print_field, print_mines, print_actions
from clicker import click_action

pyautogui.FAILSAFE = True

pixel_area = {"small": [735, 427, 450, 360], "medium": [690, 397, 540, 420]}
field_count = {"small": [10, 8], "medium": [18, 14]}
max_moves = {"small": 20, "medium":80}


def run_once(preset, detection, field_prev=None, mine_prev=None, save_debug=False):
    LEFT, TOP, WIDTH, HEIGHT = pixel_area[preset]
    COLS, ROWS = field_count[preset]

    # (РЕКОМЕНДУЮ) Уводим мышь с поля, чтобы не было подсветки клеток
    pyautogui.moveTo(1, 1)

    img = screenshot_region(LEFT, TOP, WIDTH, HEIGHT)
    if save_debug:
        img.save("region.png")
        print("Saved: region.png")

    grid = split_grid_np(img, COLS, ROWS)

    field, mine = update_board_from_grid(grid, detection, field_prev, mine_prev)

    actions, changed = solver_step_left_only(field, mine, LEFT, TOP, WIDTH, HEIGHT, COLS, ROWS)

    return field, mine, actions


if __name__ == "__main__":
    preset = "medium"
    detection = Detection()

    field = None
    mine = None

    print("Switch to the browser window with Minesweeper. Starting in 3 seconds...")
    time.sleep(3)

    moves = 0
    while moves < max_moves[preset]:
        try:
            field, mine, actions = run_once(preset, detection, field, mine, save_debug=False)
        except RuntimeError as e:
            # Если всё-таки поймали противоречие — это почти всегда hover/артефакт.
            # Просто пропускаем итерацию (мышь уже уводим), можно сделать small sleep.
            print("WARN:", e)
            time.sleep(0.2)
            continue

        print_field(field)
        print_mines(mine)
        print_actions(actions, limit=10)

        if not actions:
            print("No deterministic actions. Stop.")
            break

        for action in actions:
            print("NEXT:", action)

            click_action(action, pre_delay=0.01, post_delay=0.01)
        moves += 1

    if moves == max_moves[preset]:
        print("Все сломалось")
    else:
        print("готово")
