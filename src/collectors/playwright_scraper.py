"""Playwright 直爬亚马逊数据采集器

不依赖第三方 API，直接通过浏览器抓取亚马逊页面数据。
支持 Best Sellers / 搜索结果。
"""

import asyncio
import random
import re
from typing import List

from src.models.product import Product

# 随机 User-Agent 池
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# 站点域名
MARKETPLACE_DOMAINS = {
    "us": "www.amazon.com",
    "uk": "www.amazon.co.uk",
    "de": "www.amazon.de",
    "fr": "www.amazon.fr",
    "jp": "www.amazon.co.jp",
    "au": "www.amazon.com.au",
    "ca": "www.amazon.ca",
    "it": "www.amazon.it",
    "es": "www.amazon.es",
    "in": "www.amazon.in",
    "br": "www.amazon.com.br",
    "mx": "www.amazon.com.mx",
    "sg": "www.amazon.sg",
    "ae": "www.amazon.ae",
    "nl": "www.amazon.nl",
    "se": "www.amazon.se",
    "be": "www.amazon.com.be",
}


class PlaywrightScraper:
    """Playwright 亚马逊直爬采集器"""

    def __init__(self, marketplace: str = "us", headless: bool = True):
        self.marketplace = marketplace
        self.domain = MARKETPLACE_DOMAINS.get(marketplace, "www.amazon.com")
        self.headless = headless
        self.base_url = f"https://{self.domain}"

    async def _get_browser(self, playwright_instance):
        """创建浏览器实例"""
        browser = await playwright_instance.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
            locale="en_US",
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
        """)
        return browser, context

    def _parse_price(self, text: str) -> float:
        if not text:
            return 0.0
        match = re.search(r'[\$£€¥]\s*[\d,]+\.?\d*', text)
        if match:
            price_str = match.group().replace('$', '').replace('£', '').replace('€', '').replace('¥', '').replace(',', '').strip()
            try:
                return float(price_str)
            except:
                return 0.0
        return 0.0

    def _parse_rating(self, text: str) -> float:
        if not text:
            return 0.0
        match = re.search(r'(\d+\.?\d*)\s*out\s*of\s*5', text)
        if match:
            return float(match.group(1))
        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            return float(match.group(1))
        return 0.0

    def _parse_number(self, text: str) -> int:
        if not text:
            return 0
        match = re.search(r'[\d,]+', text.replace(' ', ''))
        if match:
            try:
                return int(match.group().replace(',', ''))
            except:
                return 0
        return 0

    def _make_product(self, *, asin, title, price, rating, reviews_count, bsr, category, image_url) -> Product:
        return Product(
            asin=asin,
            title=title.strip()[:500],
            brand="",
            category=category,
            price=price,
            rating=rating,
            reviews_count=reviews_count,
            bsr=bsr,
            monthly_sales_est=max(1, int(reviews_count * 0.3)),
            monthly_revenue_est=round(price * max(1, int(reviews_count * 0.3)), 2),
            seller_count=1,
            buy_box_seller="",
            weight_grams=0,
            dimensions=(),
            listing_quality_score=50,
            date_first_available="",
            image_url=image_url,
            marketplace=self.marketplace,
        )

    async def get_best_sellers(self, category: str, pages: int = 1) -> List[Product]:
        """抓取 Best Sellers 页面"""
        from playwright.async_api import async_playwright
        from urllib.parse import quote

        products = []
        # Use category name as URL slug (lowercase, hyphens)
        slug = category.lower().replace(" & ", "-").replace(" ", "-").replace(",", "")

        async with async_playwright() as p:
            browser, context = await self._get_browser(p)
            page = await context.new_page()

            for pg in range(1, pages + 1):
                url = f"{self.base_url}/gp/bestsellers/{slug}"
                if pg > 1:
                    url += f"?pg={pg}"
                try:
                    print(f"  🕷️ 正在抓取: {url}")
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(random.randint(2000, 5000))

                    content = await page.content()
                    if "captcha" in content.lower() or "robot" in content.lower():
                        print(f"  ⚠️ 触发 CAPTCHA，跳过本页")
                        continue

                    # Try multiple selectors for best seller items
                    items = await page.query_selector_all('#gridItemRoot, [data-component-type="s-impression-logger"], .p13n-grid-item, .a-carousel-card')
                    if not items:
                        items = await page.query_selector_all('[data-asin]')

                    page_count = 0
                    for idx, item in enumerate(items[:50]):
                        try:
                            asin = await item.get_attribute('data-asin') or ''
                            if not asin or len(asin) != 10:
                                continue
                            rank = idx + 1 + (pg - 1) * 50

                            title_el = await item.query_selector('a.a-link-normal span, .a-text-normal, [data-cy="title-recipe-title"]')
                            title = await title_el.inner_text() if title_el else ""

                            price_el = await item.query_selector('.a-price .a-offscreen, .a-color-price, span.p13n-sc-price')
                            price_text = await price_el.inner_text() if price_el else "0"
                            price = self._parse_price(price_text)

                            rating_el = await item.query_selector('i.a-icon-star-small span, .a-icon-alt, i[data-cy="reviews-ratings-slot"] span')
                            rating_text = await rating_el.inner_text() if rating_el else "0"
                            rating = self._parse_rating(rating_text)

                            reviews_el = await item.query_selector('span.a-size-small, .a-size-base.s-underline-text')
                            reviews_text = await reviews_el.inner_text() if reviews_el else "0"
                            reviews_count = self._parse_number(reviews_text)

                            img_el = await item.query_selector('img.s-image, img[src*="images-amazon"]')
                            image_url = await img_el.get_attribute('src') if img_el else ""

                            if title and price > 0:
                                products.append(self._make_product(
                                    asin=asin, title=title, price=price, rating=rating,
                                    reviews_count=reviews_count, bsr=rank, category=category,
                                    image_url=image_url,
                                ))
                                page_count += 1
                        except:
                            continue
                    print(f"  ✅ 第 {pg} 页：获取 {page_count} 个产品")
                    if pg < pages:
                        await page.wait_for_timeout(random.randint(3000, 8000))
                except Exception as e:
                    print(f"  ❌ 第 {pg} 页抓取失败: {e}")
                    continue

            await browser.close()
        print(f"  🕷️ Playwright 抓取完成，共 {len(products)} 个产品")
        return products

    async def search(self, keyword: str, pages: int = 1) -> List[Product]:
        """关键词搜索产品"""
        from playwright.async_api import async_playwright
        from urllib.parse import quote

        products = []

        async with async_playwright() as p:
            browser, context = await self._get_browser(p)
            page = await context.new_page()

            for pg in range(1, pages + 1):
                url = f"{self.base_url}/s?k={quote(keyword)}&page={pg}"
                try:
                    print(f"  🕷️ 搜索: {url}")
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(random.randint(2000, 5000))

                    content = await page.content()
                    if "captcha" in content.lower():
                        print(f"  ⚠️ 触发 CAPTCHA，跳过")
                        continue

                    items = await page.query_selector_all('[data-asin]:not([data-asin=""])')
                    for idx, item in enumerate(items[:48]):
                        try:
                            asin = await item.get_attribute('data-asin') or ''
                            if not asin or len(asin) != 10:
                                continue

                            title_el = await item.query_selector('h2 a span, h2 span, .a-text-normal')
                            title = await title_el.inner_text() if title_el else ""

                            price_el = await item.query_selector('.a-price .a-offscreen, .a-color-price')
                            price_text = await price_el.inner_text() if price_el else "0"
                            price = self._parse_price(price_text)

                            rating_el = await item.query_selector('i.a-icon-star-small span, .a-icon-alt')
                            rating_text = await rating_el.inner_text() if rating_el else "0"
                            rating = self._parse_rating(rating_text)

                            reviews_el = await item.query_selector('span.a-size-base.s-underline-text, span[aria-label*="stars"]')
                            reviews_text = await reviews_el.inner_text() if reviews_el else "0"
                            reviews_count = self._parse_number(reviews_text)

                            img_el = await item.query_selector('img.s-image')
                            image_url = await img_el.get_attribute('src') if img_el else ""

                            if title and price > 0:
                                products.append(self._make_product(
                                    asin=asin, title=title, price=price, rating=rating,
                                    reviews_count=reviews_count, bsr=0, category="",
                                    image_url=image_url,
                                ))
                        except:
                            continue
                    print(f"  ✅ 搜索第 {pg} 页完成")
                    if pg < pages:
                        await page.wait_for_timeout(random.randint(3000, 8000))
                except Exception as e:
                    print(f"  ❌ 搜索第 {pg} 页失败: {e}")
                    continue

            await browser.close()
        return products

    async def get_categories(self) -> list:
        """从亚马逊 Best Sellers 页面抓取品类列表"""
        from playwright.async_api import async_playwright

        categories = []

        async with async_playwright() as p:
            browser, context = await self._get_browser(p)
            page = await context.new_page()

            try:
                url = f"{self.base_url}/gp/bestsellers/"
                print(f"  🕷️ 抓取品类列表: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)

                cat_links = await page.query_selector_all('#zg_browseRoot a, .a-link-normal[href*="/bestsellers/"]')
                for link in cat_links:
                    try:
                        name = await link.inner_text()
                        href = await link.get_attribute('href') or ''
                        slug_match = re.search(r'/bestsellers/([\w-]+)', href)
                        if slug_match and name:
                            categories.append({
                                "id": slug_match.group(1),
                                "name": name.strip(),
                            })
                    except:
                        continue
            except Exception as e:
                print(f"  ❌ 品类抓取失败: {e}")

            await browser.close()
        return categories


# ─── 同步包装器 ───────────────────────────────────────────────

def sync_get_best_sellers(marketplace: str, category: str, pages: int = 1) -> List[Product]:
    """同步版本的 Best Sellers 抓取"""
    scraper = PlaywrightScraper(marketplace=marketplace)
    return asyncio.run(scraper.get_best_sellers(category, pages))


def sync_search(marketplace: str, keyword: str, pages: int = 1) -> List[Product]:
    """同步版本的搜索"""
    scraper = PlaywrightScraper(marketplace=marketplace)
    return asyncio.run(scraper.search(keyword, pages))


def sync_get_categories(marketplace: str) -> list:
    """同步版本的品类获取"""
    scraper = PlaywrightScraper(marketplace=marketplace)
    return asyncio.run(scraper.get_categories())
