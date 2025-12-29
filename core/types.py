from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass(frozen=True)
class Action:
    kind: str           # "open" (только левый клик)
    r: int
    c: int
    reason: str
    risk: Optional[float] = None  # для min-risk

@dataclass
class BoardState:
    rows: int
    cols: int
    total_mines: Optional[int]
    field: List[List[int]]  # -1 closed, 0 empty, 1..8 digits
    mine: List[List[int]]   # -1 unknown, 0 not mine/open, 1 mine (internal)
