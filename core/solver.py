from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from core.types import Action  # поправь путь под свою структуру


# -------------------- helpers --------------------

def neighbors8(r: int, c: int, rows: int, cols: int):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < cols:
                yield rr, cc


@dataclass
class Constraint:
    r: int
    c: int
    v: int
    U: Set[Tuple[int, int]]
    need: int


def build_constraints(field: List[List[int]], mine: List[List[int]]) -> List[Constraint]:
    rows = len(field)
    cols = len(field[0]) if rows else 0

    cons: List[Constraint] = []
    for r in range(rows):
        for c in range(cols):
            v = field[r][c]
            if not (1 <= v <= 8):
                continue

            U: Set[Tuple[int, int]] = set()
            m = 0

            for rr, cc in neighbors8(r, c, rows, cols):
                if mine[rr][cc] == 1:
                    m += 1
                elif field[rr][cc] == -1 and mine[rr][cc] != 1:
                    U.add((rr, cc))

            need = v - m
            if need < 0:
                raise RuntimeError(f"Contradiction at {(r, c)}: m={m} > v={v}")
            if need > len(U):
                raise RuntimeError(f"Contradiction at {(r, c)}: need={need} > u={len(U)}")

            if U:
                cons.append(Constraint(r=r, c=c, v=v, U=U, need=need))

    return cons


def apply_basic_rules(cons: List[Constraint], mine: List[List[int]]) -> Tuple[bool, Set[Tuple[int, int]]]:
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
    safe: Set[Tuple[int, int]] = set()
    changed_mines = False

    n = len(cons)
    for i in range(n):
        A = cons[i]
        for j in range(n):
            if i == j:
                continue
            B = cons[j]

            if not A.U.issubset(B.U):
                continue

            D = B.U - A.U
            if not D:
                continue

            k = B.need - A.need
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


def propagate_deterministic(field: List[List[int]], mine: List[List[int]], max_iters: int = 50) -> Tuple[bool, Set[Tuple[int, int]]]:
    overall_changed = False
    overall_safe: Set[Tuple[int, int]] = set()

    for _ in range(max_iters):
        cons = build_constraints(field, mine)

        changed1, safe1 = apply_basic_rules(cons, mine)
        changed2, safe2 = apply_subset_rule(cons, mine)

        overall_safe |= safe1
        overall_safe |= safe2

        if changed1 or changed2:
            overall_changed = True
            continue
        break

    return overall_changed, overall_safe


def estimate_risk_map(
    field: List[List[int]],
    mine: List[List[int]],
    total_mines: Optional[int] = None,
) -> Dict[Tuple[int, int], float]:
    cons = build_constraints(field, mine)
    rows = len(field)
    cols = len(field[0]) if rows else 0

    risk: Dict[Tuple[int, int], float] = {}
    for cst in cons:
        p = cst.need / len(cst.U)
        for cell in cst.U:
            risk[cell] = max(risk.get(cell, 0.0), p)

    if total_mines is not None:
        flagged = sum(1 for r in range(rows) for c in range(cols) if mine[r][c] == 1)
        mines_left = max(0, total_mines - flagged)

        unknown = [(r, c) for r in range(rows) for c in range(cols) if field[r][c] == -1 and mine[r][c] != 1]
        if unknown:
            p_global = mines_left / len(unknown)
            for cell in unknown:
                risk.setdefault(cell, p_global)

    return risk


def pick_min_risk_action(field: List[List[int]], mine: List[List[int]], total_mines: Optional[int]) -> Optional[Action]:
    risk = estimate_risk_map(field, mine, total_mines=total_mines)
    if not risk:
        return None

    (r, c), p = min(risk.items(), key=lambda kv: kv[1])
    return Action(kind="open", r=r, c=c, reason="MIN-RISK guess", risk=float(p))


def solver_step(
    field: List[List[int]],
    mine: List[List[int]],
    total_mines: Optional[int] = None,
) -> Tuple[List[Action], bool]:
    """
    Универсальный solver без UI:
    - возвращает список safe действий (open r,c)
    - если safe нет, возвращает один min-risk guess
    """
    changed, safe = propagate_deterministic(field, mine)

    actions: List[Action] = []
    for (r, c) in sorted(safe):
        if field[r][c] == -1 and mine[r][c] != 1:
            actions.append(Action(kind="open", r=r, c=c, reason="SAFE (deterministic)"))

    if not actions:
        guess = pick_min_risk_action(field, mine, total_mines=total_mines)
        if guess is not None:
            actions.append(guess)

    return actions, changed
