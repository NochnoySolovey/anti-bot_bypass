# anti-bot_bypass
РУ: 
Движок поддерживает два режима работы:
 MODE = "http" — быстрые запросы через curl_cffi (имитация TLS-отпечатка реального браузера Chrome) с автоматическим откатом на стандартный requests, если библиотека не установлена.
 MODE = "browser" — полноценный рендеринг через Playwright (Chromium) с подменой navigator.webdriver, настройкой локали, часового пояса, окна браузера и плавной прокруткой страницы для подгрузки динамического контента.
 Как подключать в свои скрипты
  Прямой запуск через переменные внутри файла:
  1.Измени вверху файла TARGET_URL, USER_AGENT, PROXY_URL и MODE ("http" или "browser"), после чего запусти:
    python3 engine_parser-ru.py
  2.Импорт в другой проект с передачей переменных на лету:

   from engine_parser-ru import RequestEngineCore
   my_url = "https://example.com/catalog"
   my_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"
   engine = RequestEngineCore(user_agent=my_ua, proxy=None)
   res = engine.run(url=my_url, mode="http")  # или mode="browser"
   print(res["status_code"], len(res["html"]))

  3.Зависимости для максимальной совместимости:
   Для режима "http" с браузерным TLS-отпечатком: pip install curl_cffi requests
   Для режима "browser" с рендерингом JS: pip install playwright && playwright install chromium
EN:
The engine supports two operating modes:
  MODE = "http" — fast requests via curl_cffi (simulating a real Chrome browser TLS fingerprint) with automatic fallback to standard requests if the library is not installed.
  MODE = "browser" — full rendering via Playwright (Chromium) with navigator.webdriver spoofing, locale, timezone, and viewport configuration, plus smooth page scrolling to load dynamic content.
How to integrate into your scripts
Direct execution using in-file variables:
  1.Edit TARGET_URL, USER_AGENT, PROXY_URL, and MODE ("http" or "browser") at the top of the file, then run:
    python3 engine_parser-en.py

  2.Import into another project and pass variables on the fly:
from engine_parser-ru import RequestEngineCore

my_url = "https://example.com/catalog"
my_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"
engine = RequestEngineCore(user_agent=my_ua, proxy=None)
res = engine.run(url=my_url, mode="http")  # or mode="browser"
print(res["status_code"], len(res["html"]))

  Dependencies for maximum compatibility:

  For "http" mode with browser TLS fingerprinting: pip install curl_cffi requests
  For "browser" mode with JS rendering: pip install playwright && playwright install chromium
   
