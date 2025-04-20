#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用OpenAI API分析剩余的产品榜单

此脚本用于使用OpenAI API分析剩余的产品榜单，主要功能包括：
1. 读取Excel文件中的产品数据
2. 检查哪些产品尚未被分析
3. 使用OpenAI API生成分析内容
4. 保存分析结果到Markdown文件

使用:
    python analyze_remaining_with_openai.py --rank-range 503-507
"""

import os
import sys
import argparse
import pandas as pd
import time
import json
import traceback
from datetime import datetime
import re
import glob
import requests
from tqdm import tqdm

# 分析框架模板
ANALYSIS_FRAMEWORK_CN = """
## 产品信息

📊 排名: {rank}

💰 收入: {revenue}

🔗 产品链接: [{domain}](https://{domain})

🔍 分析链接: [toolify.ai/tool/{safe_domain}](https://www.toolify.ai/tool/{safe_domain})

👀 月访问量: {monthly_visits}

🏢 公司: {company}

🗓️ 成立日期: {founded_year}

💲 定价: {pricing}

📱 平台: {platform}

🔧 核心功能: {features}

🌐 应用场景: {use_cases}

⏱️ 分析时间: {current_date}

🤖 分析工具: OpenAI GPT-4

## 产品分析框架

💡 这个产品解决的是什么问题？

👤 用户是谁？

🤔 用户为什么需要它？

🗣️ 用户是如何评价它的？

🔍 它是如何找到用户的？

💰 它赚钱吗？多少？

🧠 我从这个产品身上学到了什么？

🤔 它的什么做法不容易？

🤗 一句话推销：

💡 不同的方法：

🎉 我能做出来吗？

🧭 如何找到用户？

🤔 为什么是我？

❤️ 我能坚持吗？

## SWOT分析

| 优势(Strengths) | 劣势(Weaknesses) |
|----------------|----------------|
| • 优势1 | • 劣势1 |
| • 优势2 | • 劣势2 |
| • 优势3 | • 劣势3 |

| 机会(Opportunities) | 威胁(Threats) |
|-------------------|------------|
| • 机会1 | • 威胁1 |
| • 机会2 | • 威胁2 |
| • 机会3 | • 威胁3 |

## 评分体系

创新性：7/10

商业模式可行性：6/10

增长潜力：8/10

总分：7/10

## 关键洞察与建议

可执行洞察：

1. 洞察1
2. 洞察2
3. 洞察3

经验教训：

- 教训1
- 教训2
- 教训3

市场差异化建议：

- 建议1
- 建议2
- 建议3
"""

def get_current_date_str():
    """获取当前日期字符串，格式为YYYYMMDD"""
    return datetime.now().strftime("%Y%m%d")

def find_data_file(base_dir="output", language="cn", date_str=None):
    """
    查找数据文件
    
    Args:
        base_dir (str): 基础目录
        language (str): 语言，"cn"或"en"
        date_str (str, optional): 日期字符串，如果不提供则使用当前日期
        
    Returns:
        str: 数据文件路径
    """
    if date_str is None:
        date_str = get_current_date_str()
    
    data_dir = os.path.join(base_dir, "toolify_data")
    
    # 尝试查找精确匹配的文件
    file_pattern = f"*{language.upper()}*{date_str}*.xlsx"
    matching_files = glob.glob(os.path.join(data_dir, file_pattern))
    
    if matching_files:
        return matching_files[0]
    
    # 如果没有找到精确匹配，尝试查找最新的文件
    file_pattern = f"*{language.upper()}*.xlsx"
    matching_files = glob.glob(os.path.join(data_dir, file_pattern))
    
    if matching_files:
        # 按修改时间排序
        matching_files.sort(key=os.path.getmtime, reverse=True)
        return matching_files[0]
    
    print(f"[ERROR] 未找到{language.upper()}数据文件")
    return None

def get_missing_ranks(language="cn", date_str=None, base_dir="output"):
    """
    获取缺失的产品排名
    
    Args:
        language (str): 语言，"cn"或"en"
        date_str (str, optional): 日期字符串，如果不提供则使用当前日期
        base_dir (str): 基础目录
        
    Returns:
        list: 缺失的产品排名列表
    """
    if date_str is None:
        date_str = get_current_date_str()
    
    # 查找数据文件
    data_file = find_data_file(base_dir, language, date_str)
    if not data_file:
        return []
    
    # 读取数据文件
    try:
        df = pd.read_excel(data_file)
        total_products = len(df)
        print(f"[INFO] 数据文件中共有 {total_products} 个产品")
    except Exception as e:
        print(f"[ERROR] 读取数据文件时出错: {str(e)}")
        return []
    
    # 查找markdown文件目录
    analysis_dir = os.path.join(base_dir, f"toolify_analysis_{date_str}")
    markdown_dir = os.path.join(analysis_dir, language, "markdown_files")
    if not os.path.exists(markdown_dir):
        print(f"[ERROR] Markdown目录不存在: {markdown_dir}")
        return list(range(1, total_products + 1))  # 如果目录不存在，返回所有排名
    
    # 获取所有markdown文件
    markdown_files = glob.glob(os.path.join(markdown_dir, "*.md"))
    
    # 提取所有已分析的产品排名
    analyzed_ranks = set()
    for file_path in markdown_files:
        file_name = os.path.basename(file_path)
        # 使用正则表达式提取排名
        match = re.match(r'^(\d+)-', file_name)
        if match:
            rank = int(match.group(1))
            if os.path.getsize(file_path) >= 1000:  # 确保文件大小足够
                analyzed_ranks.add(rank)
    
    # 找出缺失的产品
    missing_ranks = []
    for i in range(1, total_products + 1):
        if i not in analyzed_ranks:
            missing_ranks.append(i)
    
    return missing_ranks

def analyze_product_with_openai(product, api_key, language="cn"):
    """
    使用OpenAI API分析产品
    
    Args:
        product (dict): 产品数据
        api_key (str): OpenAI API密钥
        language (str): 语言，"cn"或"en"
        
    Returns:
        str: 分析内容
    """
    # 从产品数据中提取信息
    name = product.get("Tool Name") or product.get("工具名称", "未知")
    rank = product.get("Rank") or product.get("排名", "未知")
    revenue = product.get("Revenue") or product.get("收入", "未知")
    
    # 使用C列作为产品链接，D列作为产品网址
    if language == "cn":
        # 中文表格
        tool_link = product.get("C") or product.get("工具链接", "未知")
        website = product.get("D") or product.get("网站", "未知")
    else:
        # 英文表格
        tool_link = product.get("C") or product.get("Tool Link", "未知")
        website = product.get("D") or product.get("Website", "未知")
    
    monthly_visits = product.get("Monthly Visits") or product.get("月访问量", "未知")
    company = product.get("Company") or product.get("公司", "未知")
    founded_year = product.get("Founded Year") or product.get("成立年份", "未知")
    pricing = product.get("Payment Platform") or product.get("定价", "未知")
    features = product.get("Features") or product.get("功能特性", "未知")
    use_cases = product.get("Use Cases") or product.get("应用场景", "未知")
    description = product.get("Description") or product.get("描述", "未知")
    
    # 确保有一个有效的域名
    # 如果没有获取到链接信息，使用产品名称生成域名
    domain = name.lower().replace(' ', '').replace('-', '').replace('_', '') + '.com'
    safe_domain = domain.replace('.', '-')
    
    # 准备模板数据
    current_date = datetime.now().strftime('%Y年%m月%d日')
    platform = '网页、移动网页' if website else '未知'
    
    # 填充模板
    template = ANALYSIS_FRAMEWORK_CN.format(
        rank=rank,
        revenue=revenue,
        domain=domain,
        safe_domain=safe_domain,
        monthly_visits=monthly_visits,
        company=company,
        founded_year=founded_year,
        pricing=pricing,
        platform=platform,
        features=features,
        use_cases=use_cases,
        current_date=current_date
    )
    
    # 准备提示语
    prompt = f"""请对以下产品进行全面分析，并直接在模板中填充内容。不要改变模板的格式和结构。

产品名称: {name}
产品描述: {description}
产品链接: {website}

请注意以下要求：
1. 保留模板中的所有链接格式，如 [domain.com](https://www.domain.com)
2. 分析时间应为当前日期：{current_date}
3. 分析工具应为 OpenAI GPT-4
4. 不要使用箭头符号（→），直接写出内容
5. 每个问题的回答应该简洁清晰，不要过于冗长
6. 在SWOT分析中填写具体的优势、劣势、机会和威胁
7. 在评分体系中给出具体的分数，如 8/10
8. 不要添加分隔线（---）或其他额外的格式元素
9. 不要在标题前添加加粗或其他格式，保持原样式
10. 不要在文本中添加星号（*）、双星号（**）、反引号（`）等特殊符号
11. 不要在文本行末添加空格或特殊符号
12. 不要使用加粗、斜体、下划线等格式，保持纯文本格式
13. 在产品分析框架部分，直接回答问题，不要添加"解决什么问题？**"、"目标用户：**"等额外的标记
14. 关键洞察与建议部分应该按照模板中的格式细分为可执行洞察、经验教训和市场差异化建议三部分

请在以下模板中直接填充内容，保持模板的格式不变：

{template}
"""
    
    # 调用OpenAI API
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis_content = result["choices"][0]["message"]["content"]
            
            # 处理多余的空行
            analysis_content = re.sub(r'\n{3,}', '\n\n', analysis_content)
            
            # 添加标题
            markdown_content = f"# {name}\n\n{analysis_content}"
            
            return markdown_content
        else:
            print(f"[ERROR] OpenAI API调用失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] 调用OpenAI API时出错: {str(e)}")
        return None

def analyze_ranks(rank_range, language="cn", date_str=None, base_dir="output"):
    """
    分析指定排名范围的产品
    
    Args:
        rank_range (str): 排名范围，如"1-5"
        language (str): 语言，"cn"或"en"
        date_str (str, optional): 日期字符串，如果不提供则使用当前日期
        base_dir (str): 基础目录
        
    Returns:
        bool: 是否成功
    """
    if date_str is None:
        date_str = get_current_date_str()
    
    # 检查排名范围格式
    if "-" not in rank_range:
        print("错误: 排名范围格式不正确，应为如'1-5'这样的格式")
        return False
    
    # 解析排名范围
    try:
        start_rank, end_rank = map(int, rank_range.split("-"))
    except ValueError:
        print("错误: 排名必须是数字")
        return False
    
    if start_rank <= 0 or end_rank <= 0:
        print("错误: 排名必须大于0")
        return False
    
    if start_rank > end_rank:
        print("错误: 起始排名不能大于结束排名")
        return False
    
    # 查找数据文件
    data_file = find_data_file(base_dir, language, date_str)
    if not data_file:
        return False
    
    # 读取数据文件
    try:
        df = pd.read_excel(data_file)
        products = df.to_dict('records')
        print(f"[INFO] 已加载 {len(products)} 个产品数据")
    except Exception as e:
        print(f"[ERROR] 读取数据文件时出错: {str(e)}")
        return False
    
    # 获取OpenAI API密钥
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] 未找到OpenAI API密钥，请设置环境变量OPENAI_API_KEY")
        return False
    
    # 设置输出目录
    output_dir = os.path.join(base_dir, f"toolify_analysis_{date_str}", language, "markdown_files")
    os.makedirs(output_dir, exist_ok=True)
    
    # 分析产品
    success_count = 0
    for rank in range(start_rank, end_rank + 1):
        # 查找对应排名的产品
        product = None
        for p in products:
            p_rank = p.get("Rank") or p.get("排名")
            try:
                p_rank = int(p_rank)
            except (ValueError, TypeError):
                continue
            
            if p_rank == rank:
                product = p
                break
        
        if not product:
            print(f"[WARNING] 未找到排名为 {rank} 的产品")
            continue
        
        # 检查是否已经分析过
        product_name = product.get("Tool Name") or product.get("工具名称", "未知")
        safe_name = "".join([c if c.isalnum() else "_" for c in product_name.lower()])
        markdown_path = os.path.join(output_dir, f"{rank}-{safe_name}.md")
        
        if os.path.exists(markdown_path) and os.path.getsize(markdown_path) >= 1000:
            print(f"[INFO] 排名 {rank} 的产品已经分析过，跳过")
            success_count += 1
            continue
        
        print(f"[INFO] 正在分析排名 {rank} 的产品: {product_name}")
        
        # 使用OpenAI API分析产品
        markdown_content = analyze_product_with_openai(product, api_key, language)
        
        if markdown_content:
            # 保存分析结果
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"[SUCCESS] 已保存分析结果到 {markdown_path}")
            success_count += 1
        else:
            print(f"[ERROR] 分析排名 {rank} 的产品失败")
        
        # 等待一段时间，避免API限制
        time.sleep(2)
    
    print(f"[INFO] 分析完成，成功分析 {success_count}/{end_rank - start_rank + 1} 个产品")
    
    return success_count > 0

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='使用OpenAI API分析剩余的产品榜单')
    parser.add_argument('--rank-range', type=str, required=True,
                        help='排名范围，如"1-5"')
    parser.add_argument('--language', choices=['cn', 'en'], default='cn',
                        help='语言，"cn"或"en"')
    parser.add_argument('--date', type=str, default=None,
                        help='日期字符串，格式为YYYYMMDD，默认为当前日期')
    parser.add_argument('--base-dir', type=str, default='output',
                        help='基础目录')
    
    args = parser.parse_args()
    
    # 分析指定排名范围的产品
    success = analyze_ranks(
        args.rank_range,
        language=args.language,
        date_str=args.date,
        base_dir=args.base_dir
    )
    
    if success:
        print("[SUCCESS] 分析完成")
    else:
        print("[ERROR] 分析失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
