from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class Action:
    """
    Действие, которое нужно выполнить в игре.

    kind: используем "left"
    x, y: координаты на экране (в пикселях) куда кликнуть
    r, c: координаты клетки в матрице (row/col) — удобно для дебага
    reason: объяснение
    """
    kind: str   # "left"
    x: int
    y: int
    r: int
    c: int
    reason: str


# -------------------- geometry / neighbors --------------------

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


# -------------------- constraint building --------------------

@dataclass
class Constraint:
    """Ограничение от одной цифры: среди U мин ровно need."""
    r: int
    c: int
    v: int
    U: Set[Tuple[int, int]]
    need: int


def build_constraints(field: List[List[int]], mine: List[List[int]], ROWS: int, COLS: int) -> List[Constraint]:
    cons: List[Constraint] = []
    for r in range(ROWS):
        for c in range(COLS):
            v = field[r][c]
            if not (1 <= v <= 8):
                continue

            U: Set[Tuple[int, int]] = set()
            m = 0

            for rr, cc in neighbors8(r, c, ROWS, COLS):
                if mine[rr][cc] == 1:
                    m += 1
                elif field[rr][cc] == -1 and mine[rr][cc] != 1:
                    U.add((rr, cc))

            need = v - m

            # противоречия
            if need < 0:
                raise RuntimeError(f"Contradiction at {(r, c)}: m={m} > v={v}")
            if need > len(U):
                raise RuntimeError(f"Contradiction at {(r, c)}: need={need} > u={len(U)}")

            if U:
                cons.append(Constraint(r=r, c=c, v=v, U=U, need=need))

    return cons


# -------------------- deterministic propagation --------------------

def apply_basic_rules(cons: List[Constraint], mine: List[List[int]]) -> Tuple[bool, Set[Tuple[int, int]]]:
    """
    Базовые правила:
      1) need == 0  => все клетки из U безопасны
      2) need == |U| => все клетки из U - мины (внутренне помечаем)
    Возвращает:
      - changed_mines: были ли новые мины
      - safe_cells: множество безопасных клеток
    """
    safe: Set[Tuple[int, int]] = set()
    changed_mines = False

    for cst in cons:
        if cst.need == 0:
            safe |= cst.U
        elif cst.need == len(cst.U):
            for rr, cc in cst.U:
                if mine[rr][cc] != 1:
                    mine[rr][cc] = 1
                    changed_mines = True

    return changed_mines, safe


def apply_subset_rule(cons: List[Constraint], mine: List[List[int]]) -> Tuple[bool, Set[Tuple[int, int]]]:
    r"""
    Subset правило:
    если U(A) ⊆ U(B), то на D = U(B)\U(A) мин ровно need(B)-need(A)

    - если k=0 => D безопасны
    - если k=|D| => D мины

    Возвращает:
      - changed_mines
      - safe_cells
    """
    safe: Set[Tuple[int, int]] = set()
    changed_mines = False

    n = len(cons)
    for i in range(n):
        A = cons[i]
        UA = A.U
        needA = A.need
        for j in range(n):
            if i == j:
                continue
            B = cons[j]
            UB = B.U
            needB = B.need

            if not UA.issubset(UB):
                continue

            D = UB - UA
            if not D:
                continue

            k = needB - needA
            # Если тут вылетает - обычно распознавание поехало (или mine рассинхрон)
            if k < 0 or k > len(D):
                raise RuntimeError(
                    f"Subset contradiction: {(A.r, A.c)} ⊆ {(B.r, B.c)} "
                    f"but k={k}, |D|={len(D)}"
                )

            if k == 0:
                safe |= D
            elif k == len(D):
                for rr, cc in D:
                    if mine[rr][cc] != 1:
                        mine[rr][cc] = 1
                        changed_mines = True

    return changed_mines, safe


def propagate_deterministic(
    field: List[List[int]],
    mine: List[List[int]],
    ROWS: int,
    COLS: int,
    max_iters: int = 50,
) -> Tuple[bool, Set[Tuple[int, int]]]:
    """
    Прогоняем детерминированные правила до стабилизации:
      - basic (need==0, need==|U|)
      - subset

    Возвращает:
      changed: были ли изменения mine (новые пометки мин)
      safe: множество безопасных клеток (закрытых), которые можно кликать левым
    """
    overall_changed = False
    overall_safe: Set[Tuple[int, int]] = set()

    for _ in range(max_iters):
        cons = build_constraints(field, mine, ROWS, COLS)

        changed1, safe1 = apply_basic_rules(cons, mine)
        changed2, safe2 = apply_subset_rule(cons, mine)

        overall_safe |= safe1
        overall_safe |= safe2

        if changed1 or changed2:
            overall_changed = True
            # появились новые мины => ограничения изменились => продолжаем
            continue

        # если мины больше не добавляются, safe тоже может расширяться только через cons,
        # но на следующей итерации будет то же самое => можно остановиться
        break

    return overall_changed, overall_safe


