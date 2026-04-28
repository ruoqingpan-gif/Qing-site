#!/usr/bin/env python3
"""
PMP 笔记 Word → HTML 转换脚本（基于 pandoc）

功能：
- 扫描 pmp-docs/ 下所有 .docx 文件（按文件名排序）
- 用 pandoc 转换为 HTML（自动处理标题/列表/表格/加粗等）
- 提取内嵌图片到 pmp-images/（英文文件名）
- 图片标记占位符，需手动补充描述
- 输出 pmp-output.html，每个领域一个折叠卡片

用法：
  1. 将 .docx 文件放入 pmp-docs/ 文件夹（如 01 整合管理.docx）
  2. 运行: python convert_pmp.py
  3. 用 pmp-output.html 的内容替换 pmp-notes.html 中的卡片部分
"""

import os
import re
import sys
import shutil
from pathlib import Path

try:
    import pypandoc
except ImportError:
    print("错误：请先安装 pypandoc")
    print("运行: pip install pypandoc_binary")
    sys.exit(1)

# ===== 配置 =====
SCRIPT_DIR = Path(__file__).parent
DOCS_DIR = SCRIPT_DIR / "pmp-docs"
IMAGES_DIR = SCRIPT_DIR / "pmp-images"
OUTPUT_FILE = SCRIPT_DIR / "pmp-output.html"

# 中文 → 英文映射
TITLE_MAP = {
    "整合管理": "Integration Management 整合管理",
    "范围管理": "Scope Management 范围管理",
    "进度管理": "Schedule Management 进度管理",
    "成本管理": "Cost Management 成本管理",
    "质量管理": "Quality Management 质量管理",
    "资源管理": "Resource Management 资源管理",
    "沟通管理": "Communications Management 沟通管理",
    "风险管理": "Risk Management 风险管理",
    "采购管理": "Procurement Management 采购管理",
    "干系人管理": "Stakeholder Management 干系人管理",
}

FILENAME_MAP = {
    "整合管理": "integration",
    "范围管理": "scope",
    "进度管理": "schedule",
    "成本管理": "cost",
    "质量管理": "quality",
    "资源管理": "resource",
    "沟通管理": "communication",
    "风险管理": "risk",
    "采购管理": "procurement",
    "干系人": "stakeholder",
}


def safe_english_name(chinese_name):
    """中文文件名转英文"""
    result = chinese_name
    for cn, en in FILENAME_MAP.items():
        result = result.replace(cn, en)
    # 清理非安全字符
    result = re.sub(r'[^\w\s-]', '', result)
    result = re.sub(r'[\s]+', '_', result).strip('_').lower()
    result = re.sub(r'^\d+_', '', result)
    return result if result else "doc"


def rename_images_to_english(html_content, doc_prefix, images_dir):
    """将 HTML 中引用的图片重命名为英文，并更新引用"""
    # 找到所有 img 标签的 src
    img_pattern = re.compile(r'<img\s+[^>]*src="([^"]+)"[^>]*>', re.IGNORECASE)

    renamed_map = {}
    counter = [0]

    def replace_img_src(match):
        full_tag = match.group(0)
        old_src = match.group(1)

        if old_src in renamed_map:
            new_src = renamed_map[old_src]
        else:
            counter[0] += 1
            old_path = SCRIPT_DIR / old_src
            if old_path.exists():
                ext = old_path.suffix or ".png"
                new_name = f"{doc_prefix}_img{counter[0]}{ext}"
                new_path = images_dir / new_name
                shutil.copy2(old_path, new_path)
                new_src = f"pmp-images/{new_name}"
                renamed_map[old_src] = new_src
                print(f"  图片: {old_path.name} → {new_name}")
            else:
                new_src = old_src

        return full_tag.replace(old_src, new_src)

    result = img_pattern.sub(replace_img_src, html_content)
    return result


def convert_docx_to_html(docx_path, images_dir):
    """用 pandoc 将 .docx 转为 HTML 片段"""
    doc_prefix = safe_english_name(docx_path.stem)
    temp_media = SCRIPT_DIR / f"_temp_media_{doc_prefix}"

    try:
        # 用 pandoc 转换，提取图片到临时目录
        html = pypandoc.convert_file(
            str(docx_path),
            "html",
            extra_args=[
                "--extract-media", str(temp_media),
                "--wrap=none",
            ]
        )

        # 重命名图片为英文
        if temp_media.exists():
            html = rename_images_to_english(html, doc_prefix, images_dir)
            shutil.rmtree(temp_media, ignore_errors=True)

        return html

    except Exception as e:
        # 清理临时目录
        if temp_media.exists():
            shutil.rmtree(temp_media, ignore_errors=True)
        raise e


