# BaiduWenzhangExporter（增强版）

> 百度文章批量备份工具 — 将 `wenzhang.baidu.com` 上的个人文章自动抓取并导出为 CSV/Markdown/TXT/WordPress WXR 格式。

---

## 与原版相比的改进

| 功能 | 原版 | 增强版 |
|------|------|--------|
| 浏览器支持 | 仅 Chrome | **Chrome + Edge（双版本）** |
| Edge Profile 自动登录 | ❌ | ✅ 复用已登录的 Edge Profile，无需手动输密码 |
| 预检查工具 | ❌ | ✅ `pre_check.py`：启动前自动检测环境、杀进程、测试连接 |
| 一键启动菜单 | ❌ | ✅ `一键启动.bat`：Windows 用户双击即可操作 |
| 输出格式 | CSV + WXR | CSV + WXR + **Markdown** + **TXT**（每篇文章一个文件） |
| Markdown 转换 | ❌ | ✅ `csv_to_md.py` |
| TXT 转换 | ❌ | ✅ `csv_to_txt.py` |
| Edge 进程清理 | ❌ | ✅ 自动杀残留进程、清除锁文件、GPU 缓存 |

---

## 快速开始

### 环境要求

- Windows 7/10/11（Python 脚本跨平台，菜单仅 Windows）
- Python 3.8+
- Microsoft Edge 或 Google Chrome
- 百度账号（需能访问 `wenzhang.baidu.com` 的「我的文章」）

### 安装

```bash
pip install selenium beautifulsoup4 webdriver-manager
```

WebDriver 会在首次运行时自动安装，无需手动下载。

### 使用

#### Windows 用户（推荐）

双击 `一键启动.bat`，按菜单提示操作：

```
=========================================
  百度文章批量备份工具 - 一键启动版
=========================================
 [1] 预检查 - 验证 Edge Profile 2 能否启动
 [2] 启动抓取 - Edge版_Profile2
 [3] 启动抓取 - Chrome版
 [4] CSV 转 Markdown
 [5] CSV 转 TXT
 [6] 打开输出目录
 [0] 退出
```

**推荐流程**：先选 `[1]` 预检查 → 全部通过后选 `[2]` 抓取 → 完成后选 `[4]`/`[5]` 转换格式。

#### 命令行用户

```bash
# 先运行预检查
python pre_check.py

# 抓取（Edge 版，自动使用 Profile 2 登录态）
python BaiduExporter_Edge.py

# 或抓取（Chrome 版，需手动登录）
python BaiduExporter.py

# 抓取完成后转换格式
python csv_to_md.py    # 生成 md_output/ 目录
python csv_to_txt.py   # 生成 txt_output/ 目录
```

### 抓取流程

1. 脚本自动打开浏览器
2. **Edge 版**：自动使用已登录的 Profile（无需手动登录）
3. **Chrome 版**：在浏览器中手动登录百度账号
4. 进入「我的文章」列表页，回到终端按回车
5. 脚本自动滚动扫描列表 → 逐篇抓取正文 → 实时写入 CSV
6. 抓取结束后自动生成排序版 CSV 和 WXR 文件

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `BaiduExporter.py` | Chrome 版抓取脚本（原版） |
| `BaiduExporter_Edge.py` | Edge 版抓取脚本（支持 Profile 自动登录） |
| `pre_check.py` | 预检查工具：检测环境、清进程、测试 Edge 启动 |
| `csv_to_md.py` | CSV → Markdown 批量转换 |
| `csv_to_txt.py` | CSV → TXT 批量转换 |
| `一键启动.bat` | Windows 一键启动菜单 |

运行后自动生成（不提交到仓库）：

| 文件 | 说明 |
|------|------|
| `baidu_articles_RAW.csv` | 原始抓取备份（断点续传依据） |
| `baidu_articles_SORTED.csv` | 按发布时间倒序排列 |
| `baidu_wordpress_import_FINAL.xml` | WordPress WXR 导入文件 |
| `md_output/` | 每篇文章一个 .md 文件 |
| `txt_output/` | 每篇文章一个 .txt 文件 |

---

## Edge Profile 自动登录

Edge 版抓取支持复用浏览器已有的登录状态，无需每次手动输入密码。

### 默认配置

- 用户数据目录：`%LOCALAPPDATA%\Microsoft\Edge\User Data`
- Profile 目录：`Profile 2`

### 自定义 Profile

如果账号在其他 Profile 中，设置环境变量：

```bash
set EDGE_PROFILE=Default        # 使用默认配置
set EDGE_PROFILE=Profile 1      # 使用 Profile 1
```

### 预检查工具

运行 `pre_check.py` 或选择菜单 `[1]`，它会自动执行 5 项检查：

1. Edge 浏览器是否已安装
2. Profile 目录是否存在
3. 锁文件状态 → 自动清除
4. 残留 Edge 进程 → 自动杀掉
5. 启动 Edge 测试 → 验证能否打开并登录百度

全部显示 `✅` 即可放心运行抓取脚本。

---

## 断点续传

脚本每抓取一篇就实时写入 `baidu_articles_RAW.csv`。如果中途中断（网络断开、电脑卡死、手动 Ctrl+C），直接重新运行即可，已抓取的文章会自动跳过。

断点判断依据是「原始URL」字段。

---

## 内容处理

- 定位百度文章正文容器（含 iframe）
- 自动点击「阅读全文 / 展开全文」
- 三段式滚动触发懒加载图片
- 移除空 div/p，保留正文段落和图片
- 压缩过多连续换行

---

## 导入 WordPress

1. 登录 WordPress 后台 → 工具 → 导入
2. 选择 WordPress 导入器
3. 上传 `baidu_wordpress_import_FINAL.xml`
4. 分配作者并导入

文章会自动归入「百度文章」分类，原始 URL 保存在 `_original_url` 自定义字段中。

---

## 常见问题

### Edge 启动失败 / 崩溃？

1. 关闭所有 Edge 窗口
2. 任务管理器中结束所有 `msedge.exe` 进程
3. 运行 `pre_check.py` 自动诊断
4. 仍失败则使用 Chrome 版（菜单 `[3]`）

### 图片导入 WordPress 后不显示？

百度图片有防盗链。建议安装 WordPress 图片搬运插件（如 Auto Upload Images），自动下载到本地。

### 文章显示「无内容」？

百度页面结构可能变化，或正文容器未加载成功。重试该篇即可。

---

## 许可

MIT License — 详见 [LICENSE](LICENSE)

基于 [VeteranXYZ/BaiduWenzhangExporter](https://github.com/VeteranXYZ/BaiduWenzhangExporter) 改进。
