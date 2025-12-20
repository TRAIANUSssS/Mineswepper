import json
import cv2
import numpy as np


def hex_to_bgr(hex_color: str) -> np.ndarray:
    """'#RRGGBB' -> np.array([B,G,R], dtype=np.uint8)"""
    h = hex_color.lstrip("#")
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return np.array([b, g, r], dtype=np.uint8)


class Detection:
    """
    Быстрый детект клетки:
      - closed/open: по доле пикселей, похожих на цвета травы (2 оттенка)
      - есть цифра: по edge_ratio (Canny) в узком центральном ROI (digit_pad_frac)
      - какая цифра: по HSV-диапазонам (из digit_hsv_ranges.json),
        но считаем ratio только по пикселям, которые НЕ похожи на фон
        (фон = трава + коричневое открытое поле, по 2 оттенка каждого)
    """

    def __init__(
        self,
        digit_ranges_path: str = "digit_hsv_ranges.json",

        # Цвета фона (как ты написал)
        grass_hex=("#AAD751", "#A2D149"),
        open_hex=("#D7B899", "#E5C29F"),

        # ROI
        center_pad_frac: float = 0.30,   # для определения травы (open/closed)
        digit_pad_frac: float = 0.38,    # для edges и распознавания цифры

        # Похожесть на фон (в BGR)
        bg_dist_thr: int = 25,           # насколько близко к фон-цвету, чтобы считать "фон"
        grass_ratio_thr: float = 0.55,   # если доля травы в центре > порога => closed

        # Есть цифра
        edge_ratio_thr: float = 0.030,   # подняли (у тебя ложные 0.057 на закрытой клетке)
        canny1: int = 60,
        canny2: int = 140,

        # Цвет цифры (по HSV)
        digit_min_ratio: float = 0.010,  # порог доли пикселей цифры (среди НЕ-фона)
        valid_min_v: int = 30,           # чуть ниже, чтобы не терять тонкие штрихи
    ):
        self.center_pad_frac = center_pad_frac
        self.digit_pad_frac = digit_pad_frac

        self.bg_dist_thr = int(bg_dist_thr)
        self.grass_ratio_thr = float(grass_ratio_thr)

        self.edge_ratio_thr = float(edge_ratio_thr)
        self.canny1 = int(canny1)
        self.canny2 = int(canny2)

        self.digit_min_ratio = float(digit_min_ratio)
        self.valid_min_v = int(valid_min_v)

        # фоновые цвета в BGR
        self.grass_bgr = [hex_to_bgr(c) for c in grass_hex]
        self.open_bgr = [hex_to_bgr(c) for c in open_hex]
        self.bg_bgr = self.grass_bgr + self.open_bgr

        # HSV диапазоны цифр
        self.digit_hsv_ranges = self.load_digit_hsv_ranges(digit_ranges_path)

    # -------------------- helpers --------------------

    def load_digit_hsv_ranges(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        ranges = {}
        for k, lst in raw.items():
            d = int(k)
            ranges[d] = []
            for item in lst:
                low = np.array(item["low"], dtype=np.uint8)
                high = np.array(item["high"], dtype=np.uint8)
                ranges[d].append((low, high))
        return ranges

    def crop_center(self, img_bgr: np.ndarray, pad_frac: float) -> np.ndarray:
        h, w = img_bgr.shape[:2]
        px = int(w * pad_frac)
        py = int(h * pad_frac)
        x0 = min(max(px, 0), w - 1)
        y0 = min(max(py, 0), h - 1)
        x1 = max(w - px, x0 + 1)
        y1 = max(h - py, y0 + 1)
        return img_bgr[y0:y1, x0:x1]

    def _min_dist_mask(self, roi_bgr: np.ndarray, colors_bgr: list[np.ndarray], thr: int) -> np.ndarray:
        """
        Возвращает mask (H,W) где пиксель "похож" на хотя бы один из цветов.
        Похожесть = min Euclidean distance в BGR <= thr.
        """
        roi = roi_bgr.astype(np.int16)  # чтобы не было переполнения при вычитании
        h, w = roi.shape[:2]
        min_d2 = np.full((h, w), 10**9, dtype=np.int32)

        for c in colors_bgr:
            cc = c.astype(np.int16)
            diff = roi - cc  # (h,w,3)
            d2 = diff[:, :, 0] * diff[:, :, 0] + diff[:, :, 1] * diff[:, :, 1] + diff[:, :, 2] * diff[:, :, 2]
            min_d2 = np.minimum(min_d2, d2)

        return min_d2 <= (thr * thr)

    # -------------------- open/closed --------------------

    def classify_open_closed(self, cell_bgr: np.ndarray):
        """
        Смотрим центр и считаем долю пикселей, похожих на траву (2 оттенка).
        """
        roi = self.crop_center(cell_bgr, self.center_pad_frac)
        grass_mask = self._min_dist_mask(roi, self.grass_bgr, self.bg_dist_thr)
        grass_ratio = float(grass_mask.mean())

        state = "closed" if grass_ratio >= self.grass_ratio_thr else "open"
        return state, grass_ratio

    # -------------------- has digit --------------------

    def has_digit(self, cell_bgr: np.ndarray):
        """
        Edge_ratio считаем в более узком ROI (digit_pad_frac), чтобы кайма/трава меньше мешала.
        """
        roi = self.crop_center(cell_bgr, self.digit_pad_frac)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        edges = cv2.Canny(gray, self.canny1, self.canny2)
        edge_ratio = float((edges > 0).mean())

        return edge_ratio > self.edge_ratio_thr, edge_ratio

    # -------------------- digit by color --------------------

    def classify_digit_by_color(self, cell_bgr: np.ndarray):
        """
        Распознаём цифру по HSV, но считаем только по пикселям, которые НЕ похожи на фон.
        Это важно, потому что "2" зелёная — если выкидывать весь зелёный, ты её теряешь.
        """
        roi = self.crop_center(cell_bgr, self.digit_pad_frac)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # фон (трава + коричневое) по BGR расстоянию
        bg_mask = self._min_dist_mask(roi, self.bg_bgr, self.bg_dist_thr)

        # валидные пиксели = не фон и не слишком тёмные
        v = hsv[:, :, 2]
        valid_mask = (~bg_mask) & (v >= self.valid_min_v)

        denom = int(valid_mask.sum())
        if denom < 20:
            # если вдруг почти всё фон (редко), ослабим фильтр
            valid_mask = (v >= self.valid_min_v)
            denom = int(valid_mask.sum())
            if denom < 20:
                # совсем нечего анализировать
                return None, 0.0, {d: 0.0 for d in self.digit_hsv_ranges.keys()}

        ratios = {}
        best_digit = None
        best_ratio = -1.0

        for d, ranges in self.digit_hsv_ranges.items():
            mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)

            for low, high in ranges:
                mask_total |= cv2.inRange(hsv, low, high)

            hit = (mask_total > 0) & valid_mask
            ratio = float(hit.sum() / denom)

            ratios[d] = ratio
            if ratio > best_ratio:
                best_ratio = ratio
                best_digit = d

        if best_ratio < self.digit_min_ratio:
            return None, best_ratio, ratios

        return int(best_digit), best_ratio, ratios

    # -------------------- main --------------------

    def classify_cell(self, cell_bgr: np.ndarray):
        """
        Возвращает:
          label: "closed" | "open_empty" | "open_number"
          num: -1 | 0 | 1..8 | -3
          meta: для дебага
        """
        # Сначала edges: если есть явные детали — это почти точно открытая цифра.
        digit_present, edge_ratio = self.has_digit(cell_bgr)

        state, grass_ratio = self.classify_open_closed(cell_bgr)

        if not digit_present:
            if state == "closed":
                return "closed", -1, {"grass_ratio": grass_ratio, "edge_ratio": edge_ratio}
            return "open_empty", 0, {"grass_ratio": grass_ratio, "edge_ratio": edge_ratio}

        digit, ratio, ratios_all = self.classify_digit_by_color(cell_bgr)

        if digit is None:
            return "open_number", -3, {
                "grass_ratio": grass_ratio,
                "edge_ratio": edge_ratio,
                "digit_color_ratio": ratio,
                "ratios": ratios_all,
            }

        return "open_number", digit, {
            "grass_ratio": grass_ratio,
            "edge_ratio": edge_ratio,
            "digit_color_ratio": ratio,
            "ratios": ratios_all,
        }
