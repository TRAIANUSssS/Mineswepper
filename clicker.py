import time
import pyautogui

# Если увести мышь в левый верхний угол — pyautogui выбросит исключение и остановит скрипт.
pyautogui.FAILSAFE = True

def click_action(action, pre_delay: float = 0.1, post_delay: float = 0.1):
    """
    Кликает по координатам action.x, action.y.
    Поддерживает left/right (на будущее), но сейчас у тебя actions только left.
    """
    time.sleep(pre_delay)

    if action.kind == "left":
        pyautogui.click(action.x, action.y, button="left")
    elif action.kind == "right":
        pyautogui.click(action.x, action.y, button="right")
    else:
        raise ValueError(f"Unknown action kind: {action.kind}")

    time.sleep(post_delay)
