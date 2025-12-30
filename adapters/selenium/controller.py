from typing import Iterable, Tuple, Set
from selenium.webdriver.remote.webdriver import WebDriver


def click_action(driver: WebDriver, action):
    """
    Надёжный левый клик по клетке (data-x=col, data-y=row).
    Делает mousedown+mouseup+click, потому что игра часто реагирует именно на mousedown.
    """
    res = driver.execute_script(
        """
        const x = arguments[0], y = arguments[1];

        const el = document.querySelector(`#AreaBlock [data-x="${x}"][data-y="${y}"]`);
        if (!el) return { ok: false, reason: "not_found" };

        // на всякий: чтобы элемент был в видимой области
        el.scrollIntoView({block: "center", inline: "center"});

        const rect = el.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top  + rect.height / 2;

        const opts = {
          bubbles: true,
          cancelable: true,
          view: window,
          clientX: cx,
          clientY: cy,
          button: 0
        };

        el.dispatchEvent(new MouseEvent("mousedown", opts));
        el.dispatchEvent(new MouseEvent("mouseup", opts));
        el.dispatchEvent(new MouseEvent("click", opts));

        return { ok: true, cls: el.className };
        """,
        action.c,  # data-x = col
        action.r,  # data-y = row
    )

    if not res or not res.get("ok"):
        raise RuntimeError(f"click_action failed: {res}")


def clear_highlights(driver: WebDriver):
    driver.execute_script("""
        const area = document.getElementById('AreaBlock');
        if (!area) return;
        const els = area.querySelectorAll('[data-x][data-y]');
        for (const el of els) {
            el.style.boxShadow = '';
            el.style.borderRadius = '';
        }
    """)


def highlight_cells(
    driver: WebDriver,
    safe_cells: Iterable[Tuple[int, int]],
    mine_cells: Iterable[Tuple[int, int]],
    risk_cells: Iterable[Tuple[int, int]],
    prev: Set[Tuple[int, int]],
):
    safe_cells = set(safe_cells)
    mine_cells = set(mine_cells)
    risk_cells = set(risk_cells)

    # приоритет: красный (mine) перекрывает всё, зелёный перекрывает жёлтый
    risk_cells -= safe_cells
    risk_cells -= mine_cells
    safe_cells -= mine_cells

    now = safe_cells | mine_cells | risk_cells
    to_clear = prev - now

    driver.execute_script(
        """
        const safe = arguments[0];
        const mines = arguments[1];
        const risk = arguments[2];
        const clear = arguments[3];

        function getEl(x,y){
          return document.querySelector(`#AreaBlock [data-x="${x}"][data-y="${y}"]`);
        }
        function clearEl(el){
          if (!el) return;
          el.style.boxShadow = '';
          el.style.borderRadius = '';
        }
        function mark(el, rgba){
          if (!el) return;
          el.style.borderRadius = '4px';
          el.style.boxShadow = `inset 0 0 0 9999px ${rgba}`;
        }

        // clear old
        for (let i=0;i<clear.length;i++){
          const [x,y] = clear[i];
          clearEl(getEl(x,y));
        }

        // risk yellow
        for (let i=0;i<risk.length;i++){
          const [x,y] = risk[i];
          mark(getEl(x,y), 'rgba(255, 214, 0, 0.25)');
        }

        // safe green
        for (let i=0;i<safe.length;i++){
          const [x,y] = safe[i];
          mark(getEl(x,y), 'rgba(0, 200, 83, 0.25)');
        }

        // mines red
        for (let i=0;i<mines.length;i++){
          const [x,y] = mines[i];
          mark(getEl(x,y), 'rgba(213, 0, 0, 0.25)');
        }
        """,
        [[c, r] for (r, c) in safe_cells],
        [[c, r] for (r, c) in mine_cells],
        [[c, r] for (r, c) in risk_cells],
        [[c, r] for (r, c) in to_clear],
    )

    prev.clear()
    prev.update(now)