def postprocess_html(html):
    """后处理 HTML：清理 pandoc 输出，优化排版"""
    # 移除 pandoc 生成的空段落
    html = re.sub(r'<p>\s*</p>', '', html)

    # 给表格添加 class（方便样式控制）
    html = html.replace('<table', '<table class="pmp-table"')

    # 处理图片：替换为占位符提示
    img_pattern = re.compile(
        r'<img\s+[^>]*src="([^"]+)"[^>]*alt="([^"]*)"[^>]*/?>',
        re.IGNORECASE
    )

    def replace_img(match):
        src = match.group(1)
        alt = match.group(2)
        filename = Path(src).name
        return (
            f'<div class="img-placeholder">'
            f'<p class="img-label">[图片: {filename}]</p>'
            f'<p class="img-desc">请在此处补充图片描述内容</p>'
            f'</div>'
        )

    html = img_pattern.sub(replace_img, html)

    # 处理没有 alt 的 img 标签
    img_pattern2 = re.compile(r'<img\s+[^>]*src="([^"]+)"[^>]*/?>', re.IGNORECASE)
    html = img_pattern2.sub(
        lambda m: (
            f'<div class="img-placeholder">'
            f'<p class="img-label">[图片: {Path(m.group(1)).name}]</p>'
            f'<p class="img-desc">请在此处补充图片描述内容</p>'
            f'</div>'
        ),
        html
    )

    # 清理多余空行
    html = re.sub(r'\n{3,}', '\n\n', html)

    return html.strip()


def main():
    print("=" * 50)
    print("PMP 笔记 Word → HTML 转换工具")
    print("基于 pandoc，自动处理文字/表格/格式")
    print("=" * 50)

    # 检查目录
    if not DOCS_DIR.exists():
        DOCS_DIR.mkdir(parents=True)
        print(f"\n已创建文件夹: {DOCS_DIR}")
        print("请将 .docx 文件放入此文件夹后重新运行脚本。")
        print("文件名格式: 01 整合管理.docx, 02 范围管理.docx ...")
        return

    # 扫描 .docx 文件
    docx_files = sorted(DOCS_DIR.glob("*.docx"), key=lambda f: int(re.match(r'(\d+)', f.stem).group(1)) if re.match(r'(\d+)', f.stem) else 999)
    if not docx_files:
        print(f"\n未找到 .docx 文件。")
        print(f"请将文件放入: {DOCS_DIR}")
        return

    print(f"\n找到 {len(docx_files)} 个文件:")
    for f in docx_files:
        print(f"  - {f.name}")

    # 清理并重建图片目录
    if IMAGES_DIR.exists():
        shutil.rmtree(IMAGES_DIR)
    IMAGES_DIR.mkdir(parents=True)

    # 转换每个文件
    all_cards = []

    for docx_file in docx_files:
        print(f"\n处理: {docx_file.name}")
        print("-" * 40)

        try:
            html_content = convert_docx_to_html(docx_file, IMAGES_DIR)
            html_content = postprocess_html(html_content)

            # 提取标题
            card_title = re.sub(r'^\d+\s*', '', docx_file.stem).strip()
            full_title = TITLE_MAP.get(card_title, card_title)

            if html_content.strip():
                card = f'''<details class="note-card fade-in">
  <summary>{full_title}</summary>
  <div class="note-body">
{html_content}
  </div>
</details>'''
                all_cards.append(card)
                print(f"  转换成功")
            else:
                print(f"  未提取到内容")

        except Exception as e:
            print(f"  转换失败: {e}")
            all_cards.append(
                f'<details class="note-card fade-in">\n'
                f'  <summary>{docx_file.stem}</summary>\n'
                f'  <div class="note-body"><p>转换失败: {e}</p></div>\n'
                f'</details>'
            )

    # 统计
    image_files = list(IMAGES_DIR.glob("*")) if IMAGES_DIR.exists() else []

    # 输出
    output_html = "\n\n".join(all_cards)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output_html)

    print("\n" + "=" * 50)
    print("转换完成！")
    print("=" * 50)
    print(f"\n输出: {OUTPUT_FILE}")
    print(f"图片: {len(image_files)} 张 → {IMAGES_DIR}")

    if image_files:
        print("\n需要手动补充描述的图片:")
        for img in sorted(image_files):
            print(f"  - {img.name}")

    print(f"\n下一步:")
    print(f"  1. 用 pmp-output.html 替换 pmp-notes.html 中的卡片内容")
    print(f"  2. 浏览器检查排版")
    print(f"  3. 搜索 'img-placeholder' 手动补充图片描述")


if __name__ == "__main__":
    main()
