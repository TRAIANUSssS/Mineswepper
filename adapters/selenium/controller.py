from typing import Iterable, Tuple
from selenium.webdriver.remote.webdriver import WebDriver


def click_action(cells_2d, action):
    """
    Action из core/types.py: kind="open", r,c
    """
    cells_2d[action.r][action.c].click()


def clear_highlights(driver, cells_2d):
    flat = [cells_2d[r][c] for r in range(len(cells_2d)) for c in range(len(cells_2d[0]))]
    driver.execute_script("""
        arguments[0].forEach(el => {
            el.style.boxShadow = '';
            el.style.borderRadius = '';
        });
    """, flat)

def highlight_cells(driver, cells_2d, safe_cells, mine_cells):
    clear_highlights(driver, cells_2d)

    # зелёная "заливка" для safe
    for r, c in safe_cells:
        el = cells_2d[r][c]
        driver.execute_script("""
            const el = arguments[0];
            el.style.borderRadius = '4px';
            el.style.boxShadow = 'inset 0 0 0 9999px rgba(0, 200, 83, 0.25)';
        """, el)

    # красная "заливка" для mine
    for r, c in mine_cells:
        el = cells_2d[r][c]
        driver.execute_script("""
            const el = arguments[0];
            el.style.borderRadius = '4px';
            el.style.boxShadow = 'inset 0 0 0 9999px rgba(213, 0, 0, 0.25)';
        """, el)
