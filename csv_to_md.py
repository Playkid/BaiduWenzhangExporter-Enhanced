"""
CSV → Markdown 批量转换工具
将 baidu_articles_SORTED.csv 中的每篇文章转为独立的 .md 文件
"""
import csv
import os
import re
import sys

# 默认输入文件
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(SCRIPT_DIR, "baidu_articles_SORTED.csv")
DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "md_output")


def safe_filename(title: str, max_len: int = 80) -> str:
    """去除标题中的非法字符，生成安全文件名"""
    # 替换 Windows 文件名非法字符
    safe = re.sub(r'[\\/:*?"<>|]', '_', title)
    # 去除多余空格
    safe = re.sub(r'\s+', ' ', safe).strip()
    return safe[:max_len] if len(safe) > max_len else safe


def html_to_markdown(html: str) -> str:
    """简单的 HTML 转 Markdown（保留基本格式）"""
    text = html
    # <br> → 换行
    text = re.sub(r'<br\s*/?>', '\n', text)
    # <p>...</p> → 段落 + 换行
    text = re.sub(r'</p>\s*<p[^>]*>', '\n\n', text)
    text = re.sub(r'<p[^>]*>', '', text)
    text = re.sub(r'</p>', '\n\n', text)
    # <strong> / <b>
    text = re.sub(r'<strong>|</strong>|<b>|</b>', '**', text)
    # <em> / <i>
    text = re.sub(r'<em>|</em>|<i>|</i>', '*', text)
    # <img> → 保留 URL 引用
    text = re.sub(r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>', r'![](\1)', text)
    # <a> → Markdown 链接
    text = re.sub(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text)
    # 清理剩余 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 清理多余空白
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    output_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT_DIR

    if not os.path.exists(csv_path):
        print(f"❌ 找不到文件: {csv_path}")
        print(f"   请先运行 BaiduExporter.py 抓取文章")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    total = 0
    success = 0
    skip = 0

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            total += 1
            title = row.get('标题', f'未命名_{i}').strip()
            content_html = row.get('文章内容', '<p>无内容</p>')
            pub_date = row.get('发布时间', '未知').strip()
            original_url = row.get('原始URL', '').strip()

            if not title:
                title = f'未命名_{i}'

            filename = safe_filename(title) + '.md'
            filepath = os.path.join(output_dir, filename)

            # 跳过已存在文件（避免覆盖）
            if os.path.exists(filepath):
                print(f"  [{i}] ⏭️ 跳过已存在: {filename}")
                skip += 1
                continue

            md_content = html_to_markdown(content_html)

            with open(filepath, 'w', encoding='utf-8') as mf:
                mf.write(f"# {title}\n\n")
                mf.write(f"> 发布时间：{pub_date}\n")
                mf.write(f"> 原始链接：{original_url}\n\n")
                mf.write("---\n\n")
                mf.write(md_content)

            print(f"  [{i}] ✅ {filename}")
            success += 1

    print(f"\n📊 转换完成：总计 {total} 篇，成功 {success} 篇，跳过 {skip} 篇")
    print(f"📁 输出目录: {output_dir}")


if __name__ == '__main__':
    main()
