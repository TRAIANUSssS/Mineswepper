import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from adapters.selenium.create_driver import make_driver
from core.solver import solver_step
from utils.debug_prints import print_field, print_mines, print_actions

from adapters.selenium.discovery import discover_board_meta
from adapters.selenium.snapshot import get_class_snapshot
from adapters.selenium.board_reader import read_board_from_snapshot
from adapters.selenium.controller import click_action, highlight_cells, clear_highlights

START_URL = "https://minesweeper.online/new-game"


def get_game_status(driver) -> str:
    """
    "playing" | "win" | "loss" | "unknown"
    """
    try:
        el = driver.find_element(By.ID, "top_area_face")
    except NoSuchElementException:
        return "unknown"

    cls = (el.get_attribute("class") or "").lower()
    if "hdd_top-area-face-win" in cls:
        return "win"
    if "hdd_top-area-face-loss" in cls or "hdd_top-area-face-lose" in cls:
        return "loss"
    if "hdd_top-area-face-unpressed" in cls:
        return "playing"
    return "unknown"


def wait_for_user_ready() -> bool:
    """
    Возвращает False если пользователь хочет выйти.
    """
    cmd = input("When the board is ready, press Enter to start (or 'q' to quit): ").strip().lower()
    return cmd != "q"


def run(mode: str = "highlight", tick_sleep: float = 0.2, click_sleep: float = 0.01):
    """
    mode:
      - "auto"      : кликает сам
      - "highlight" : подсветка, ты кликаешь сам, бот обновляет каждые tick_sleep
    """
    driver = make_driver(START_URL)

    print("Browser opened. Choose a game manually (URL can change).")
    if not wait_for_user_ready():
        driver.quit()
        return

    meta = discover_board_meta(driver)
    rows, cols, total_mines = meta.rows, meta.cols, meta.total_mines
    print(f"Detected board: {cols}x{rows}, total_mines={total_mines}")

    field = None
    mine = None

    # для highlight-режима: чтобы не чистить всё поле каждый тик
    prev_highlight = set()

    while True:
        status = get_game_status(driver)
        if status in ("win", "loss"):
            print(f"Game finished: {status}.")
            clear_highlights(driver)
            prev_highlight.clear()

            field = None
            mine = None

            if not wait_for_user_ready():
                break

            meta = discover_board_meta(driver)
            rows, cols, total_mines = meta.rows, meta.cols, meta.total_mines
            print(f"Detected board: {cols}x{rows}, total_mines={total_mines}")
            continue

        t0 = time.time()

        # 1) Быстрый snapshot всех классов клеток
        snapshot = get_class_snapshot(driver, rows, cols)
        if snapshot is None or len(snapshot) != rows * cols:
            # если страница ещё не готова/перерендер — просто подождём
            time.sleep(tick_sleep)
            continue

        t_snapshot = time.time()

        # 2) Парсим в field/mine (с кешем открытых клеток)
        field, mine = read_board_from_snapshot(snapshot, rows, cols, field_prev=field, mine_prev=mine)
        t_read = time.time()

        # 3) Solver
        actions, changed = solver_step(field, mine, total_mines=total_mines)
        t_solve = time.time()

        # debug
        print_field(field)
        print_mines(mine)
        print_actions(actions, limit=10)

        # safe / mines (internal)
        safe_cells = [(a.r, a.c) for a in actions if "SAFE" in (a.reason or "")]
        mine_cells = [(r, c) for r in range(rows) for c in range(cols) if mine[r][c] == 1]
        risk_cells = [(a.r, a.c) for a in actions if
                      (getattr(a, "risk", None) is not None) or ("MIN-RISK" in (a.reason or ""))]

        highlight_cells(driver, safe_cells, mine_cells, risk_cells, prev_highlight)
        t_high = time.time()

        # тайминги
        print("timing:",
              "snapshot", round(t_snapshot - t0, 4),
              "read", round(t_read - t_snapshot, 4),
              "solve", round(t_solve - t_read, 4),
              "highlight", round(t_high - t_solve, 4))

        if mode != "highlight":
            # AUTO
            if not actions:
                print("No actions. Stop.")
                break

            for a in actions:
                click_action(driver, a)  # JS click by data-x/data-y
                time.sleep(click_sleep)

        # маленькая пауза чтобы DOM успел обновиться
        time.sleep(tick_sleep)

    driver.quit()


if __name__ == "__main__":
    run(mode="highlight", tick_sleep=0.2)
