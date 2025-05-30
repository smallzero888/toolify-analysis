#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
产品分析工具

此脚本用于分析产品榜单，支持使用DeepSeek和OpenAI两种API，默认使用DeepSeek。

使用方法:
    python analyze_product.py --rank 460 --api deepseek  # 使用DeepSeek分析排名460的产品
    python analyze_product.py --rank 460 --api openai    # 使用OpenAI分析排名460的产品
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
import requests
import glob
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API密钥
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

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

🤖 分析工具: {api_name}

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

# English analysis framework template
ANALYSIS_FRAMEWORK_EN = """
## Product Information

📊 Rank: {rank}

💰 Revenue: {revenue}

🔗 Product Link: [{domain}](https://{domain})

🔍 Analysis Link: [toolify.ai/tool/{safe_domain}](https://www.toolify.ai/tool/{safe_domain})

👀 Monthly Visits: {monthly_visits}

🏢 Company: {company}

🗓️ Founded: {founded_year}

💲 Pricing: {pricing}

📱 Platform: {platform}

🔧 Core Features: {features}

🌐 Use Cases: {use_cases}

⏱️ Analysis Date: {current_date}

🤖 Analysis Tool: {api_name}

## Product Analysis Framework

💡 What problem does this product solve?

👤 Who are the users?

🤔 Why do users need it?

🗣️ How do users review it?

🔍 How does it find users?

💰 Does it make money? How much?

🧠 What have I learned from this product?

🤔 What aspects of it are difficult to implement?

🤗 One-line pitch:

💡 Different approaches:

🎉 Can I build it?

🧭 How to find users?

🤔 Why me?

❤️ Can I persist?

## SWOT Analysis

| Strengths | Weaknesses |
|----------------|----------------|
| • Strength 1 | • Weakness 1 |
| • Strength 2 | • Weakness 2 |
| • Strength 3 | • Weakness 3 |

| Opportunities | Threats |
|-------------------|------------|
| • Opportunity 1 | • Threat 1 |
| • Opportunity 2 | • Threat 2 |
| • Opportunity 3 | • Threat 3 |

## Rating System

Innovation: 7/10

Business Model Viability: 6/10

Growth Potential: 8/10

Overall Score: 7/10

## Key Insights and Recommendations

Actionable Insights:

1. Insight 1
2. Insight 2
3. Insight 3

Lessons Learned:

- Lesson 1
- Lesson 2
- Lesson 3

Market Differentiation Recommendations:

- Recommendation 1
- Recommendation 2
- Recommendation 3
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

    # 尝试在多个可能的位置查找文件
    possible_locations = [
        # 标准位置
        os.path.join(base_dir, "toolify_data"),
        # 新位置
        os.path.join(base_dir, "toolify_data", f"toolify_analysis_{date_str}"),
        # 其他可能的位置
        os.path.join(base_dir),
        os.path.join(".", "output", "toolify_data"),
        os.path.join(".", "output", "toolify_data", f"toolify_analysis_{date_str}")
    ]

    # 尝试不同的文件名模式
    file_patterns = [
        f"*{language.upper()}*{date_str}*.xlsx",  # 精确匹配
        f"Toolify_AI_Revenue_{language.upper()}_{date_str}.xlsx",  # 标准命名
        f"Toolify_Top_AI_Revenue_Rankings_{language.upper()}_{date_str}.xlsx",  # 另一种命名
        f"*{language.upper()}*.xlsx"  # 模糊匹配
    ]

    # 在所有可能的位置和模式中查找
    for location in possible_locations:
        if not os.path.exists(location):
            continue

        print(f"[INFO] 在 {location} 中查找数据文件...")

        for pattern in file_patterns:
            matching_files = glob.glob(os.path.join(location, pattern))

            if matching_files:
                # 按修改时间排序，选择最新的文件
                matching_files.sort(key=os.path.getmtime, reverse=True)
                print(f"[INFO] 找到数据文件: {matching_files[0]}")
                return matching_files[0]

    # 如果还是找不到，尝试在当前目录下查找
    for pattern in file_patterns:
        matching_files = glob.glob(pattern)
        if matching_files:
            matching_files.sort(key=os.path.getmtime, reverse=True)
            print(f"[INFO] 在当前目录下找到数据文件: {matching_files[0]}")
            return matching_files[0]

    print(f"[ERROR] 未找到{language.upper()}数据文件")
    return None

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
    if not api_key:
        print("[ERROR] 未找到OpenAI API密钥，请设置环境变量OPENAI_API_KEY")
        return None

    # 从产品数据中提取信息
    name = product.get("Tool Name") or product.get("工具名称", "未知")
    rank = product.get("Rank") or product.get("Ranking") or product.get("排名", "未知")
    revenue = product.get("Revenue") or product.get("收入", "未知")

    # 获取网站链接
    website = product.get("Website") or product.get("D") or product.get("网站", "未知")
    # 获取工具链接
    tool_link = product.get("Tool Link") or product.get("C") or product.get("工具链接", "未知")

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
    current_date = datetime.now().strftime('%Y-%m-%d') if language == "en" else datetime.now().strftime('%Y年%m月%d日')
    platform = 'Web, Mobile Web' if language == "en" else '网页、移动网页' if website else '未知'

    # 选择模板
    template = ANALYSIS_FRAMEWORK_EN if language == "en" else ANALYSIS_FRAMEWORK_CN

    # 填充模板
    template = template.format(
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
        current_date=current_date,
        api_name="OpenAI GPT-4"
    )

    # 准备提示语
    if language == "en":
        prompt = f"""Please provide a comprehensive analysis of the following product, filling in the template directly. Do not change the format or structure of the template.

