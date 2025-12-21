from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Action:
    """
    Действие, которое нужно выполнить в игре.

    kind: сейчас используем только "left"
    x, y: координаты на экране (в пикселях) куда кликнуть
    r, c: координаты клетки в матрице (row/col) — удобно для дебага
    reason: объяснение, почему клик безопасен
    """
    kind: str   # "left"
    x: int
    y: int
    r: int
    c: int
    reason: str


def neighbors8(r: int, c: int, rows: int, cols: int):
    """Итератор по 8 соседям клетки (r,c) в пределах поля."""
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < cols:
                yield rr, cc


def cell_center_to_screen(
    LEFT: int, TOP: int, WIDTH: int, HEIGHT: int,
    COLS: int, ROWS: int,
    r: int, c: int
) -> Tuple[int, int]:
    """
    Переводит координаты клетки (r,c) в координаты центра клетки на экране (x,y).
    """
    cell_w = WIDTH / COLS
    cell_h = HEIGHT / ROWS
    x = int(LEFT + (c + 0.5) * cell_w)
    y = int(TOP + (r + 0.5) * cell_h)
    return x, y


def solver_step_left_only(
    field: List[List[int]],
    mine: List[List[int]],
    LEFT: int, TOP: int, WIDTH: int, HEIGHT: int,
    COLS: int, ROWS: int,
) -> Tuple[List[Action], bool]:
    """
    Делает один логический проход.

    field[r][c]:
      -1 = закрыта
       0 = пустая открытая
      1..8 = цифра

    mine[r][c]:
      -1 = неизвестно
       0 = точно не мина (открытая клетка)
       1 = считаем миной (внутр. отметка, НЕ флаг в игре)

    Возвращает:
      actions: список безопасных LEFT кликов
      changed: True если мы внутренне пометили новые мины
    """
    actions: List[Action] = []
    changed = False

    # (A) Сначала — помечаем мины внутренне по правилу m + u == v
    for r in range(ROWS):
        for c in range(COLS):
            v = field[r][c]
            if not (1 <= v <= 8):
                continue

            unk = []
            m = 0
            for rr, cc in neighbors8(r, c, ROWS, COLS):
                if mine[rr][cc] == 1:
                    m += 1
                elif field[rr][cc] == -1 and mine[rr][cc] != 1:
                    unk.append((rr, cc))

            need = v - m
            if need < 0:
                raise RuntimeError(f"Contradiction at {(r, c)}: m={m} > v={v}")
            if need > len(unk):
                raise RuntimeError(f"Contradiction at {(r, c)}: need={need} > u={len(unk)}")

            # Все неизвестные обязаны быть минами
            if unk and (m + len(unk) == v):
                for rr, cc in unk:
                    if mine[rr][cc] != 1:
                        mine[rr][cc] = 1
                        changed = True

    # (B) Затем — выдаём безопасные клетки по правилу m == v
    safe_set = set()  # чтобы не дублировать клики

    for r in range(ROWS):
        for c in range(COLS):
            v = field[r][c]
            if not (1 <= v <= 8):
                continue

            unk = []
            m = 0
            for rr, cc in neighbors8(r, c, ROWS, COLS):
                if mine[rr][cc] == 1:
                    m += 1
                elif field[rr][cc] == -1 and mine[rr][cc] != 1:
                    unk.append((rr, cc))

            need = v - m
            if need < 0:
                raise RuntimeError(f"Contradiction at {(r, c)}: m={m} > v={v}")
            if need > len(unk):
                raise RuntimeError(f"Contradiction at {(r, c)}: need={need} > u={len(unk)}")

            # Если мин уже столько же, сколько нужно — все остальные закрытые соседи безопасны
            if unk and (m == v):
                for rr, cc in unk:
                    if (rr, cc) in safe_set:
                        continue
                    safe_set.add((rr, cc))

                    x, y = cell_center_to_screen(LEFT, TOP, WIDTH, HEIGHT, COLS, ROWS, rr, cc)
                    actions.append(Action(
                        kind="left",
                        x=x, y=y,
                        r=rr, c=cc,
                        reason=f"Safe because neighbor digit at {(r, c)} has m==v ({m}=={v})"
                    ))

    return actions, changed
