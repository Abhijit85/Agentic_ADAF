from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "FinQA" / "official_test.json"
REPORTS_DIR = ROOT / "data" / "FinQA" / "reports"
MANIFEST_PATH = ROOT / "data" / "FinQA" / "report_download_manifest.json"

BASE_URL = "https://www.annualreports.com"
USER_AGENT = "Mozilla/5.0 (compatible; FinQA-report-downloader/1.0)"

COMPANY_LINK_RE = re.compile(r'href="(/Company/[^"#?]+)"')
LOGO_TICKER_RE_TEMPLATE = r"/HostedData/CompanyLogos/[^\"']*_{ticker}\.(?:png|webp|jpg|jpeg)"
REPORT_PDF_RE_TEMPLATE = r'(/HostedData/AnnualReportArchive/[^"\']*_{year}\.pdf)'


def fetch_text(url: str, retries: int = 6, sleep_s: float = 1.0) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            if exc.code == 429 and attempt + 1 < retries:
                time.sleep(max(5.0, sleep_s * (2 ** attempt)))
                continue
            raise
        except (URLError, TimeoutError):
            if attempt + 1 == retries:
                raise
            time.sleep(sleep_s * (2 ** attempt))
    raise RuntimeError(f"failed to fetch {url}")


def download_file(url: str, dest: Path, retries: int = 6, sleep_s: float = 1.0) -> None:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=60) as response, dest.open("wb") as out:
                out.write(response.read())
            return
        except HTTPError as exc:
            if exc.code == 429 and attempt + 1 < retries:
                time.sleep(max(5.0, sleep_s * (2 ** attempt)))
                continue
            raise
        except (URLError, TimeoutError):
            if attempt + 1 == retries:
                raise
            time.sleep(sleep_s * (2 ** attempt))


def load_report_keys() -> list[tuple[str, str]]:
    with DATASET_PATH.open() as f:
        data = json.load(f)
    keys = sorted({tuple(example["filename"].split("/")[:2]) for example in data if example.get("filename")})
    return [(ticker, year) for ticker, year in keys]


def unique_links(html: str) -> list[str]:
    seen = set()
    links = []
    for link in COMPANY_LINK_RE.findall(html):
        if link not in seen:
            seen.add(link)
            links.append(link)
    return links


def resolve_company_page(ticker: str) -> tuple[str | None, str | None]:
    search_url = f"{BASE_URL}/Companies?search={quote(ticker)}"
    html = fetch_text(search_url)
    logo_re = re.compile(LOGO_TICKER_RE_TEMPLATE.format(ticker=re.escape(ticker)), re.IGNORECASE)
    for link in unique_links(html):
        page_html = fetch_text(f"{BASE_URL}{link}")
        if logo_re.search(page_html):
            return link, page_html
        time.sleep(0.5)
    return None, None


def resolve_report_pdf(company_html: str, year: str) -> str | None:
    match = re.search(REPORT_PDF_RE_TEMPLATE.format(year=re.escape(year)), company_html, flags=re.IGNORECASE)
    if not match:
        return None
    return f"{BASE_URL}{match.group(1)}"


def iter_download_targets() -> Iterable[tuple[str, str, str]]:
    company_cache: dict[str, tuple[str | None, str | None]] = {}
    for ticker, year in load_report_keys():
        if ticker not in company_cache:
            company_cache[ticker] = resolve_company_page(ticker)
            time.sleep(0.5)
        company_link, company_html = company_cache[ticker]
        if not company_link or not company_html:
            yield ticker, year, ""
            continue
        pdf_url = resolve_report_pdf(company_html, year)
        yield ticker, year, pdf_url or ""


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text())
    else:
        manifest = {"downloaded": [], "missing": []}
    for idx, (ticker, year, pdf_url) in enumerate(iter_download_targets(), start=1):
        rel_name = f"{ticker}_{year}.pdf"
        dest = REPORTS_DIR / rel_name
        if not pdf_url:
            print(f"[{idx}] missing source for {ticker}/{year}")
            manifest["missing"].append({"ticker": ticker, "year": year})
            MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
            continue
        if dest.exists() and dest.stat().st_size > 0:
            print(f"[{idx}] exists {rel_name}")
            manifest["downloaded"].append({"ticker": ticker, "year": year, "path": str(dest), "url": pdf_url})
            MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
            continue
        print(f"[{idx}] downloading {rel_name}")
        try:
            download_file(pdf_url, dest)
            manifest["downloaded"].append({"ticker": ticker, "year": year, "path": str(dest), "url": pdf_url})
        except Exception as exc:
            print(f"[{idx}] failed {rel_name}: {exc}")
            manifest["missing"].append({"ticker": ticker, "year": year, "url": pdf_url, "error": str(exc)})
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    print(f"wrote manifest to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
