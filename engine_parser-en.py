# File: engine_core.py
import time
import random
import json
from pathlib import Path
from typing import Optional, Dict, Any

# =====================================================================
# 1. MAIN CONFIGURATION VARIABLES (CHANGE HERE)
# =====================================================================

# Target website (URL) to send the request to
TARGET_URL: str = "https://httpbin.org/headers"

# Engine operating mode:
# "http"    — fast request with browser TLS fingerprint (curl_cffi / requests)
# "browser" — full Chromium browser launch (Playwright) for JS-heavy websites
MODE: str = "http"

# User-Agent (if left empty "", the engine will pick a random one from the pool below)
USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Proxy (leave as None or "" for direct connection without proxy)
# Examples: "http://user:pass@127.0.0.1:8080" or "socks5://127.0.0.1:9050"
PROXY_URL: Optional[str] = None

# Referer (the URL the user allegedly came from)
REFERER_URL: str = "https://www.google.com/"

# Additional custom headers (if needed)
CUSTOM_HEADERS: Dict[str, str] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

# Request cookies (can be passed as a dictionary)
CUSTOM_COOKIES: Dict[str, str] = {
    # "session_id": "your_session_token",
}

# File for automatic saving and loading of cookies between runs
COOKIES_STORAGE_FILE: str = "engine_cookies.json"

# Timeout and retry settings
REQUEST_TIMEOUT_SEC: int = 30
MAX_RETRIES: int = 3
RETRY_DELAY_RANGE: tuple[float, float] = (1.5, 3.5)  # Delay between retries (min, max) in seconds

# Settings for MODE = "browser" (Playwright)
HEADLESS_BROWSER: bool = True            # True — headless mode, False — visible browser window
WAIT_SELECTOR: Optional[str] = None      # CSS selector to wait for (e.g., "div.catalog-list")
AUTO_SCROLL_PAGE: bool = True            # Whether to scroll down the page to trigger lazy loading
SAVE_RESULT_HTML: str = "last_response.html"  # File path to save the received HTML


# =====================================================================
# 2. FALLBACK USER-AGENT POOL (USED IF USER_AGENT IS EMPTY)
# =====================================================================
USER_AGENTS_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


# =====================================================================
# 3. ENGINE CORE
# =====================================================================

