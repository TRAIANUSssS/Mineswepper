import time
import pyautogui
from typing import Tuple

# Если увести мышь в левый верхний угол — pyautogui выбросит исключение и остановит скрипт.
pyautogui.FAILSAFE = True


def rc_to_xy(
    LEFT: int, TOP: int, WIDTH: int, HEIGHT: int,
    COLS: int, ROWS: int,
    r: int, c: int
) -> Tuple[int, int]:
    cell_w = WIDTH / COLS
    cell_h = HEIGHT / ROWS
    x = int(LEFT + (c + 0.5) * cell_w)
    y = int(TOP + (r + 0.5) * cell_h)
    return x, y


def click_action(
    action,
    LEFT: int, TOP: int, WIDTH: int, HEIGHT: int,
    COLS: int, ROWS: int,
    pre_delay: float = 0.1,
    post_delay: float = 0.1
):
    """
    Кликает по клетке action.r/action.c (Action из core/types.py),
    переводя координаты клетки в экранные x/y.
    """
    time.sleep(pre_delay)

    x, y = rc_to_xy(LEFT, TOP, WIDTH, HEIGHT, COLS, ROWS, action.r, action.c)

    # В новой архитектуре лучше использовать kind="open".
    # Но поддержим и старые "left/right" на всякий.
    kind = getattr(action, "kind", "open")

    if kind in ("open", "left"):
        pyautogui.click(x, y, button="left")
    elif kind == "right":
        pyautogui.click(x, y, button="right")
    else:
        raise ValueError(f"Unknown action kind: {kind}")

    time.sleep(post_delay)
