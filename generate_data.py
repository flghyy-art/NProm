import os
import re
import json

# 配置 MD 文件目录（把 .py 脚本放在仓库根目录，或修改此路径）
MD_DIR = "."  # 当前目录，也可写为 "./templates-jav"
OUTPUT_FILE = "nprom_data.js"  # 输出的 JS 文件

# 模块定义：文件名前缀 -> (模块ID, 模块Label, 模块Icon)
MODULE_MAP = {
    "01-场景主题": ("01", "01-场景主题", "🏠"),
    "02-景别构图": ("02", "02-景别构图", "🎞"),
    "03-裸露液体": ("03", "03-裸露液体", "💧"),
    "04-服装专项": ("04", "04-服装专项", "👗"),
    "05-光影氛围": ("05", "05-光影氛围", "☀️"),
    "06-姿势动作": ("06", "06-姿势动作", "🧍"),
    "07-表情眼神": ("07", "07-表情眼神", "😊"),
    "08-风格胶片": ("08", "08-风格胶片", "🎨"),
    "09-妆容专项": ("09", "09-妆容专项", "💄"),
    "10-发型饰品": ("10", "10-发型饰品", "💇"),
    "11-瑕疵细节": ("11", "11-瑕疵细节", "🔍"),
    "12-纹身标记": ("12", "12-纹身标记", "🖋️"),
    "13-道具宠物": ("13", "13-道具宠物", "🧸"),
    "14-人格卡片": ("14", "14-人格卡片", "🪪"),
}

def extract_phrases_from_md(filepath):
    """
    从 Markdown 文件中提取英文提示词短语。
    这里假设短语通常出现在表格、列表、代码块或普通段落中。
    返回一个短语列表（去重、排序）。
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"读取文件失败 {filepath}: {e}")
        return []

    phrases = set()

    # 1. 提取表格中的内容：每行按 | 分割，取英文单词/短语
    #    简单的启发式：每行至少包含一个英文单词，且不包含中文
    lines = text.splitlines()
    for line in lines:
        # 跳过纯中文行或空行
        if not re.search(r'[a-zA-Z]', line):
            continue
        # 按 | 分割表格行
        cells = line.split('|')
        for cell in cells:
            cell = cell.strip()
            # 过滤掉中文、纯数字、太短的字符串
            if not re.search(r'[\u4e00-\u9fff]', cell) and len(cell) > 2 and re.search(r'[a-zA-Z]', cell):
                # 进一步清理：去掉 Markdown 语法（粗体、斜体、链接等）
                clean = re.sub(r'\*\*|__|~~|`|\[|\]|\(|\)', '', cell)
                clean = clean.strip()
                # 保留常见的英文短语（允许空格、连字符、加号、括号）
                if re.match(r'^[\w\-\.\+\(\)\:\;\,\'\"\s]{3,}$', clean):
                    phrases.add(clean.lower())

    # 2. 提取列表项（以 - 或 * 开头，后跟英文短语）
    list_pattern = re.findall(r'^[\-\*]\s+([\w\-\.\+\(\)\:\;\,\'\"\s]{3,})$', text, re.MULTILINE)
    for item in list_pattern:
        clean = item.strip()
        if not re.search(r'[\u4e00-\u9fff]', clean) and len(clean) > 2:
            phrases.add(clean.lower())

    # 3. 提取代码块中的内容
    code_blocks = re.findall(r'```[\s\S]*?```', text)
    for block in code_blocks:
        # 去除代码标记
        content = re.sub(r'```\w*', '', block).replace('```', '')
        # 按逗号或换行分割
        for part in re.split(r'[,\n]', content):
            part = part.strip()
            if part and not re.search(r'[\u4e00-\u9fff]', part) and len(part) > 2:
                phrases.add(part.lower())

    # 4. 提取普通段落中的英文短语（简单处理：取长度在 3-50 之间的英文片段）
    #    但要注意排除太长的句子
    eng_snippets = re.findall(r'\b([a-zA-Z][\w\-\.\+\(\)\:\;\,\'\"\s]{2,50})\b', text)
    for snippet in eng_snippets:
        snippet = snippet.strip()
        if snippet and len(snippet) > 2 and not re.search(r'[\u4e00-\u9fff]', snippet):
            # 简单过滤掉一些常见噪声词
            if snippet.lower() not in ('the', 'and', 'for', 'with', 'from', 'that', 'this', 'have', 'has', 'had', 'not', 'but', 'are', 'was', 'were', 'been', 'can', 'may', 'will', 'would', 'could', 'should', 'make', 'made', 'making'):
                phrases.add(snippet.lower())

    # 清理和排序
    final = sorted(list(phrases))
    # 移除重复并再次过滤过短/过长的
    final = [p for p in final if 2 < len(p) < 80 and re.search(r'[a-zA-Z]{2,}', p)]
    return final

def build_module_from_files(prefix, mod_id, label, icon):
    """
    给定文件名前缀（如 "01-场景主题"），查找对应的 MD 文件，
    提取短语，并构建模块数据结构（含自动分类）。
    这里我们将每个文件中的短语按自然段落或标题自动分成 category，
    但为了简单，暂时将所有短语归到一个 category 下，名为 "通用短语"。
    如果需要更精细的分类，需要解析 Markdown 标题。
    """
    # 查找文件
    candidates = [f for f in os.listdir(MD_DIR) if f.startswith(prefix) and f.endswith('.md')]
    if not candidates:
        print(f"警告: 未找到匹配 {prefix} 的文件")
        return None
    filepath = os.path.join(MD_DIR, candidates[0])
    phrases = extract_phrases_from_md(filepath)
    if not phrases:
        print(f"警告: 从 {filepath} 未提取到任何短语")
        return None

    # 简单分类：将所有短语归为一个 category
    categories = [
        {
            "id": f"{mod_id}-01",
            "label": f"{label}通用",
            "phrases": phrases
        }
    ]
    return {
        "id": mod_id,
        "label": label,
        "icon": icon,
        "categories": categories
    }

def main():
    data = []
    for prefix, (mod_id, label, icon) in MODULE_MAP.items():
        module = build_module_from_files(prefix, mod_id, label, icon)
        if module:
            data.append(module)
            print(f"✓ 已处理 {label}: {len(module['categories'][0]['phrases'])} 个短语")

    # 生成 JavaScript 代码
    js_code = "// 自动生成的数据文件，请勿手动编辑\n"
    js_code += f"// 生成日期: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}\n"
    js_code += "const DEFAULT_DATA = "
    js_code += json.dumps(data, ensure_ascii=False, indent=2)
    js_code += ";\n"

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js_code)
    print(f"\n数据已生成: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()