Product Name: {name}
Product Description: {description}
Product Link: {website}

Please note the following requirements:
1. Maintain all link formats in the template, such as [domain.com](https://www.domain.com)
2. The analysis date should be the current date: {current_date}
3. The analysis tool should be OpenAI GPT-4
4. Do not use arrow symbols (→), write out the content directly
5. Each answer should be concise and clear, not overly verbose
6. Fill in specific strengths, weaknesses, opportunities, and threats in the SWOT analysis
7. Provide specific scores in the rating system, such as 8/10
8. Do not add separators (---) or other additional formatting elements
9. Do not add bold or other formatting to headings, maintain the original style
10. Do not add asterisks (*), double asterisks (**), backticks (`), or other special symbols in the text
11. Do not add spaces or special symbols at the end of text lines
12. Do not use bold, italic, underline, or other formatting, maintain plain text format
13. In the Product Analysis Framework section, answer the questions directly without adding additional markers
14. The Key Insights and Recommendations section should be divided into Actionable Insights, Lessons Learned, and Market Differentiation Recommendations as per the template

Please fill in the content directly in the following template, maintaining the format unchanged:

{template}
"""
    else:
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
        print("[INFO] 正在调用OpenAI API...")
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

def analyze_product_with_deepseek(product, api_key, language="cn"):
    """
    使用DeepSeek API分析产品

    Args:
        product (dict): 产品数据
        api_key (str): DeepSeek API密钥
        language (str): 语言，"cn"或"en"

    Returns:
        str: 分析内容
    """
    if not api_key:
        print("[ERROR] 未找到DeepSeek API密钥，请设置环境变量DEEPSEEK_API_KEY")
        return None

    # 从产品数据中提取信息
    name = product.get("Tool Name") or product.get("工具名称", "未知")
    rank = product.get("Rank") or product.get("Ranking") or product.get("排名", "未知")
    revenue = product.get("Revenue") or product.get("收入", "未知")

    # 获取网站链接
    website = product.get("Website") or product.get("D") or product.get("网站", "未知")
    # 获取工具链接
    tool_link = product.get("Tool Link") or product.get("C") or product.get("工具链接", "未知")

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
    current_date = datetime.now().strftime('%Y-%m-%d') if language == "en" else datetime.now().strftime('%Y年%m月%d日')
    platform = 'Web, Mobile Web' if language == "en" else '网页、移动网页' if website else '未知'

    # 选择模板
    template = ANALYSIS_FRAMEWORK_EN if language == "en" else ANALYSIS_FRAMEWORK_CN

    # 填充模板
    template = template.format(
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
        current_date=current_date,
        api_name="DeepSeek AI"
    )

    # 准备提示语
    if language == "en":
        prompt = f"""Please provide a comprehensive analysis of the following product, filling in the template directly. Do not change the format or structure of the template.

Product Name: {name}
Product Description: {description}
Product Link: {website}

Please note the following requirements:
1. Maintain all link formats in the template, such as [domain.com](https://www.domain.com)
2. The analysis date should be the current date: {current_date}
3. The analysis tool should be DeepSeek AI
4. Do not use arrow symbols (→), write out the content directly
5. Each answer should be concise and clear, not overly verbose
6. Fill in specific strengths, weaknesses, opportunities, and threats in the SWOT analysis
7. Provide specific scores in the rating system, such as 8/10
8. Do not add separators (---) or other additional formatting elements
9. Do not add bold or other formatting to headings, maintain the original style
10. Do not add asterisks (*), double asterisks (**), backticks (`), or other special symbols in the text
11. Do not add spaces or special symbols at the end of text lines
12. Do not use bold, italic, underline, or other formatting, maintain plain text format
13. In the Product Analysis Framework section, answer the questions directly without adding additional markers
14. The Key Insights and Recommendations section should be divided into Actionable Insights, Lessons Learned, and Market Differentiation Recommendations as per the template

Please fill in the content directly in the following template, maintaining the format unchanged:

{template}
"""
    else:
        prompt = f"""请对以下产品进行全面分析，并直接在模板中填充内容。不要改变模板的格式和结构。

产品名称: {name}
产品描述: {description}
产品链接: {website}

请注意以下要求：
1. 保留模板中的所有链接格式，如 [domain.com](https://www.domain.com)
2. 分析时间应为当前日期：{current_date}
3. 分析工具应为 DeepSeek AI
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

    # 调用DeepSeek API
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }

    try:
        print("[INFO] 正在调用DeepSeek API...")
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
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
            print(f"[ERROR] DeepSeek API调用失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] 调用DeepSeek API时出错: {str(e)}")
        return None

def analyze_product(rank, api="deepseek", language="cn", date_str=None, base_dir="output"):
    """
    分析指定排名的产品

    Args:
        rank (int): 产品排名
        api (str): 使用的API，"deepseek"或"openai"
        language (str): 语言，"cn"或"en"
        date_str (str, optional): 日期字符串，如果不提供则使用当前日期
        base_dir (str): 基础目录

    Returns:
        bool: 是否成功
    """
    if date_str is None:
        date_str = get_current_date_str()

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

    # 查找对应排名的产品
    product = None
    for p in products:
        p_rank = p.get("Rank") or p.get("Ranking") or p.get("排名")
        try:
            p_rank = int(p_rank)
        except (ValueError, TypeError):
            continue

        if p_rank == rank:
            product = p
            break

    if not product:
        print(f"[ERROR] 未找到排名为 {rank} 的产品")
        return False

    # 设置输出目录
    output_dir = os.path.join(base_dir, f"toolify_analysis_{date_str}", language, "markdown_files")
    os.makedirs(output_dir, exist_ok=True)

    # 获取产品名称
    product_name = product.get("Tool Name") or product.get("工具名称", "未知")
    safe_name = "".join([c if c.isalnum() else "_" for c in product_name.lower()])
    markdown_path = os.path.join(output_dir, f"{rank}-{safe_name}.md")

    print(f"[INFO] 正在分析排名 {rank} 的产品: {product_name}")

    # 根据选择的API分析产品
    if api.lower() == "openai":
        markdown_content = analyze_product_with_openai(product, OPENAI_API_KEY, language)
    else:  # 默认使用DeepSeek
        markdown_content = analyze_product_with_deepseek(product, DEEPSEEK_API_KEY, language)

    if markdown_content:
        # 保存分析结果
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"[SUCCESS] 已保存分析结果到 {markdown_path}")
        return True
    else:
        print(f"[ERROR] 分析排名 {rank} 的产品失败")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='产品分析工具')
    parser.add_argument('--rank', type=int, required=True,
                        help='产品排名')
    parser.add_argument('--api', choices=['deepseek', 'openai'], default='deepseek',
                        help='使用的API，默认为deepseek')
    parser.add_argument('--language', choices=['cn', 'en'], default='cn',
                        help='语言，"cn"或"en"')
    parser.add_argument('--date', type=str, default=None,
                        help='日期字符串，格式为YYYYMMDD，默认为当前日期')
    parser.add_argument('--base-dir', type=str, default='output',
                        help='基础目录')

    args = parser.parse_args()

    # 分析产品
    success = analyze_product(
        args.rank,
        api=args.api,
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
