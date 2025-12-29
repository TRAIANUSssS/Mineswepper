import os
import json
import cv2
import numpy as np

def clamp(x, lo, hi):
    return int(max(lo, min(hi, x)))

def robust_range(vals, p_lo=5, p_hi=95, margin=0, lo=0, hi=255):
    a = np.percentile(vals, p_lo)
    b = np.percentile(vals, p_hi)
    return clamp(a - margin, lo, hi), clamp(b + margin, lo, hi)

def calibrate_from_alpha(images_dir="images", digits=range(1, 9),
                         p_lo=5, p_hi=95,
                         margin_h=3, margin_s=15, margin_v=15,
                         out_json="digit_hsv_ranges.json"):
    result = {}

    for d in digits:
        path = os.path.join(images_dir, f"{d}.png")

        # ВАЖНО: читаем с альфой
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"[skip] not found: {path}")
            continue
        if img.shape[2] != 4:
            print(f"[warn] {path} has no alpha channel (need RGBA/ BGRA png).")
            continue

        bgr = img[:, :, :3]
        alpha = img[:, :, 3]

        # маска цифры: где непрозрачно
        mask = alpha > 0
        if mask.sum() < 30:
            print(f"[warn] too few pixels for digit {d} in {path}")
            continue

        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        H = hsv[:, :, 0][mask].astype(np.int32)  # 0..179
        S = hsv[:, :, 1][mask].astype(np.int32)  # 0..255
        V = hsv[:, :, 2][mask].astype(np.int32)  # 0..255

        # Проверка wrap-around для красного
        has_low = np.any(H <= 10)
        has_high = np.any(H >= 170)

        s_lo, s_hi = robust_range(S, p_lo, p_hi, margin_s, 0, 255)
        v_lo, v_hi = robust_range(V, p_lo, p_hi, margin_v, 0, 255)

        if has_low and has_high:
            # два диапазона для красного
            h_hi = clamp(int(np.percentile(H[H <= 30], p_hi)) + margin_h, 0, 179)
            h_lo = clamp(int(np.percentile(H[H >= 150], p_lo)) - margin_h, 0, 179)
            ranges = [
                {"low": [0,    s_lo, v_lo], "high": [h_hi, s_hi, v_hi]},
                {"low": [h_lo, s_lo, v_lo], "high": [179,  s_hi, v_hi]},
            ]
        else:
            h_lo, h_hi = robust_range(H, p_lo, p_hi, margin_h, 0, 179)
            ranges = [{"low": [h_lo, s_lo, v_lo], "high": [h_hi, s_hi, v_hi]}]

        result[str(d)] = ranges
        print(f"Digit {d}: {ranges}")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nSaved: {out_json}")

if __name__ == "__main__":
    calibrate_from_alpha(images_dir="../images", out_json="digit_hsv_ranges.json")
