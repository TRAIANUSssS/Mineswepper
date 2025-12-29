import time
import pyautogui

from adapters.vision.detect_fields import Detection
from adapters.vision.get_field import screenshot_region, split_grid_np
from adapters.vision.board_reader import update_board_from_grid
from core.solver import solver_step, Action
from utils.debug_prints import print_field, print_mines, print_actions
from adapters.vision.clicker import click_action

pyautogui.FAILSAFE = True

# -------------------- presets --------------------

pixel_area = {
    "small":  [735, 427, 450, 360],
    "medium": [690, 397, 540, 420],
    "hard": [660, 357, 600, 500]
}

field_count = {
    "small":  [10, 8],
    "medium": [18, 14],
    "hard": [24, 20]  # пример, если понадобится
}

total_mines = {"small": 10, "medium": 40, "hard": 99}
max_moves = {"small": 200, "medium": 800, "hard": 2000}

# -------------------- helpers --------------------

def is_all_closed(field) -> bool:
    """True если все клетки = -1 (полностью закрытое поле)."""
    return field is not None and all(v == -1 for row in field for v in row)

def center_action(LEFT, TOP, WIDTH, HEIGHT, COLS, ROWS) -> Action:
    """Стартовый клик в центре поля."""
    r = ROWS // 2
    c = COLS // 2
    cell_w = WIDTH / COLS
    cell_h = HEIGHT / ROWS
    x = int(LEFT + (c + 0.5) * cell_w)
    y = int(TOP + (r + 0.5) * cell_h)
    return Action(kind="left", r=r, c=c, reason="START: click center")

def capture_and_solve(preset: str, detection: Detection, field_prev=None, mine_prev=None, save_debug=False):
    """
    1) уводим мышь
    2) скрин -> нарезка -> распознавание (с кешем)
    3) solver -> actions
    """
    LEFT, TOP, WIDTH, HEIGHT = pixel_area[preset]
    COLS, ROWS = field_count[preset]

    # чтобы hover не портил распознавание
    pyautogui.moveTo(1, 1)

    img = screenshot_region(LEFT, TOP, WIDTH, HEIGHT)
    if save_debug:
        img.save("region.png")
        print("Saved: region.png")

    grid = split_grid_np(img, COLS, ROWS)
    field, mine = update_board_from_grid(grid, detection, field_prev, mine_prev)

    # если это самый старт (всё закрыто) — возвращаем центр-клик
    if is_all_closed(field):
        return field, mine, [center_action(LEFT, TOP, WIDTH, HEIGHT, COLS, ROWS)]

    actions, changed = solver_step(field, mine, total_mines=total_mines.get(preset))
    return field, mine, actions

def run_game(preset: str, save_debug=False, pre_start_delay=2.0):
    detection = Detection()
    field = None
    mine = None

    print(f"Preset: {preset}. Switch to the browser window. Starting in {pre_start_delay} seconds...")
    time.sleep(pre_start_delay)

    for step in range(max_moves.get(preset, 1000)):
        try:
            field, mine, actions = capture_and_solve(preset, detection, field, mine, save_debug=save_debug)
        except RuntimeError as e:
            # Обычно это hover/артефакт распознавания. Просто пропускаем тик.
            print("WARN:", e)
            time.sleep(0.05)
            continue

        print_field(field)
        print_mines(mine)
        print_actions(actions, limit=10)

        if not actions:
            print("No actions. Stop.")
            return

        # Ты хотел не ограничивать actions — ок.
        # На практике можно оставить так: все безопасные клики подряд.

        LEFT, TOP, WIDTH, HEIGHT = pixel_area[preset]
        COLS, ROWS = field_count[preset]


        for a in actions[:5]:
            print("NEXT:", a)
            click_action(a, LEFT, TOP, WIDTH, HEIGHT, COLS, ROWS, pre_delay=0.01, post_delay=0.01)

    print("Reached max_moves — stop.")

# -------------------- entry --------------------

if __name__ == "__main__":
    # small medium hard
    run_game("medium", save_debug=False, pre_start_delay=2.0)
