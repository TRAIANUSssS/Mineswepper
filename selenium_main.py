import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from core.solver import solver_step
from utils.debug_prints import print_field, print_mines, print_actions

from adapters.selenium.discovery import discover_board_meta, get_cells_2d
from adapters.selenium.board_reader import read_board_from_cells
from adapters.selenium.controller import click_action, highlight_cells, clear_highlights

START_URL = "https://minesweeper.online/"  # сюда вставь стандартную ссылку


def get_game_status(driver) -> str:
    """
    Возвращает: "playing" | "win" | "loss" | "unknown"

    Опирается на классы:
      hdd_top-area-face-unpressed  -> playing
      hdd_top-area-face-win        -> win
      hdd_top-area-face-lose       -> loss
    """
    try:
        el = driver.find_element(By.ID, "top_area_face")
    except NoSuchElementException:
        return "unknown"

    cls = (el.get_attribute("class") or "").lower()

    if "hdd_top-area-face-win" in cls:
        return "win"
    if "hdd_top-area-face-lose" in cls:
        return "loss"
    if "hdd_top-area-face-unpressed" in cls:
        return "playing"

    return "unknown"

def wait_for_user_ready(driver):
    """
    Пользователь вручную выбирает игру/уровень/перезапускает.
    Мы ждём Enter, затем убеждаемся, что поле существует.
    """
    return input("When the board is ready, press Enter here to start the bot or 'q' for quit")



def run(mode: str = "highlight"):
    """
    mode:
      - "auto"      : сам кликает
      - "highlight" : подсветка, кликаешь сам, Enter = обновить/пересчитать
    """
    driver = webdriver.Chrome()
    driver.get(START_URL)

    print("1) Browser opened. Choose a game manually (any URL).")
    input("2) When the board is ready, press Enter here to start the bot...")

    meta = discover_board_meta(driver)
    rows, cols, total_mines = meta.rows, meta.cols, meta.total_mines

    print(f"Detected board: {cols}x{rows}, total_mines={total_mines}")

    field = None
    mine = None
    cells_2d = None

    while True:
        status = get_game_status(driver)
        if status in ("win", "loss"):
            clear_highlights(driver, cells_2d) if cells_2d else None
            print(f"Game finished: {status}. Waiting for next game... ")
            field = None
            mine = None

            cmd = wait_for_user_ready(driver)
            if cmd == "q":
                break

            # пересканиваем мета-параметры заново (размер/мины могли поменяться)
            meta = discover_board_meta(driver)
            rows, cols, total_mines = meta.rows, meta.cols, meta.total_mines
            print(f"Detected board: {cols}x{rows}, total_mines={total_mines}")
            continue
        start_time = time.time()
        cells_2d = get_cells_2d(driver, rows, cols)
        get_cells_time = time.time() - start_time
        field, mine = read_board_from_cells(cells_2d, field_prev=field, mine_prev=mine)
        read_board_time = time.time() - get_cells_time - start_time
        actions, changed = solver_step(field, mine, total_mines=total_mines)
        slove_time = time.time() - read_board_time - get_cells_time - start_time

        print_field(field)
        print_mines(mine)
        print_actions(actions, limit=10)
        print_time = time.time() - read_board_time - get_cells_time - slove_time - start_time


        safe_cells = [(a.r, a.c) for a in actions if "SAFE" in (a.reason or "")]
        mine_cells = [(r, c) for r in range(rows) for c in range(cols) if mine[r][c] == 1]

        if mode == "highlight":
            highlight_cells(driver, cells_2d, safe_cells, mine_cells)
            # cmd = input("Enter=refresh, q=quit: ").strip().lower()
            # if cmd == "q":
            #     break
            highlight_cell_time = time.time() - read_board_time - get_cells_time - slove_time - print_time - start_time
            print("get_cells_time", get_cells_time)
            print("read_board_time", read_board_time)
            print("slove_time", slove_time)
            print("print_time", print_time)
            print("highlight_cell_time", highlight_cell_time)
            wait = 0.5
            print(f"Waiting {wait} second")
            time.sleep(wait)
            continue

        # AUTO
        if not actions:
            print("No actions. Stop.")
            break

        # Можно кликать все подряд (safe + возможно 1 min-risk)
        for a in actions:
            click_action(cells_2d, a)
            time.sleep(0.01)

    driver.quit()


if __name__ == "__main__":
    run(mode="highlight")  # поменяй на "auto"
