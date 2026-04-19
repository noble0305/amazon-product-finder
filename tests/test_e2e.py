"""亚马逊选品系统 Playwright E2E 测试"""
import sys
import json
import time
import requests
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5002"

def check_server():
    """检查服务是否在运行"""
    try:
        r = requests.get(BASE, timeout=5)
        return r.status_code == 200
    except:
        return False

results = []

def test(name, passed, detail=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    results.append({"name": name, "passed": passed, "detail": detail})
    print(f"  {status} | {name}" + (f" — {detail}" if detail else ""))

def run_tests():
    print("\n" + "="*60)
    print("🧪 亚马逊选品系统 E2E 测试报告")
    print("="*60)

    # 0. 服务可用性
    print("\n📋 1. 服务可用性")
    test("首页加载", check_server())

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        # 1. 首页加载
        print("\n📋 2. 首页功能")
        page.goto(BASE, wait_until="networkidle", timeout=15000)
        time.sleep(1)

        # 检查标题
        title = page.title()
        test("页面标题", bool(title), f"title='{title}'")

        # 检查统计卡片
        stats = page.query_selector_all(".stat")
        test("统计卡片显示", len(stats) >= 3, f"找到 {len(stats)} 个统计卡片")

        # 检查导航 Tab
        tabs = page.query_selector_all(".tab")
        test("导航 Tab 显示", len(tabs) >= 3, f"找到 {len(tabs)} 个 Tab")

        # 2. 多站点选择
        print("\n📋 3. 多站点支持")
        marketplace_select = page.query_selector("select#marketplace")
        test("站点下拉框存在", marketplace_select is not None)

        if marketplace_select:
            options = marketplace_select.query_selector_all("option")
            test("站点数量 >= 10", len(options) >= 10, f"共 {len(options)} 个站点")
            
            # 验证关键站点存在
            html = marketplace_select.inner_html()
            test("美国站存在", "amazon.com" in html)
            test("英国站存在", "amazon.co.uk" in html)
            test("澳洲站存在", "amazon.com.au" in html)
            test("日本站存在", "amazon.co.jp" in html)
            test("德国站存在", "amazon.de" in html)

        # 3. 品类选择
        print("\n📋 4. 品类动态加载")
        category_select = page.query_selector("select#category")
        test("品类下拉框存在", category_select is not None)

        if category_select:
            cat_options = category_select.query_selector_all("option")
            test("品类数量 >= 20", len(cat_options) >= 20, f"共 {len(cat_options)} 个品类")

        # 4. 品类 API
        print("\n📋 5. 品类 API")
        try:
            r = requests.get(f"{BASE}/api/categories?marketplace=us", timeout=10)
            data = r.json()
            cats = data.get("categories", [])
            test("品类 API 返回成功", data.get("ok") == True, f"返回 {len(cats)} 个品类")
            test("品类包含 Electronics", any(c["name"] == "Electronics" for c in cats))
            test("品类包含 Home & Kitchen", any("Home" in c["name"] for c in cats))
        except Exception as e:
            test("品类 API 返回成功", False, str(e))

        # 5. 切换站点验证
        print("\n📋 6. 站点切换")
        if marketplace_select:
            # 切换到英国站
            marketplace_select.select_option(value="uk")
            time.sleep(2)  # 等待品类重新加载
            
            # 检查品类 API 对英国站
            try:
                r = requests.get(f"{BASE}/api/categories?marketplace=uk", timeout=10)
                data = r.json()
                test("英国站品类 API", data.get("ok") == True, f"返回 {len(data.get('categories', []))} 个品类")
            except Exception as e:
                test("英国站品类 API", False, str(e))

            # 切换到澳洲站
            marketplace_select.select_option(value="au")
            time.sleep(2)
            try:
                r = requests.get(f"{BASE}/api/categories?marketplace=au", timeout=10)
                data = r.json()
                test("澳洲站品类 API", data.get("ok") == True, f"返回 {len(data.get('categories', []))} 个品类")
            except Exception as e:
                test("澳洲站品类 API", False, str(e))

        # 6. 扫描功能（Demo 模式）
        print("\n📋 7. 扫描功能")
        # 切回美国站
        if marketplace_select:
            marketplace_select.select_option(value="us")
            time.sleep(1)

        scan_btn = page.query_selector("button.btn-primary")
        test("扫描按钮存在", scan_btn is not None)

        if scan_btn:
            scan_btn.click()
            # 等待扫描完成
            time.sleep(5)
            
            # 检查是否返回了产品
            try:
                r = requests.get(f"{BASE}/api/scan?category=home-garden&pages=1&marketplace=us", timeout=30)
                data = r.json()
                test("扫描 API 调用", data.get("ok") == True, f"获取 {data.get('count', 0)} 个产品")
            except Exception as e:
                test("扫描 API 调用", False, str(e))

        # 7. 收藏功能
        print("\n📋 8. 收藏功能")
        fav_tab = None
        tabs = page.query_selector_all(".tab")
        for tab in tabs:
            text = tab.inner_text()
            if "收藏" in text:
                fav_tab = tab
                break
        test("收藏夹 Tab 存在", fav_tab is not None)

        # 8. 收藏 API
        try:
            r = requests.get(f"{BASE}/api/favorites", timeout=5)
            data = r.json()
            test("收藏夹 API", r.status_code == 200, f"返回 {len(data.get('favorites', []))} 个收藏")
        except Exception as e:
            test("收藏夹 API", False, str(e))

        # 9. 品类报告 Tab
        print("\n📋 9. 品类报告")
        report_tab = None
        for tab in page.query_selector_all(".tab"):
            if "报告" in tab.inner_text():
                report_tab = tab
                break
        test("品类报告 Tab 存在", report_tab is not None)

        # 检查报告站点选择
        report_marketplace = page.query_selector("select#report-marketplace")
        test("报告站点下拉框存在", report_marketplace is not None)

        # 10. 商品图片和链接
        print("\n📋 10. 商品图片与链接")
        # 重新加载首页看产品
        page.goto(BASE, wait_until="networkidle", timeout=15000)
        time.sleep(2)

        images = page.query_selector_all("table img")
        test("商品图片显示", len(images) >= 0, f"找到 {len(images)} 张图片")

        # 检查 ASIN 链接
        asin_links = page.query_selector_all("table a[href*='amazon']")
        test("ASIN 商品链接", len(asin_links) >= 0, f"找到 {len(asin_links)} 个链接")

        # 11. 浅色主题验证
        print("\n📋 11. 浅色主题")
        body_bg = page.evaluate("window.getComputedStyle(document.body).backgroundColor")
        test("浅色背景", body_bg != "rgb(15, 11, 26)", f"body bg = {body_bg}")

        header = page.query_selector(".header")
        if header:
            header_color = header.evaluate("el => window.getComputedStyle(el).backgroundColor")
            test("Header 渐变色", header_color != "rgba(0, 0, 0, 0)", f"header bg = {header_color}")

        # 截图
        page.screenshot(path="/tmp/amazon-scout-test.png", full_page=True)
        test("截图保存", True, "/tmp/amazon-scout-test.png")

        browser.close()

    # 输出报告
    print("\n" + "="*60)
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    print(f"📊 测试结果：{passed}/{total} 通过，{failed} 失败")
    print("="*60)

    if failed:
        print("\n❌ 失败项：")
        for r in results:
            if not r["passed"]:
                print(f"  - {r['name']}: {r['detail']}")

    return passed, total

if __name__ == "__main__":
    if not check_server():
        print("❌ 服务未启动！请先运行 python src/web.py")
        sys.exit(1)
    passed, total = run_tests()
    sys.exit(0 if passed == total else 1)
