"""
BaiduWenzhangExporter - Edge 浏览器版本
使用 Microsoft Edge + 已有登录 Profile 自动抓取百度文章
无需手动登录！直接使用 Edge 中已登录的百度账号会话。
"""
import os
import time
import random
import re
import csv
import sys
import shutil
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# ==================== 1. 全局配置 ====================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CSV = os.path.join(SCRIPT_DIR, "baidu_articles_RAW.csv")
SORTED_CSV = os.path.join(SCRIPT_DIR, "baidu_articles_SORTED.csv")
WXR_FILE = os.path.join(SCRIPT_DIR, "baidu_wordpress_import_FINAL.xml")

# Edge Profile 路径配置
# Profile 2 = 通常路径: C:\Users\<用户名>\AppData\Local\Microsoft\Edge\User Data\Profile 2
EDGE_USER_DATA = os.path.expandvars(
    os.environ.get(
        'EDGE_USER_DATA',
        r'%LOCALAPPDATA%\Microsoft\Edge\User Data'
    )
)
EDGE_PROFILE = os.environ.get('EDGE_PROFILE', 'Profile 2')

# ==================== 2. 工具函数 ====================

def kill_edge_processes():
    """强制结束所有 Edge 进程并清除锁文件/缓存"""
    print("🔪 正在关闭所有 Edge 进程...")
    import subprocess
    # 方法1: taskkill 强制杀
    subprocess.run("taskkill /F /IM msedge.exe /T", shell=True, capture_output=True)
    subprocess.run("taskkill /F /IM msedgewebview2.exe /T", shell=True, capture_output=True)
    time.sleep(3)

    # 验证: 是否还有残留进程
    result = subprocess.run("tasklist /FI \"IMAGENAME eq msedge.exe\" /FO CSV /NH",
                           shell=True, capture_output=True, encoding='gbk', errors='replace')
    if (result.stdout or '').strip() and "INFO" not in (result.stdout or ''):
        print("  ⚠️ 仍有 Edge 进程残留，再次尝试...")
        subprocess.run("taskkill /F /IM msedge.exe /T", shell=True, capture_output=True)
        time.sleep(2)

    # 删除所有锁文件（完整的3个）
    profile_dir = os.path.join(EDGE_USER_DATA, EDGE_PROFILE)
    for lock_name in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
        lock_file = os.path.join(profile_dir, lock_name)
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                print(f"  已清除锁文件: {lock_name}")
            except:
                pass

    # 删除可能损坏的 GPU 缓存
    gpu_cache = os.path.join(profile_dir, "GPUCache")
    if os.path.exists(gpu_cache):
        try:
            import shutil
            shutil.rmtree(gpu_cache, ignore_errors=True)
            print(f"  已清除 GPU 缓存")
        except:
            pass
    print("  ✅ 进程清理完成")

def find_existing_driver():
    """查找系统上已有的 msedgedriver.exe（无需联网）"""
    import glob as _glob
    search_paths = [
        # webdriver-manager 缓存
        os.path.join(os.path.expanduser("~"), ".wdm", "drivers", "edgedriver", "win64", "**", "msedgedriver.exe"),
        # Edge 安装目录自带
        os.path.join(os.environ.get("PROGRAMFILES", ""), "Microsoft", "Edge", "Application", "msedgedriver.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Microsoft", "Edge", "Application", "msedgedriver.exe"),
        # 常见自定义路径
        os.path.join(os.path.expanduser("~"), "msedgedriver.exe"),
    ]
    for pattern in search_paths:
        if "**" in pattern:
            matches = sorted(_glob.glob(pattern, recursive=True), reverse=True)
        else:
            matches = [pattern] if os.path.exists(pattern) else []
        for m in matches:
            if m and os.path.isfile(m):
                return m
    return None

