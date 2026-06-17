"""
pre_check.py - Edge Profile 2 启动预检查工具
双击运行，自动检测并修复所有可能导致启动失败的问题
"""
import os, time, subprocess, sys, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EDGE_USER_DATA = os.path.expandvars(
    os.environ.get('EDGE_USER_DATA', r'%LOCALAPPDATA%\Microsoft\Edge\User Data')
)
EDGE_PROFILE = os.environ.get('EDGE_PROFILE', 'Profile 2')
PROFILE_DIR = os.path.join(EDGE_USER_DATA, EDGE_PROFILE)

print("=" * 60)
print("  Edge Profile 2 启动预检查工具")
print("=" * 60)

# ===== 检查1: Edge 浏览器 =====
print("\n[1/5] 检查 Edge 浏览器...")
edge_found = False
for p in [
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
]:
    if os.path.exists(p):
        edge_found = True
        print(f"  ✅ Edge 已安装: {p}")
        break
if not edge_found:
    print("  ❌ 未找到 Edge 浏览器！请先安装 Microsoft Edge")
    input("按回车退出...")
    sys.exit(1)

# ===== 检查2: Profile 2 目录 =====
print("\n[2/5] 检查 Profile 2 目录...")
if not os.path.exists(PROFILE_DIR):
    print(f"  ❌ Profile 2 目录不存在: {PROFILE_DIR}")
    print(f"  请在 Edge 中确认 Profile 2 存在（地址栏输入 edge://settings/profiles）")
    input("按回车退出...")
    sys.exit(1)

# 读取 Profile 显示名称
profile_name = "?"
prefs_file = os.path.join(PROFILE_DIR, "Preferences")
if os.path.exists(prefs_file):
    try:
        with open(prefs_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            profile_name = data.get('profile', {}).get('name', '?')
    except:
        pass
print(f"  ✅ Profile 2 目录存在")
print(f"  显示名称: {profile_name}")
print(f"  路径: {PROFILE_DIR}")

# ===== 检查3: 锁文件 =====
print("\n[3/5] 检查锁文件状态...")
lock_files = ["SingletonLock", "SingletonSocket", "SingletonCookie"]
has_lock = False
for lock_name in lock_files:
    lock_path = os.path.join(PROFILE_DIR, lock_name)
    if os.path.exists(lock_path):
        has_lock = True
        print(f"  🔒 发现锁文件: {lock_name}")
print("  ✅ 无锁文件（已清除或可正常启动）" if not has_lock else "  ⚠️ 锁文件存在，需要清除")

# ===== 检查4: 杀掉 Edge 进程 =====
print("\n[4/5] 检查 Edge 进程...")
result = subprocess.run(
    'tasklist /FI "IMAGENAME eq msedge.exe" /FO CSV /NH',
    shell=True, capture_output=True, text=True
)
lines = [l for l in result.stdout.strip().split('\n') if l.strip() and 'INFO' not in l]
if lines:
    print(f"  ⚠️ 发现 {len(lines)} 个 Edge 进程正在运行：")
    for l in lines[:3]:
        parts = l.strip('"').split('","')
        if len(parts) >= 2:
            print(f"    PID={parts[1]}  {parts[0]}")
    print("  → 正在自动清除...")
    subprocess.run("taskkill /F /IM msedge.exe /T", shell=True, capture_output=True)
    time.sleep(3)
    result2 = subprocess.run(
        'tasklist /FI "IMAGENAME eq msedge.exe" /FO CSV /NH',
        shell=True, capture_output=True, text=True
    )
    remaining = [l for l in result2.stdout.strip().split('\n') if l.strip() and 'INFO' not in l]
    if remaining:
        print(f"  ❌ 仍有 {len(remaining)} 个进程无法清除，请手动关闭 Edge")
    else:
        print("  ✅ 所有 Edge 进程已清除")
else:
    print("  ✅ 无 Edge 进程运行")

# 清除锁文件（杀进程后再检查一次）
for lock_name in lock_files:
    lock_path = os.path.join(PROFILE_DIR, lock_name)
    if os.path.exists(lock_path):
        try:
            os.remove(lock_path)
            print(f"  ✅ 已删除锁文件: {lock_name}")
        except:
            print(f"  ⚠️ 无法删除锁文件: {lock_name}（可能被占用）")

# ===== 检查5: 尝试启动 Edge =====
print("\n[5/5] 尝试启动 Edge (带 Profile 2)...")
try:
    import importlib.util
    # Check selenium
    spec = importlib.util.find_spec("selenium")
    if spec is None:
        print("  ❌ selenium 未安装，请先运行: pip install selenium")
        input("按回车退出...")
        sys.exit(1)
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.edge.options import Options
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    print("  ✅ Selenium 模块已加载")

    options = Options()
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-features=RendererCodeIntegrity")
    options.add_argument("--remote-debugging-port=0")
    options.add_argument(f"--user-data-dir={EDGE_USER_DATA}")
    options.add_argument("--profile-directory=Profile 2")
    options.page_load_strategy = 'eager'

    print("  正在启动 Edge（最多等待 30 秒）...")
    service = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)
    print("  ✅✅✅ Edge 启动成功！Profile 2 完全可用！")

    driver.get("https://wenzhang.baidu.com/")
    time.sleep(3)
    url = driver.current_url
    print(f"  当前页面: {url}")

    if "passport.baidu.com" in url or "login" in url.lower():
        print("  ⚠️ 未自动登录（Cookie 可能过期，需手动登录一次）")
        print("  → 请在打开的 Edge 窗口中手动登录百度账号")
        print("  → 登录后关闭浏览器，重新运行本工具验证")
    else:
        print("  ✅ 已自动登录百度！Profile 2 的登录状态正常")

    driver.quit()
    print("\n" + "=" * 60)
    print("  ✅ 所有检查通过！可以正常运行 BaiduExporter_Edge.py")
    print("=" * 60)

except Exception as e:
    print(f"\n  ❌ 启动失败: {type(e).__name__}")
    print(f"  错误信息: {str(e)[:200]}")
    print("\n  建议操作:")
    print("  1. 确认所有 Edge 窗口已关闭")
    print("  2. 在任务管理器中确认无 msedge.exe 进程")
    print("  3. 尝试重启电脑后再次运行")
    print("  4. 如仍失败，使用 Chrome 版抓取（选项 [1]）")

print()
input("按回车退出...")