# -------------------- min-risk fallback --------------------

def estimate_risk_map(
    field: List[List[int]],
    mine: List[List[int]],
    ROWS: int,
    COLS: int,
    total_mines: Optional[int] = None,
) -> Dict[Tuple[int, int], float]:
    """
    Оценивает риск клетки быть миной.
    Для каждой цифры: p = need/|U|
    Для клетки: risk = max(p по всем цифрам, которые её видят)  (консервативно)

    + Если total_mines задан:
      - для клеток, которые не участвуют ни в одном ограничении, риск = p_global = mines_left/unknown_left
    """
    cons = build_constraints(field, mine, ROWS, COLS)

    risk: Dict[Tuple[int, int], float] = {}

    for cst in cons:
        p = cst.need / len(cst.U)
        for cell in cst.U:
            if cell in risk:
                risk[cell] = max(risk[cell], p)
            else:
                risk[cell] = p

    # Глобальная оценка для "далёких" неизвестных (не на фронтире)
    if total_mines is not None:
        flagged = sum(1 for r in range(ROWS) for c in range(COLS) if mine[r][c] == 1)
        mines_left = max(0, total_mines - flagged)

        unknown_cells = [(r, c) for r in range(ROWS) for c in range(COLS) if field[r][c] == -1 and mine[r][c] != 1]
        unknown_left = len(unknown_cells)

        if unknown_left > 0:
            p_global = mines_left / unknown_left
            for cell in unknown_cells:
                # если локальный риск неизвестен — подставим глобальный
                risk.setdefault(cell, p_global)

    return risk


def pick_min_risk_action(
    field: List[List[int]],
    mine: List[List[int]],
    LEFT: int, TOP: int, WIDTH: int, HEIGHT: int,
    COLS: int, ROWS: int,
    total_mines: Optional[int] = None,
) -> Optional[Action]:
    """
    Возвращает один "угадывающий" ход с минимальным риском.
    """
    risk = estimate_risk_map(field, mine, ROWS, COLS, total_mines=total_mines)
    if not risk:
        return None

    (r, c), p = min(risk.items(), key=lambda kv: kv[1])
    x, y = cell_center_to_screen(LEFT, TOP, WIDTH, HEIGHT, COLS, ROWS, r, c)

    return Action(
        kind="left",
        x=x, y=y,
        r=r, c=c,
        reason=f"MIN-RISK guess: p≈{p:.3f} (total_mines={total_mines})"
    )


# -------------------- public API --------------------

def solver_step_left_only(
    field: List[List[int]],
    mine: List[List[int]],
    LEFT: int, TOP: int, WIDTH: int, HEIGHT: int,
    COLS: int, ROWS: int,
    total_mines: Optional[int] = None,
) -> Tuple[List[Action], bool]:
    """
    Главная функция, которую зовёшь из main.

    Возвращает:
      actions: список кликов (все безопасные, если есть; иначе один min-risk)
      changed: True если мы внутренне пометили новые мины
    """
    changed, safe = propagate_deterministic(field, mine, ROWS, COLS)

    # превращаем safe -> actions (кликаем только по закрытым и не помеченным как мина)
    actions: List[Action] = []
    safe_sorted = sorted(safe)  # стабильный порядок для отладки

    for r, c in safe_sorted:
        if field[r][c] != -1:
            continue
        if mine[r][c] == 1:
            continue
        x, y = cell_center_to_screen(LEFT, TOP, WIDTH, HEIGHT, COLS, ROWS, r, c)
        actions.append(Action(
            kind="left",
            x=x, y=y,
            r=r, c=c,
            reason="SAFE (deterministic)"
        ))

    # Если safe-ходов нет — пробуем min-risk
    if not actions:
        guess = pick_min_risk_action(field, mine, LEFT, TOP, WIDTH, HEIGHT, COLS, ROWS, total_mines=total_mines)
        if guess is not None:
            actions.append(guess)

    return actions, changed