def setup_edge_driver():
    """配置 Edge 浏览器，使用已登录的 Profile"""
    # 先杀掉所有 Edge 进程
    kill_edge_processes()
    
    options = Options()
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-features=RendererCodeIntegrity")
    options.add_argument("--remote-debugging-port=0")
    options.add_argument(f"--user-data-dir={EDGE_USER_DATA}")
    options.add_argument(f"--profile-directory={EDGE_PROFILE}")
    options.page_load_strategy = 'eager'
    
    errors = []
    
    # 尝试1: 查找本地已有的 msedgedriver（无需联网）
    existing_driver = find_existing_driver()
    if existing_driver:
        print(f"  尝试方法1: 使用已有驱动 {existing_driver}...")
        try:
            svc = Service(executable_path=existing_driver)
            driver = webdriver.Edge(service=svc, options=options)
            print("  ✅ Edge 启动成功！")
            driver.set_page_load_timeout(30)
            driver.maximize_window()
            return driver
        except Exception as e:
            errors.append(f"方法1: {str(e)[:100]}")
            print(f"  ❌ 方法1 失败")
    else:
        print("  未找到已有驱动，跳过方法1")
    
    # 尝试2: Selenium 自动检测（无需联网，自动匹配 Edge 版本）
    print("  尝试方法2: Selenium 自动检测驱动...")
    try:
        driver = webdriver.Edge(options=options)
        print("  ✅ Edge 启动成功！")
        driver.set_page_load_timeout(30)
        driver.maximize_window()
        return driver
    except Exception as e:
        errors.append(f"方法2: {str(e)[:100]}")
        print(f"  ❌ 方法2 失败")
    
    # 尝试3: webdriver-manager 在线下载（需要网络）
    print("  尝试方法3: 在线下载 EdgeDriver...")
    try:
        svc = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=svc, options=options)
        print("  ✅ Edge 启动成功！")
        driver.set_page_load_timeout(30)
        driver.maximize_window()
        return driver
    except Exception as e:
        errors.append(f"方法3: {str(e)[:100]}")
        print(f"  ❌ 方法3 失败")
    
    # 尝试4: 不带 Profile，手动登录 + Selenium 自动检测
    print("  尝试方法4: 不带 Profile，手动登录...")
    options2 = Options()
    options2.add_argument("--no-first-run")
    options2.add_argument("--no-default-browser-check")
    options2.add_argument("--disable-gpu")
    options2.add_argument("--disable-extensions")
    options2.add_argument("--disable-sync")
    options2.add_argument("--disable-features=RendererCodeIntegrity")
    options2.add_argument("--remote-debugging-port=0")
    options2.page_load_strategy = 'eager'
    
    try:
        driver = webdriver.Edge(options=options2)
        print("  ✅ Edge 启动成功 (需手动登录百度)")
        driver.set_page_load_timeout(30)
        driver.maximize_window()
        return driver
    except Exception as e:
        errors.append(f"方法4: {str(e)[:100]}")
        print(f"  ❌ 方法4 也失败")
    
    # 全部失败
    print(f"\n❌ 所有方法都失败了！错误信息:")
    for err in errors:
        print(f"  - {err}")
    print(f"\n可能的原因:")
    print(f"  1. Edge 浏览器未正确安装")
    print(f"  2. 系统权限不足")
    print(f"\n建议: 尝试选项 [1] Chrome版抓取（需安装Chrome浏览器）")
    sys.exit(1)

def clean_html_content(raw_html):
    """HTML 净化器"""
    if not raw_html or "<div" not in raw_html:
        return "<p>无内容</p>"
    soup = BeautifulSoup(raw_html, "html.parser")
    content_div = soup.find("div", id=re.compile(r"detailArticleContent_")) or \
                  soup.find("div", class_=re.compile(r"pcs-article-content_"))
    if not content_div:
        return "<p>无内容</p>"
    parts = []
    for child in content_div.children:
        if child.name:
            if child.name in ["p", "div"] and not child.get_text(strip=True) and not child.find("img"):
                continue
            parts.append(str(child))
        elif isinstance(child, str) and child.strip():
            parts.append(child.replace("\n", "<br>"))
    content = "".join(parts)
    content = re.sub(r"(<br>\s*){3,}", "<br><br>", content)
    return content.strip() or "<p>无内容</p>"

