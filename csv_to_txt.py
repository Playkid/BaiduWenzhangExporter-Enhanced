"""
CSV → TXT 批量转换工具
将 baidu_articles_SORTED.csv 中的每篇文章转为独立的 .txt 文件
"""
import csv
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(SCRIPT_DIR, "baidu_articles_SORTED.csv")
DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "txt_output")


def safe_filename(title: str, max_len: int = 80) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', '_', title)
    safe = re.sub(r'\s+', ' ', safe).strip()
    return safe[:max_len] if len(safe) > max_len else safe


def html_to_plain_text(html: str) -> str:
    """HTML 转纯文本"""
    text = html
    # <br> → 换行
    text = re.sub(r'<br\s*/?>', '\n', text)
    # <p>...</p> → 段落换行
    text = re.sub(r'</p>\s*<p[^>]*>', '\n\n', text)
    text = re.sub(r'<p[^>]*>', '', text)
    text = re.sub(r'</p>', '\n', text)
    # <img> → 图片URL
    text = re.sub(r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>', r'[图片: \1]', text)
    # <a> → [文字](链接)
    text = re.sub(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text)
    # <li> → -
    text = re.sub(r'<li[^>]*>', '- ', text)
    text = re.sub(r'</li>', '\n', text)
    # 清理其余标签
    text = re.sub(r'<[^>]+>', '', text)
    # HTML 实体
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    # 清理多余空白行
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

            filename = safe_filename(title) + '.txt'
            filepath = os.path.join(output_dir, filename)

            if os.path.exists(filepath):
                print(f"  [{i}] ⏭️ 跳过已存在: {filename}")
                skip += 1
                continue

            plain_text = html_to_plain_text(content_html)

            with open(filepath, 'w', encoding='utf-8') as tf:
                tf.write(f"{title}\n")
                tf.write(f"{'=' * len(title)}\n\n")
                tf.write(f"发布时间：{pub_date}\n")
                tf.write(f"原始链接：{original_url}\n")
                tf.write(f"{'─' * 50}\n\n")
                tf.write(plain_text)

            print(f"  [{i}] ✅ {filename}")
            success += 1

    print(f"\n📊 转换完成：总计 {total} 篇，成功 {success} 篇，跳过 {skip} 篇")
    print(f"📁 输出目录: {output_dir}")


if __name__ == '__main__':
    main()
