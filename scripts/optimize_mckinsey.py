#!/usr/bin/env python3
"""
麦肯锡46种框架 PPT转MD 优化脚本
- 移除空表格行和元数据行
- 按框架类型重新组织
- 统一标题格式
"""

import re
from pathlib import Path

# 框架分类定义
FRAMEWORK_CATEGORIES = {
    "逻辑思考": [
        "金字塔原理", "MECE原则", "归纳与演绎", "PREP模型", "认知重建", "六顶思考帽"
    ],
    "创意与想象": [
        "SCAMPER法", "曼陀罗思考法", "书面脑风暴", "KJ法"
    ],
    "问题解决": [
        "逻辑树", "流程图", "差距分析", "空—雨—伞", "议题树", "假设思考"
    ],
    "决策分析": [
        "利弊均衡表", "支付矩阵", "决策矩阵", "PDCA", "ABC理论", "重要紧急矩阵"
    ],
    "市场营销": [
        "3C分析", "STP分析", "用户画像分析", "消费者旅程", "PEST分析", "五力分析",
        "AIDMA模型", "产品生命周期", "市场营销组合", "品牌资产"
    ],
    "经营战略": [
        "SWOT分析", "价值链分析", "波士顿矩阵", "安索夫矩阵", "波特3大战略",
        "定位地图", "帕累托法则", "核心竞争力分析"
    ],
    "组织管理": [
        "7S分析", "KPI树", "卡茨管理技能", "PM理论", "马斯洛需求理论", "5W1H(6W2H)"
    ]
}

def get_category(framework_name: str) -> str:
    """根据框架名称确定分类"""
    for category, frameworks in FRAMEWORK_CATEGORIES.items():
        for fw in frameworks:
            if fw in framework_name:
                return category
    return "其他"

def clean_content(lines: list) -> list:
    """清理内容：移除空表格行、元数据行等"""
    cleaned = []
    skip_patterns = [
        r'^来源\s*\|',  # 元数据行
        r'^制作\s*\|',
        r'^\s*\|\s*\|\s*\|\s*\|?\s*$',  # 空表格行
    ]

    for line in lines:
        # 跳过空行
        if not line.strip():
            cleaned.append(line)
            continue

        # 跳过匹配的模式
        skip = False
        for pattern in skip_patterns:
            if re.match(pattern, line.strip()):
                skip = True
                break

        if not skip:
            cleaned.append(line)

    return cleaned

def parse_slides(content: str) -> list:
    """解析所有幻灯片"""
    # 按幻灯片分割
    slide_pattern = r'<!-- Slide number: (\d+) -->'
    parts = re.split(slide_pattern, content)

    slides = []
    for i in range(1, len(parts), 2):
        slide_num = parts[i]
        slide_content = parts[i + 1] if i + 1 < len(parts) else ""

        # 提取框架名称
        framework_match = re.search(r'46种框架之[：:]\s*([^\n]+)', slide_content)
        framework_name = framework_match.group(1).strip() if framework_match else "未知框架"

        # 获取第一行作为标题
        title_lines = [l for l in slide_content.split('\n') if l.strip() and not l.startswith('来源') and not l.startswith('制作') and not l.startswith('软件')][:3]

        slides.append({
            'num': int(slide_num),
            'framework': framework_name,
            'category': get_category(framework_name),
            'content': slide_content,
            'title': ' '.join(title_lines[:2]) if title_lines else framework_name
        })

    return slides

def format_slide_content(content: str, slide_num: int) -> str:
    """格式化单个幻灯片内容"""
    lines = content.split('\n')
    result = []

    # 跳过开头的信息行（图片引用、标题等）
    skip_first = True
    in_table = False

    for line in lines:
        stripped = line.strip()

        # 跳过元数据行
        if stripped.startswith('来源') or stripped.startswith('制作') or stripped.startswith('软件'):
            continue
        if '《麦肯锡思维工具》' in stripped or '《麦肯锡思考工具》' in stripped:
            continue
        if stripped.startswith('46种框架之'):
            continue

        # 处理空表格行
        if re.match(r'^\|?\s*\|?\s*\|?\s*\|?\s*\|?\s*$', stripped):
            continue

        # 跳过重复的图片引用（同一张幻灯片多次出现）
        if stripped.startswith('![](图片') and skip_first:
            skip_first = False
            result.append(line)
            continue

        # 保留内容
        result.append(line)

    return '\n'.join(result)

def generate_toc(slides: list) -> str:
    """生成目录"""
    toc = ["## 目录\n"]

    for category, frameworks in FRAMEWORK_CATEGORIES.items():
        # 检查该分类是否有幻灯片
        category_slides = [s for s in slides if s['framework'] in [f for f in frameworks]]
        if not category_slides:
            continue

        # 分类标题
        toc.append(f"- **{category}**\n")

        for framework in frameworks:
            framework_slides = [s for s in category_slides if framework in s['framework']]
            if not framework_slides:
                continue

            # 框架链接
            anchor = framework.lower().replace('(', '').replace(')', '').replace('（', '').replace('）', '').replace(' ', '-')
            toc.append(f"  - [{framework}](#{anchor})  ({len(framework_slides)}页)\n")

        toc.append("\n")

    return ''.join(toc)

def generate_markdown(slides: list) -> str:
    """生成优化后的Markdown"""
    output = []

    # 封面
    output.append("# 麦肯锡思维工具：46种框架详解\n")
    output.append("*来源：《麦肯锡思维工具》*\n")
    output.append("\n---\n\n")

    # 生成目录
    output.append(generate_toc(slides))
    output.append("---\n\n")

    # 按分类组织
    for category, frameworks in FRAMEWORK_CATEGORIES.items():
        # 找到该分类下的幻灯片
        category_slides = [s for s in slides if s['framework'] in [f for f in frameworks]]

        if not category_slides:
            continue

        output.append(f"## {category}\n\n")

        # 按框架分组
        for framework in frameworks:
            framework_slides = [s for s in category_slides if framework in s['framework']]

            if not framework_slides:
                continue

            output.append(f"### {framework}\n\n")

            # 添加锚点标记
            anchor = framework.lower().replace('(', '').replace(')', '').replace('（', '').replace('）', '').replace(' ', '-')
            output.append(f"<!-- anchor: {anchor} -->\n\n")

            for slide in framework_slides:
                formatted = format_slide_content(slide['content'], slide['num'])
                output.append(formatted)
                output.append("\n---\n\n")

    return ''.join(output)

def main():
    input_file = "/Users/nexlume/Downloads/麦肯锡思维工具：详解46种框架.md"
    output_file = "/Users/nexlume/Downloads/麦肯锡思维工具：详解46种框架_优化版.md"

    print(f"读取文件: {input_file}")
    content = Path(input_file).read_text(encoding='utf-8')

    print("解析幻灯片...")
    slides = parse_slides(content)
    print(f"共解析 {len(slides)} 张幻灯片")

    print("生成优化内容...")
    markdown = generate_markdown(slides)

    print(f"写入文件: {output_file}")
    Path(output_file).write_text(markdown, encoding='utf-8')

    print("完成!")

if __name__ == "__main__":
    main()