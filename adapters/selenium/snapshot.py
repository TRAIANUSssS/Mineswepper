from typing import List
from selenium.webdriver.remote.webdriver import WebDriver

def get_class_snapshot(driver: WebDriver, rows: int, cols: int) -> List[str]:
    """
    Возвращает список длиной rows*cols:
      snapshot[r*cols + c] = className клетки (строка)
    Клетки привязываем по data-x/data-y (x=col, y=row).
    """
    return driver.execute_script(
        """
        const rows = arguments[0], cols = arguments[1];
        const area = document.getElementById('AreaBlock');
        if (!area) return null;

        const els = area.querySelectorAll('[data-x][data-y]');
        const out = new Array(rows * cols).fill("");

        for (let i = 0; i < els.length; i++) {
          const el = els[i];
          const x = parseInt(el.dataset.x, 10);
          const y = parseInt(el.dataset.y, 10);
          if (Number.isFinite(x) && Number.isFinite(y) && x >= 0 && x < cols && y >= 0 && y < rows) {
            out[y * cols + x] = el.className || "";
          }
        }
        return out;
        """,
        rows, cols
    )
