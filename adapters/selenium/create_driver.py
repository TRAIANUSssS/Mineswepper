import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def make_driver(start_url: str):
    opts = Options()

    # Профиль (см. ниже про cookies) — самый мощный способ "как обычный браузер"
    opts.add_argument(r"--user-data-dir=E:\Projects\Mineswepper\chrome_profile")
    opts.add_argument("--profile-directory=Default")

    # Убираем явные флаги automation (не 100% гарантия, но часто помогает)
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    # Нормальный user-agent
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=opts)

    # CDP headers: Accept-Language и т.п.
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
        "headers": {
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
            "DNT": "1",
        }
    })

    # Уберём navigator.webdriver (часто проверяют)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """
    })

    driver.get(start_url)
    return driver