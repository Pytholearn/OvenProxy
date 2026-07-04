<div align="center">

# 🔥 OvenProxy

**A production-grade SOCKS5 / SOCKS4 / HTTP proxy scraper, checker & local gateway — with a modern Fluent dark UI built in PyQt6.**

![python](https://img.shields.io/badge/python-3.12%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-Fluent%20Dark-4cc2ff)
![platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![license](https://img.shields.io/badge/use-educational-green)

</div>

> ⚠️ **Legal / ethical use only.** OvenProxy works with *public* proxy lists for privacy,
> censorship-circumvention, research and testing. Only route traffic you are authorised to
> route, and respect the terms of any service you connect to.

---

## 🇬🇧 English

### Features

| Module | What it does |
|--------|--------------|
| **Scraper** | Concurrently downloads proxy lists from many providers. **You choose which protocols to scrape** — SOCKS5, SOCKS4 and/or HTTP. Enable/disable sources, add custom sources, import URLs. |
| **Checker** | Validates every proxy through a real request (using its own protocol): alive/dead, latency, country, exit IP, anonymity. Live progress, stop anytime. |
| **Working Proxies** | Sortable / searchable / filterable table. **Sort by ping**, copy, delete, import and export to **txt / csv / json**. |
| **Local Gateway** | Runs a local SOCKS5 server (`127.0.0.1:1080`) forwarding through one upstream — **SOCKS5, SOCKS4 or HTTP**. |
| **System Proxy** | One click routes **all Windows traffic** through the gateway (and restores your settings on stop). |
| **Mobile / LAN mode** | Binds to your LAN so a **phone on the same Wi‑Fi can connect**. |
| **Traffic Monitor** | Per-second upload/download charts, totals, active connections. |
| **Updates** | Checks a remote `version` file and self-updates via the `autoupgrader` library, with a GUI banner. |
| **Settings / Logs / Docs** | Auto-saved settings, colour-coded log console, and a built-in user guide. |

### Install & run

```bash
git clone https://github.com/Pytholearn/OvenProxy.git
cd OvenProxy
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
python main.py
```

Requires **Python 3.12+**.

### Typical workflow

1. **Scraper** → tick the protocols (SOCKS5 / SOCKS4 / HTTP) and sources → *Start Scraping*.
2. You're moved to **Checker** automatically → *Start Check*. Alive proxies stream into…
3. **Working Proxies** → *Sort by Ping*, filter/export, or select one and *Use in Gateway*.
4. **Local Gateway** → choose upstream + port → optionally tick **system proxy** or **LAN/mobile** → *Start*.
5. Point an app at `socks5://127.0.0.1:1080`, or your phone at `socks5://<LAN-IP>:1080`.

### Architecture (clean, layered)

```
app/
├── ui/         # MainWindow, theme, sidebar, pages/   (presentation)
├── widgets/    # cards, table, chart, log console, update banner
├── resources/  # inline SVG icon factory
├── services/   # QThread workers, traffic monitor, update service
├── system/     # Windows system-proxy integration
├── scraper/    # concurrent downloading (ThreadPoolExecutor)
├── checker/    # concurrent validation (ThreadPoolExecutor)
├── gateway/    # asyncio forwarding server (SOCKS5 in, SOCKS5/4/HTTP out)
├── proxy/      # import / export
├── models/ · database/ · utils/ · config.py · constants.py
main.py · version · requirements.txt
```

* **The GUI never freezes** — scraping/checking run on `QThread`; the gateway runs an
  `asyncio` loop on its own thread. Everything talks back via signals/slots.

### How anonymity is determined
The checker routes a request to a geolocation endpoint *through* each proxy and compares the
returned exit IP to your real public IP: same → `Transparent`, different → `Anonymous`.

### Updates
`autoupgrader` compares the local `VERSION` file to a remote `version` file on GitHub and pulls
the repo when newer. Defaults point at `Pytholearn/OvenProxy` and are editable in **Settings**.

---

<div dir="rtl">

## 🇮🇷 فارسی

**اوون‌پروکسی (OvenProxy)** یک ابزار حرفه‌ای دسکتاپ برای **جمع‌آوری، تست و استفاده از پروکسی‌های SOCKS5 / SOCKS4 / HTTP** است، با رابط کاربری تاریک و مدرن (Fluent) که با PyQt6 ساخته شده.

> ⚠️ **فقط استفادهٔ قانونی و اخلاقی.** این ابزار با لیست‌های پروکسی *عمومی* کار می‌کند؛ برای حریم خصوصی، عبور از فیلترینگ، تحقیق و تست. فقط ترافیکی را عبور دهید که مجاز به آن هستید.

### امکانات

| بخش | کاری که می‌کند |
|------|----------------|
| **اسکرپر** | دانلود همزمان لیست‌ها از چند منبع. **خودت انتخاب می‌کنی چه پروتکلی اسکرپ شود** — SOCKS5، SOCKS4 و/یا HTTP. فعال/غیرفعال کردن منابع، افزودن منبع دلخواه، ایمپورت URL. |
| **چکر** | تست هر پروکسی با یک درخواست واقعی (با پروتکل خودش): زنده/مرده، پینگ، کشور، IP خروجی، سطح ناشناسی. پیشرفت زنده و توقف هر لحظه. |
| **پروکسی‌های سالم** | جدول قابل‌جستجو/مرتب‌سازی/فیلتر. **مرتب‌سازی بر اساس پینگ**، کپی، حذف، ایمپورت و اکسپورت به **txt / csv / json**. |
| **گیت‌وی محلی** | یک سرور SOCKS5 محلی روی `127.0.0.1:1080` که ترافیک را از طریق یک پروکسی بالادست (**SOCKS5، SOCKS4 یا HTTP**) عبور می‌دهد. |
| **پروکسی سیستمی** | با یک کلیک **کل ترافیک ویندوز** از گیت‌وی رد می‌شود (و موقع توقف، تنظیمات قبلی برمی‌گردد). |
| **حالت موبایل / شبکه** | روی IP شبکهٔ محلی باند می‌شود تا **گوشی روی همان وای‌فای وصل شود**. |
| **مانیتور ترافیک** | نمودار لحظه‌ای آپلود/دانلود، مجموع و تعداد اتصالات فعال. |
| **آپدیت** | یک فایل `version` از راه دور را چک می‌کند و با کتابخانهٔ `autoupgrader` خودش را آپدیت می‌کند، همراه با بنر داخل برنامه. |
| **تنظیمات / لاگ / راهنما** | تنظیمات با ذخیرهٔ خودکار، کنسول لاگ رنگی و راهنمای داخل برنامه. |

### نصب و اجرا

```bash
git clone https://github.com/Pytholearn/OvenProxy.git
cd OvenProxy
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

نیازمند **پایتون ۳٫۱۲ به بالا**.

### مسیر استفاده

۱. **اسکرپر** → پروتکل‌ها (SOCKS5/SOCKS4/HTTP) و منابع را تیک بزن → *Start Scraping*.
۲. خودکار به **چکر** می‌روی → *Start Check*. پروکسی‌های سالم می‌روند به…
۳. **پروکسی‌های سالم** → *Sort by Ping*، فیلتر/اکسپورت، یا یکی را انتخاب و *Use in Gateway*.
۴. **گیت‌وی محلی** → پروکسی بالادست و پورت را انتخاب کن → در صورت نیاز **پروکسی سیستمی** یا **حالت موبایل** را تیک بزن → *Start*.
۵. یک برنامه را روی `socks5://127.0.0.1:1080` یا گوشی را روی `socks5://<IP-شبکه>:1080` تنظیم کن.

### اتصال گوشی (حالت موبایل)
گزینهٔ **Allow LAN / mobile** را قبل از استارت تیک بزن؛ گیت‌وی روی همهٔ اینترفیس‌ها باند می‌شود و آدرس شبکه‌ات را نشان می‌دهد. گوشی را روی همان وای‌فای نگه دار و در تنظیمات وای‌فای، پروکسی دستی SOCKS را با همان IP و پورت وارد کن. اگر وصل نشد، اجازهٔ عبور برنامه از فایروال ویندوز را بده.

### نکته دربارهٔ پروکسی سیستمی
پروکسی سیستمی ویندوز برای SOCKS محدودیت دارد (best-effort)؛ برای اطمینان کامل، تنظیم پروکسی داخل خود برنامه‌ها همیشه مطمئن‌تر است.

</div>

---

## License

For educational and authorised use only. No warranty.