def get_done_urls():
    """断点续传"""
    done_urls = set()
    if os.path.exists(RAW_CSV):
        try:
            with open(RAW_CSV, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("原始URL"):
                        done_urls.add(row["原始URL"].strip())
        except:
            pass
    return done_urls

# ==================== 3. 核心抓取 ====================

def collect_all_urls(driver):
    """深度滚动，收集所有文章链接"""
    print("🚀 正在扫描文章列表...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    no_change_count = 0
    
    while no_change_count < 10:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.8 + random.uniform(0.1, 0.4))
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        units = driver.find_elements(By.CSS_SELECTOR, 'li.unit[id^="key_"]')
        print(f"  > 已发现文章: {len(units)} 篇...", end="\r")
        
        if new_height == last_height:
            no_change_count += 1
        else:
            no_change_count = 0
            last_height = new_height
    
    urls = []
    for u in units:
        key = u.get_attribute("id")[4:]
        prefix = "article" if "article" in u.get_attribute("class") else "page"
        urls.append(f"https://wenzhang.baidu.com/{prefix}/view?key={key}")
    
    print(f"\n✅ 列表扫描完成！共 {len(urls)} 条链接。")
    return urls

def fetch_article(driver, url):
    """抓取单篇文章"""
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        # 1. 进入 iframe
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe.pcs-article-iframe")))
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # 2. 展开全文
        driver.execute_script("""
            let btns = document.querySelectorAll('*');
            for(let b of btns) { 
                let text = (b.innerText || '').trim();
                if(text === '阅读全文' || text === '展开全文' || text === '展开') { b.click(); break; } 
            }
        """)
        time.sleep(0.5)
        
        # 3. 触发懒加载
        for p in [0.33, 0.66, 1.0]:
            driver.execute_script(f"window.scrollTo({{top: document.body.scrollHeight * {p}, behavior: 'smooth'}});")
            time.sleep(0.5)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.switch_to.default_content()

        title_el = soup.select_one("h1, .pcs-article-title_ptkaiapt4bxy_baiduscarticle")
        title = title_el.get_text(strip=True) if title_el else "无标题"
        
        date_str = "1970-01-01"
        time_el = soup.select_one(".time-cang")
        if time_el:
            m = re.search(r"(\d{4})[年\.\-](\d{1,2})[月\.\-](\d{1,2})", time_el.get_text())
            if m: date_str = f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"

        content_el = soup.select_one("#detailArticleContent_ptkaiapt4bxy_baiduscarticle, .pcs-article-content_ptkaiapt4bxy_baiduscarticle")
        clean_content = clean_html_content(str(content_el)) if content_el else "<p>无内容</p>"
        
        return {"title": title, "content": clean_content, "date": date_str, "url": url}
    except Exception as e:
        print(f"  [!] 抓取出错: {str(e)[:50]}")
        try: driver.switch_to.default_content()
        except: pass
        return None

# ==================== 4. 数据后期处理 ====================

def build_final_package():
    """排序 + 生成 CSV 和 WXR"""
    print("\n📦 正在进行数据组装...")
    if not os.path.exists(RAW_CSV): return

    articles = []
    with open(RAW_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("发布时间"): articles.append(row)

    if not articles:
        print("暂无抓取到的数据。")
        return

    def safe_date(art):
        try: return datetime.strptime(art["发布时间"], "%Y-%m-%d")
        except: return datetime(1970, 1, 1)
    articles.sort(key=safe_date, reverse=True)

    with open(SORTED_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["标题", "文章内容", "发布时间", "原始URL"])
        writer.writeheader()
        writer.writerows(articles)

    channel_pubDate = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
    xml_header = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
    xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
    xmlns:content="http://purl.org/rss/1.0/modules/content/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:wp="http://wordpress.org/export/1.2/">
<channel>
    <title>百度文章迁移</title>
    <link>https://wenzhang.baidu.com</link>
    <description>BaiduWenzhang to WordPress Exporter</description>
    <pubDate>{channel_pubDate}</pubDate>
    <language>zh-CN</language>
    <wp:wxr_version>1.2</wp:wxr_version>
"""
    item_tpl = """    <item>
        <title><![CDATA[{title}]]></title>
        <pubDate>{pub_date}</pubDate>
        <dc:creator><![CDATA[admin]]></dc:creator>
        <content:encoded><![CDATA[{content}]]></content:encoded>
        <wp:post_date><![CDATA[{raw_date} 00:00:00]]></wp:post_date>
        <wp:post_name><![CDATA[{slug}]]></wp:post_name>
        <wp:status><![CDATA[publish]]></wp:status>
        <wp:post_type><![CDATA[post]]></wp:post_type>
        <category domain="category" nicename="baidu-wenzhang"><![CDATA[百度文章]]></category>
        <wp:postmeta><wp:meta_key><![CDATA[_original_url]]></wp:meta_key><wp:meta_value><![CDATA[{url}]]></wp:meta_value></wp:postmeta>
    </item>
"""
    with open(WXR_FILE, "w", encoding="utf-8") as f:
        f.write(xml_header)
        for i, art in enumerate(articles):
            dt = safe_date(art)
            slug_raw = re.sub(r"[^\w\s-]", "", art["标题"]).strip()
            slug = re.sub(r"\s+", "-", slug_raw.lower())[:50] or f"post-{i}"
            f.write(item_tpl.format(
                title=art["标题"].replace("]]>", "]]&gt;"),
                pub_date=dt.strftime("%a, %d %b %Y 00:00:00 +0800"),
                content=art["文章内容"].replace("]]>", "]]&gt;"),
                raw_date=art["发布时间"],
                slug=slug,
                url=art["原始URL"]
            ))
        f.write("</channel>\n</rss>")

    print(f"🎉 任务完成！\n CSV: {SORTED_CSV}\n WXR: {WXR_FILE}")

# ==================== 5. 主程序 ====================

if __name__ == "__main__":
    print("="*60)
    print("  BaiduWenzhangExporter - Edge 版本")
    print(f"  Edge Profile: {EDGE_PROFILE}")
    print(f"  User Data:   {EDGE_USER_DATA}")
    print("="*60)
    
    # 确保 Edge 没有其他实例在运行（Profile 锁冲突）
    print("\n⚠️ 请确保关闭所有 Edge 浏览器窗口，否则会报 Profile 锁定错误！")
    input("按回车继续...")
    
    if not os.path.exists(RAW_CSV):
        with open(RAW_CSV, "w", encoding="utf-8-sig", newline="") as f:
            csv.writer(f).writerow(["标题", "文章内容", "发布时间", "原始URL"])

    driver = setup_edge_driver()
    try:
        # 使用已登录的 Profile，自动携带百度 Cookie
        driver.get("https://wenzhang.baidu.com/")
        
        # 检查是否已登录
        current_url = driver.current_url
        if "passport.baidu.com" in current_url or "login" in current_url.lower():
            print(f"\n⚠️ Edge Profile 未登录百度账号！")
            print(f"  当前 URL: {current_url}")
            print(f"  请在打开的 Edge 窗口中手动登录百度...")
            input("登录后按回车继续...")
            driver.get("https://wenzhang.baidu.com/")
        
        # 确认在文章列表页
        print("\n当前页面 URL:", driver.current_url)
        if "wenzhang.baidu.com" in driver.current_url:
            print("✅ 已进入百度文章页面！")
        else:
            print("⚠️ 未进入百度文章页面，请手动导航到『我的文章』列表")
            input("进入列表后按回车继续...")
        
        all_urls = collect_all_urls(driver)
        done_urls = get_done_urls()
        todo_urls = [u for u in all_urls if u not in done_urls]
        
        print(f"📊 总计 {len(all_urls)} 篇，已抓取 {len(done_urls)} 篇，待抓取 {len(todo_urls)} 篇。")

        if todo_urls:
            with open(RAW_CSV, "a", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                for i, url in enumerate(todo_urls):
                    art = fetch_article(driver, url)
                    if art:
                        writer.writerow([art["title"], art["content"], art["date"], art["url"]])
                        f.flush()
                        print(f"[{len(done_urls)+i+1}/{len(all_urls)}] ✅ {art['title'][:20]}")
                    else:
                        print(f"[{len(done_urls)+i+1}/{len(all_urls)}] ⏭️ 跳过")
                    time.sleep(random.uniform(0.5, 1.2))
        else:
            print("✨ 所有文章已抓取完毕。")
            
    finally:
        driver.quit()
        
    build_final_package()
