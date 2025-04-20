#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用OpenAI API分析剩余的产品榜单

此脚本用于使用OpenAI API分析剩余的产品榜单，主要功能包括：
1. 读取Excel文件中的产品数据
2. 使用OpenAI API生成分析内容
3. 保存分析结果到Markdown文件
"""

import os
import sys
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

# 获取OpenAI API密钥
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("错误: 未找到OpenAI API密钥，请确保.env文件中包含OPENAI_API_KEY")
    sys.exit(1)

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

def analyze_product_with_openai(product, api_key):
    """
    使用OpenAI API分析产品

    Args:
        product (dict): 产品数据
        api_key (str): OpenAI API密钥

    Returns:
        str: 分析内容
    """
    # 从产品数据中提取信息
    name = product.get("Tool Name") or product.get("工具名称", "未知")
    rank = product.get("Rank") or product.get("排名", "未知")
    revenue = product.get("Revenue") or product.get("收入", "未知")

    # 使用C列作为产品链接，D列作为产品网址
    tool_link = product.get("C") or product.get("工具链接", "未知")
    website = product.get("D") or product.get("网站", "未知")

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
            print(f"错误: OpenAI API调用失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"错误: 调用OpenAI API时出错: {str(e)}")
        return None

def main():
    """主函数"""
    # 设置日期字符串
    date_str = datetime.now().strftime("%Y%m%d")

    # 设置输入文件
    input_file = f"output/toolify_data/Toolify_Top_AI_Revenue_Rankings_CN_{date_str}.xlsx"

    # 设置输出目录
    output_dir = f"output/toolify_analysis_{date_str}/cn/markdown_files"
    os.makedirs(output_dir, exist_ok=True)

    # 读取数据文件
    try:
        df = pd.read_excel(input_file)
        products = df.to_dict('records')
        print(f"已加载 {len(products)} 个产品数据")
    except Exception as e:
        print(f"错误: 读取数据文件时出错: {str(e)}")
        sys.exit(1)

    # 检查哪些产品尚未被分析
    missing_ranks = []
    for rank in range(1, len(products) + 1):
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
            continue

        # 检查是否已经分析过
        product_name = product.get("Tool Name") or product.get("工具名称", "未知")
        safe_name = "".join([c if c.isalnum() else "_" for c in product_name.lower()])
        markdown_path = os.path.join(output_dir, f"{rank}-{safe_name}.md")

        if not os.path.exists(markdown_path) or os.path.getsize(markdown_path) < 1000:
            missing_ranks.append(rank)

    print(f"发现 {len(missing_ranks)} 个产品尚未被分析: {missing_ranks}")

    # 只分析460的产品
    ranks_to_analyze = [460]

    for rank in ranks_to_analyze:
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
            print(f"警告: 未找到排名为 {rank} 的产品")
            continue

        # 检查是否已经分析过
        product_name = product.get("Tool Name") or product.get("工具名称", "未知")
        safe_name = "".join([c if c.isalnum() else "_" for c in product_name.lower()])
        markdown_path = os.path.join(output_dir, f"{rank}-{safe_name}.md")

        if os.path.exists(markdown_path) and os.path.getsize(markdown_path) >= 1000:
            print(f"排名 {rank} 的产品已经分析过，跳过")
            continue

        print(f"正在分析排名 {rank} 的产品: {product_name}")

        # 使用OpenAI API分析产品
        markdown_content = analyze_product_with_openai(product, OPENAI_API_KEY)

        if markdown_content:
            # 保存分析结果
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"已保存分析结果到 {markdown_path}")
        else:
            print(f"分析排名 {rank} 的产品失败")

        # 等待一段时间，避免API限制
        time.sleep(2)

    print("分析完成")

if __name__ == "__main__":
    main()
