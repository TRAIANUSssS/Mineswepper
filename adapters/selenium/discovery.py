import re
from dataclasses import dataclass
from typing import List, Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@dataclass
class BoardMeta:
    rows: int
    cols: int
    total_mines: int


_DIGIT_RE = re.compile(r"hdd_top-area-num(\d)")


def _digit_from_class(el) -> int:
    cls = (el.get_attribute("class") or "")
    m = _DIGIT_RE.search(cls)
    return int(m.group(1)) if m else 0


def read_total_mines(driver: WebDriver) -> int:
    def get_by_id(id_):
        try:
            return driver.find_element(By.ID, id_)
        except Exception:
            return None

    e100 = get_by_id("top_area_mines_100")
    e10  = get_by_id("top_area_mines_10")
    e1   = get_by_id("top_area_mines_1")

    d100 = _digit_from_class(e100) if e100 else 0
    d10  = _digit_from_class(e10) if e10 else 0
    d1   = _digit_from_class(e1) if e1 else 0
    return 100 * d100 + 10 * d10 + d1


def discover_board_meta(driver: WebDriver, wait_sec: float = 10.0) -> BoardMeta:
    WebDriverWait(driver, wait_sec).until(EC.presence_of_element_located((By.ID, "AreaBlock")))

    area = driver.find_element(By.ID, "AreaBlock")
    flat = area.find_elements(By.CSS_SELECTOR, "[data-x][data-y]")
    if not flat:
        raise RuntimeError("No cells found: #AreaBlock [data-x][data-y]")

    max_x = -1
    max_y = -1
    for el in flat:
        cx = int(el.get_attribute("data-x"))
        cy = int(el.get_attribute("data-y"))
        if cx > max_x: max_x = cx
        if cy > max_y: max_y = cy

    cols = max_x + 1
    rows = max_y + 1
    total_mines = read_total_mines(driver)
    return BoardMeta(rows=rows, cols=cols, total_mines=total_mines)


def get_cells_2d(driver: WebDriver, rows: int, cols: int):
    """
    Каждый тик заново собираем матрицу [rows][cols] по data-x/data-y.
    """
    area = driver.find_element(By.ID, "AreaBlock")
    flat = area.find_elements(By.CSS_SELECTOR, "[data-x][data-y]")

    cells = [[None for _ in range(cols)] for _ in range(rows)]
    for el in flat:
        c = int(el.get_attribute("data-x"))
        r = int(el.get_attribute("data-y"))
        if 0 <= r < rows and 0 <= c < cols:
            cells[r][c] = el

    missing = sum(1 for r in range(rows) for c in range(cols) if cells[r][c] is None)
    if missing:
        raise RuntimeError(f"get_cells_2d: missing {missing} cells. Selector may be wrong.")

    return cells