class RequestEngineCore:
    def __init__(
        self,
        user_agent: str = USER_AGENT,
        proxy: Optional[str] = PROXY_URL,
        referer: str = REFERER_URL,
        extra_headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        cookies_file: str = COOKIES_STORAGE_FILE,
        timeout: int = REQUEST_TIMEOUT_SEC,
    ):
        self.user_agent = user_agent.strip() if user_agent else random.choice(USER_AGENTS_POOL)
        self.proxy = proxy.strip() if proxy else None
        self.referer = referer
        self.timeout = timeout
        self.cookies_file = Path(cookies_file) if cookies_file else None

        # Assemble final headers
        self.headers = dict(CUSTOM_HEADERS)
        self.headers["User-Agent"] = self.user_agent
        if self.referer:
            self.headers["Referer"] = self.referer
        if extra_headers:
            self.headers.update(extra_headers)

        # Load saved cookies and merge with provided ones
        self.cookies = self._load_saved_cookies()
        if CUSTOM_COOKIES:
            self.cookies.update(CUSTOM_COOKIES)
        if cookies:
            self.cookies.update(cookies)

    def _load_saved_cookies(self) -> Dict[str, str]:
        if self.cookies_file and self.cookies_file.exists():
            try:
                data = json.loads(self.cookies_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return {str(k): str(v) for k, v in data.items()}
            except Exception:
                pass
        return {}

    def _save_cookies(self, new_cookies: Dict[str, str]) -> None:
        self.cookies.update(new_cookies)
        if self.cookies_file:
            try:
                self.cookies_file.write_text(
                    json.dumps(self.cookies, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                pass

    def fetch_http(
        self,
        url: str = TARGET_URL,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json_body: Optional[Dict[str, Any]] = None,
        impersonate_browser: str = "chrome120",
    ) -> Dict[str, Any]:
        """
        Performs an HTTP request simulating a browser TLS fingerprint (if curl_cffi is installed)
        or via a standard requests session.
        """
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Attempt 1: via curl_cffi (spoofing JA3/TLS fingerprint to match Chrome)
                try:
                    from curl_cffi import requests as cffi_requests

                    with cffi_requests.Session(impersonate=impersonate_browser) as session:
                        resp = session.request(
                            method=method.upper(),
                            url=url,
                            headers=self.headers,
                            cookies=self.cookies,
                            params=params,
                            data=data,
                            json=json_body,
                            proxies=proxies,
                            timeout=self.timeout,
                            allow_redirects=True,
                        )
                        self._save_cookies(dict(resp.cookies))
                        return {
                            "ok": resp.status_code < 400,
                            "status_code": resp.status_code,
                            "url": str(resp.url),
                            "html": resp.text,
                            "cookies": dict(resp.cookies),
                            "engine": f"curl_cffi ({impersonate_browser})",
                        }
                except ImportError:
                    # Attempt 2: standard requests if curl_cffi is not installed
                    import requests

                    with requests.Session() as session:
                        resp = session.request(
                            method=method.upper(),
                            url=url,
                            headers=self.headers,
                            cookies=self.cookies,
                            params=params,
                            data=data,
                            json=json_body,
                            proxies=proxies,
                            timeout=self.timeout,
                            allow_redirects=True,
                        )
                        self._save_cookies(requests.utils.dict_from_cookiejar(resp.cookies))
                        return {
                            "ok": resp.status_code < 400,
                            "status_code": resp.status_code,
                            "url": str(resp.url),
                            "html": resp.text,
                            "cookies": self.cookies,
                            "engine": "requests",
                        }

            except Exception as e:
                last_error = str(e)
                if attempt < MAX_RETRIES:
                    pause = random.uniform(*RETRY_DELAY_RANGE)
                    print(f"[Attempt {attempt}/{MAX_RETRIES}] Error: {last_error}. Waiting {pause:.1f} sec...")
                    time.sleep(pause)

        return {
            "ok": False,
            "status_code": 0,
            "url": url,
            "html": "",
            "error": last_error,
            "engine": "http_failed",
        }

    def fetch_browser(
        self,
        url: str = TARGET_URL,
        headless: bool = HEADLESS_BROWSER,
        wait_selector: Optional[str] = WAIT_SELECTOR,
        auto_scroll: bool = AUTO_SCROLL_PAGE,
    ) -> Dict[str, Any]:
        """
        Opens the page via a real Chromium browser (Playwright)
        with automation stealth, configured User-Agent, cookies, and scrolling.
        """
        from playwright.sync_api import sync_playwright

        proxy_cfg = {"server": self.proxy} if self.proxy else None

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless,
                proxy=proxy_cfg,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            context = browser.new_context(
                user_agent=self.user_agent,
                locale="ru-RU",
                timezone_id="Europe/Moscow",
                viewport={"width": 1920, "height": 1080},
                extra_http_headers={
                    k: v for k, v in self.headers.items() if k.lower() != "user-agent"
                },
            )

            # Hide basic automation flags in the page's JS environment
            context.add_init_script(
                """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU', 'ru', 'en-US', 'en']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                """
            )

            # If saved cookies exist, load them into the target URL domain
            if self.cookies:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.hostname or ""
                if domain:
                    pw_cookies = [
                        {"name": k, "value": v, "domain": domain, "path": "/"}
                        for k, v in self.cookies.items()
                    ]
                    try:
                        context.add_cookies(pw_cookies)
                    except Exception:
                        pass

            page = context.new_page()
            status_code = 0

            try:
                response = page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                if response:
                    status_code = response.status

                if wait_selector:
                    page.wait_for_selector(wait_selector, timeout=self.timeout * 1000)
                else:
                    page.wait_for_timeout(random.randint(1500, 2800))

                if auto_scroll:
                    for _ in range(4):
                        page.mouse.wheel(0, random.randint(600, 1100))
                        page.wait_for_timeout(random.randint(400, 800))

                html_content = page.content()
                final_url = page.url

                # Save cookies from the browser
                browser_cookies = {c["name"]: c["value"] for c in context.cookies()}
                self._save_cookies(browser_cookies)

                return {
                    "ok": status_code < 400 if status_code else bool(html_content),
                    "status_code": status_code,
                    "url": final_url,
                    "html": html_content,
                    "cookies": browser_cookies,
                    "engine": "playwright_chromium",
                }
            except Exception as e:
                return {
                    "ok": False,
                    "status_code": status_code,
                    "url": url,
                    "html": page.content() if page else "",
                    "error": str(e),
                    "engine": "playwright_chromium",
                }
            finally:
                context.close()
                browser.close()

    def run(self, url: str = TARGET_URL, mode: str = MODE) -> Dict[str, Any]:
        """Universal execution method based on the selected MODE ('http' or 'browser')."""
        if mode.lower() == "browser":
            return self.fetch_browser(url=url)
        return self.fetch_http(url=url)


# =====================================================================
# 4. DIRECT EXECUTION EXAMPLE
# =====================================================================
if __name__ == "__main__":
    engine = RequestEngineCore(
        user_agent=USER_AGENT,
        proxy=PROXY_URL,
        referer=REFERER_URL,
    )

    print(f"🚀 Starting request to: {TARGET_URL}")
    print(f"⚙️ Mode: {MODE} | User-Agent: {engine.user_agent}")

    result = engine.run(url=TARGET_URL, mode=MODE)

    print(f"✅ Status: {result.get('status_code')} | Engine: {result.get('engine')}")
    if result.get("html"):
        Path(SAVE_RESULT_HTML).write_text(result["html"], encoding="utf-8")
        print(f"HTML saved to file: {SAVE_RESULT_HTML} ({len(result['html'])} characters)")
    else:
        print(f"Error: {result.get('error')}")