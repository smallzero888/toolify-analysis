#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Toolify AI产品分析工具

用于分析来自toolify.ai的产品数据，并生成全面的产品分析报告。
支持批量处理、并行处理以及GPU加速（如果可用）。

使用:
    python product_analyzer.py -i <input_file> -o <output_dir> -f <framework_file>
"""

import os
import pandas as pd
import numpy as np
import time
import json
import argparse
import sys
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Any, Union, Tuple, Optional
import traceback
from tqdm import tqdm
import re
import glob

# 导入工具模块
from toolify_utils import GPU_AVAILABLE, update_excel_with_analysis

# 全局变量初始化
DEEPSEEK_AVAILABLE = False
OPENAI_AVAILABLE = False
REQUESTS_AVAILABLE = False
requests = None  # 初始化requests变量

try:
    import requests as requests_module  # 重命名导入
    requests = requests_module  # 赋值给全局变量
    REQUESTS_AVAILABLE = True
    DEEPSEEK_AVAILABLE = True
    OPENAI_AVAILABLE = True
    print("[OK] API客户端依赖已成功导入")
except ImportError:
    print("[!] 请求库未安装，将跳过分析")

# 尝试导入dotenv库加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()  # 加载.env文件中的环境变量
    print("[OK] 环境变量已加载")
except ImportError:
    print("[!] dotenv库未安装，将使用系统环境变量")

# 尝试导入并发库
try:
    import concurrent.futures
    CONCURRENT_AVAILABLE = True
    print("[OK] 并发处理库已成功导入")
except ImportError:
    CONCURRENT_AVAILABLE = False
    print("[!] concurrent.futures库未安装，将使用顺序处理")

# 分析框架模板 - 为中英文创建单独的模板
# 从文件中加载模板
try:
    with open("analysis_framework.txt", "r", encoding="utf-8") as f:
        ANALYSIS_FRAMEWORK_CN = f.read()
    print("[INFO] 使用文件中的Markdown模板")
except Exception as e:
    print(f"[INFO] 无法读取模板文件，使用默认模板: {str(e)}")
    ANALYSIS_FRAMEWORK_CN = """
## 产品信息

📊 排名: 100

💰 收入: 估计$300-500万/年

🔗 产品链接: [domain.com](https://www.domain.com)

🔍 分析链接: [toolify.ai/tool/domain-com](https://www.toolify.ai/tool/domain-com)

👀 月访问量: 1.9M

🏢 公司: APEUni Education Technology

🗓️ 成立日期: 约2018年

💲 定价: 免费基础版 + 会员订阅(约$15-30/月)

📱 平台: 网页、移动网页

🔧 核心功能: PTE模拟测试、AI评分系统、备考资料库

🌐 应用场景: 留学语言考试备考、英语水平评估

⏱️ 分析时间: 2025年4月19日

🤖 分析工具: DeepSeek AI

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
| • 免费模式降低使用门槛 | • 品牌知名度低于官方合作伙伴 |
| • AI评分提供即时反馈 | • 评分算法透明度不足 |
| • 精准定位备考痛点 | • 缺乏官方认证背书 |
| • 高月访问量(1.9M) | • 商业模式不清晰 |

| 机会(Opportunities) | 威胁(Threats) |
|-------------------|------------|
| • 全球留学市场持续增长 | • 官方机构推出竞品 |
| • 亚洲考生群体扩大 | • 替代性考试(如Duolingo)兴起 |
| • AI技术提升评分准确度 | • 政策风险(考试改革) |
| • 拓展增值服务(课程/辅导) | • 用户获取成本上升 |

## 评分体系

创新性：7/10

商业模式可行性：6/10

增长潜力：8/10

总分：7/10

## 关键洞察与建议

可执行洞察：

1. 变现策略：
   - 推出阶梯式会员体系(如$9.99/月基础版，$29.99/月专业版)
   - 开发官方评分算法认证提升溢价能力

2. 产品优化：
   - 增加“评分偏差说明”提升透明度
   - 开发移动端APP提高用户粘性

3. 增长引擎：
   - 与留学中介建立B2B合作
   - 创建考生社区促进有机传播

经验教训：

- 教育类产品需平衡免费内容和付费墙设置
- 高流量不一定等同高转化，需明确用户旅程
- 考试准备产品特别依赖内容更新频率和准确性
- 第三方备考平台需要与官方保持适度合作关系

市场差异化建议：

- 开发“薄弱项追踪系统”提供个性化提升方案
- 引入真人教师+AI混合评分模式
- 建立考试成绩与院校录取的关联数据库
"""

# 使用中文模板作为英文模板的基础
try:
    # 尝试读取英文模板文件
    with open("analysis_framework_en.txt", "r", encoding="utf-8") as f:
        ANALYSIS_FRAMEWORK_EN = f.read()
    print("[INFO] 使用英文模板文件")
except Exception:
    # 如果没有英文模板文件，使用默认模板
    ANALYSIS_FRAMEWORK_EN = """
## Product Information

📊 Rank: 100

💰 Revenue: Estimated $3-5M/year

🔗 Product Link: [domain.com](https://www.domain.com)

🔍 Analysis Link: [toolify.ai/tool/domain-com](https://www.toolify.ai/tool/domain-com)

👀 Monthly Visits: 1.5M

🏢 Company: Company Name

🗓️ Founded Date: Around 2018

💲 Pricing: Free basic + Premium subscription ($15-30/month)

📱 Platform: Web, Mobile Web

🔧 Core Features: Core Feature 1, Core Feature 2, Core Feature 3

🌐 Use Cases: Use Case 1, Use Case 2

⏱️ Analysis Time: April 19, 2025

🤖 Analysis Tool: DeepSeek AI


## Product Analysis Framework

💡 What problem does this product solve?

👤 Who are the users?

🤔 Why do users need it?

🗣️ How do users review it?

🔍 How does it find users?

💰 Does it make money? How much?

🧠 What did I learn from this product?

🤔 What aspects of it are challenging?

🤗 One-line pitch:

💡 Different approaches:

🎉 Can I make it?

🧭 How to find users?

🤔 Why me?

❤️ Can I persist?

## SWOT Analysis

| Strengths | Weaknesses |
|-----------|------------|
| Strength 1 | Weakness 1 |
| Strength 2 | Weakness 2 |
| Strength 3 | Weakness 3 |

| Opportunities | Threats |
|--------------|--------|
| Opportunity 1 | Threat 1 |
| Opportunity 2 | Threat 2 |
| Opportunity 3 | Threat 3 |

## Rating System

Innovation: 8/10

Business Model Viability: 7/10

Growth Potential: 8/10

Total Score: 7.7/10

## Key Insights and Recommendations

Actionable Insights:
Here are actionable insights about the product.

Lessons Learned:
Here are lessons learned from the product.

Market Differentiation Suggestions:
Here are suggestions on how to differentiate in the market.
"""


class ProductAnalyzer:
    """产品分析器类，负责分析产品并生成报告"""

    def __init__(self, api="deepseek", api_key=None, api_url=None, timeout=120, use_gpu=False, language="cn", debug=False):
        """
        初始化产品分析器

        Args:
            api (str, optional): 使用的API，"deepseek"或"openai"
            api_key (str, optional): API密钥，如不提供则尝试从环境变量获取
            api_url (str, optional): API URL，如不提供则使用默认值
            timeout (int, optional): API请求超时时间（秒）
            use_gpu (bool, optional): 是否使用GPU加速
            language (str, optional): 语言，"cn"或"en"
            debug (bool, optional): 是否显示调试信息
        """
        self.timeout = timeout
        self.language = language.lower()
        self.debug = debug
        self.api = api.lower()

        # 确定API密钥和URL
        if self.api == "openai":
            self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
            self.api_url = api_url or os.environ.get("OPENAI_API_URL", "https://api.openai.com/v1")
            self.api_model = "gpt-4"
            self.api_name = "OpenAI GPT-4"

            # 检查API密钥和客户端
            if self.api_key and OPENAI_AVAILABLE:
                try:
                    self.client = True  # OpenAI使用requests库，这里仅标记客户端可用
                    print(f"[OK] 使用OpenAI API: {self.api_url}")
                except Exception as e:
                    self.client = None
                    print(f"[!] 初始化OpenAI客户端失败: {str(e)}")
            else:
                self.client = None
                if not self.api_key:
                    print("[!] 未提供OpenAI API密钥，将使用基本分析")
                elif not OPENAI_AVAILABLE:
                    print("[!] 请求库未安装，将使用基本分析")
        else:  # 默认使用DeepSeek
            self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
            self.api_url = api_url or os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/v1")
            self.api_model = "deepseek-chat"
            self.api_name = "DeepSeek AI"

            # 检查API密钥和客户端
            if self.api_key and DEEPSEEK_AVAILABLE:
                try:
                    self.client = True  # DeepSeek使用requests库，这里仅标记客户端可用
                    print(f"[OK] 使用DeepSeek API: {self.api_url}")
                except Exception as e:
                    self.client = None
                    print(f"[!] 初始化DeepSeek客户端失败: {str(e)}")
            else:
                self.client = None
                if not self.api_key:
                    print("[!] 未提供DeepSeek API密钥，将使用基本分析")
                elif not DEEPSEEK_AVAILABLE:
                    print("[!] 请求库未安装，将使用基本分析")

        # 设置计算设备
        self.use_gpu = use_gpu and GPU_AVAILABLE
        if self.use_gpu:
            print("[OK] 使用GPU加速模式")
        else:
            print("[INFO] 使用CPU模式")

        # 初始化统计信息，使用字典但确保可以接受float类型
        self.stats = {}
        self.stats["total_products"] = 0
        self.stats["successful_analyses"] = 0
        self.stats["failed_analyses"] = 0
        self.stats["total_time"] = 0.0
        self.stats["avg_time_per_product"] = 0.0

    def analyze_product(self, product):
        """分析单个产品"""
        start_time = time.time()

        try:
            # 从产品数据中提取信息
            name = product.get("Tool Name") or product.get("工具名称", "未知")
            rank = product.get("Rank") or product.get("排名", "未知")
            revenue = product.get("Revenue") or product.get("收入", "未知")

            # 使用C列作为产品链接，D列作为产品网址
            if self.language == "cn":
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

            # 选择模板
            template = ANALYSIS_FRAMEWORK_CN if self.language == "cn" else ANALYSIS_FRAMEWORK_EN

            # 替换模板中的占位符
            template = template.replace("{api_name}", self.api_name)

            # 填充产品信息
            if self.language == "cn":
                # 中文模板
                template = template.replace("📊 排名: 100", f"📊 排名: {rank}")
                template = template.replace("💰 收入: 估计$300-500万/年", f"💰 收入: {revenue}")

                # 处理产品链接和分析链接
                # 确保有一个有效的域名
                # 如果没有获取到链接信息，使用产品名称生成域名
                domain = name.lower().replace(' ', '').replace('-', '').replace('_', '') + '.com'

                # 替换产品链接
                template = template.replace("[domain.com](https://www.domain.com)", f"[{domain}](https://{domain})")

                # 生成分析链接
                safe_domain = domain.replace('.', '-')
                toolify_link = f"toolify.ai/tool/{safe_domain}"
                template = template.replace("[toolify.ai/tool/domain-com](https://www.toolify.ai/tool/domain-com)",
                                          f"[{toolify_link}](https://www.{toolify_link})")

                template = template.replace("👀 月访问量: 1.5M", f"👀 月访问量: {monthly_visits}")
                template = template.replace("🏢 公司: 公司名称", f"🏢 公司: {company}")
                template = template.replace("🗓️ 成立日期: 约2018年", f"🗓️ 成立日期: {founded_year}")
                template = template.replace("💲 定价: 免费基础版 + 会员订阅(约$15-30/月)", f"💲 定价: {pricing}")
                template = template.replace("📱 平台: 网页、移动网页", f"📱 平台: {'网页、移动网页' if website else '未知'}")
                template = template.replace("🔧 核心功能: 核心功能1、核心功能2、核心功能3", f"🔧 核心功能: {features}")
                template = template.replace("🌐 应用场景: 应用场景1、应用场景2", f"🌐 应用场景: {use_cases}")
                template = template.replace("⏱️ 分析时间: 2025年4月19日", f"⏱️ 分析时间: {datetime.now().strftime('%Y年%m月%d日')}")
                template = template.replace("🤖 分析工具: DeepSeek AI", f"🤖 分析工具: {self.api_name}")
            else:
                # 英文模板
                template = template.replace("📊 Rank: 100", f"📊 Rank: {rank}")
                template = template.replace("💰 Revenue: Estimated $3-5M/year", f"💰 Revenue: {revenue}")

                # 处理产品链接和分析链接
                # 确保有一个有效的域名
                # 如果没有获取到链接信息，使用产品名称生成域名
                domain = name.lower().replace(' ', '').replace('-', '').replace('_', '') + '.com'

                # 替换产品链接
                template = template.replace("[domain.com](https://www.domain.com)", f"[{domain}](https://{domain})")

                # 生成分析链接
                safe_domain = domain.replace('.', '-')
                toolify_link = f"toolify.ai/tool/{safe_domain}"
                template = template.replace("[toolify.ai/tool/domain-com](https://www.toolify.ai/tool/domain-com)",
                                          f"[{toolify_link}](https://www.{toolify_link})")

                template = template.replace("👀 Monthly Visits: 1.5M", f"👀 Monthly Visits: {monthly_visits}")
                template = template.replace("🏢 Company: Company Name", f"🏢 Company: {company}")
                template = template.replace("🗓️ Founded Date: Around 2018", f"🗓️ Founded Date: {founded_year}")
                template = template.replace("💲 Pricing: Free basic + Premium subscription ($15-30/month)", f"💲 Pricing: {pricing}")
                template = template.replace("📱 Platform: Web, Mobile Web", f"📱 Platform: {'Web, Mobile Web' if website else 'Unknown'}")
                template = template.replace("🔧 Core Features: Core Feature 1, Core Feature 2, Core Feature 3", f"🔧 Core Features: {features}")
                template = template.replace("🌐 Use Cases: Use Case 1, Use Case 2", f"🌐 Use Cases: {use_cases}")
                template = template.replace("⏱️ Analysis Time: April 19, 2025", f"⏱️ Analysis Time: {datetime.now().strftime('%B %d, %Y')}")
                template = template.replace("🤖 Analysis Tool: DeepSeek AI", f"🤖 Analysis Tool: {self.api_name}")

            # 准备调用API
            if self.client and self.api_key:
                try:
                    print(f"[API] 正在调用{self.api_name}分析产品: {name}...")

                    # 准备提示语
                    current_date = datetime.now().strftime('%Y年%m月%d日')
                    english_date = datetime.now().strftime('%B %d, %Y')

                    # 确保模板中的分析工具名称正确
                    if "🤖 分析工具: " in template:
                        template = re.sub(r'🤖 分析工具: [^\n]+', f'🤖 分析工具: {self.api_name}', template)
                    elif "🤖 Analysis Tool: " in template:
                        template = re.sub(r'🤖 Analysis Tool: [^\n]+', f'🤖 Analysis Tool: {self.api_name}', template)

                    prompt = f"""请对以下产品进行全面分析，并直接在模板中填充内容。不要改变模板的格式和结构。

产品名称: {name}
产品描述: {description}
产品链接: {website}

请注意以下要求：
1. 保留模板中的所有链接格式，如 [domain.com](https://www.domain.com)
2. 分析时间应为当前日期：{current_date} 或 {english_date}
3. 分析工具应为 {self.api_name}
4. 不要使用箭头符号（→），直接写出内容
5. 每个问题的回答应该简洁清晰，不要过于冗长
6. 在SWOT分析中填写具体的优势、劣势、机会和威胁
7. 在评分体系中给出具体的分数，如 8/10
8. 不要添加分隔线（---）或其他额外的格式元素
9. 不要在标题前添加加粗或其他格式，保持原样式
10. 不要在文本中添加星号（*）、双星号（**）、反引号（`）等特殊符号
11. 不要在文本行末添加空格或特殊符号
12. 不要使用加粗、斜体、下划线等格式，保持纯文本格式
13. 在产品分析框架部分，直接回答问题，不要添加“解决什么问题？**”、“目标用户：**”等额外的标记
14. 关键洞察与建议部分应该按照模板中的格式细分为可执行洞察、经验教训和市场差异化建议三部分
15. 必须保留模板中的所有部分，包括：产品信息、产品分析框架、SWOT分析、评分体系和关键洞察与建议
16. 不要删除或修改模板中的任何标题或结构

请在以下模板中直接填充内容，保持模板的格式不变：

# {name}

{template}
"""

                    # 调用API
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }

                    data = {
                        "model": self.api_model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 4000
                    }

                    response = requests.post(
                        f"{self.api_url}/chat/completions",
                        headers=headers,
                        json=data,
                        timeout=self.timeout
                    )

                    if response.status_code == 200:
                        result = response.json()
                        analysis_content = result["choices"][0]["message"]["content"]

                        # 提取分析内容
                        if "# " in analysis_content and "\n\n" in analysis_content:
                            # 分析内容包含标题，去除标题部分
                            # 处理多余的空行
                            analysis_content = re.sub(r'\n{3,}', '\n\n', analysis_content)
                            markdown_content = analysis_content
                        else:
                            # 如果没有标题，添加标题
                            analysis_content = re.sub(r'\n{3,}', '\n\n', analysis_content)
                            markdown_content = f"# {name}\n\n{analysis_content}"

                        print(f"[API] {self.api_name}分析完成")
                    else:
                        print(f"[ERROR] {self.api_name}调用失败: {response.status_code} - {response.text}")
                        # 使用默认模板
                        markdown_content = f"# {name}\n\n{template}"
                except Exception as api_error:
                    print(f"[ERROR] 调用{self.api_name}时出错: {str(api_error)}")
                    # 使用默认模板
                    markdown_content = f"# {name}\n\n{template}"
            else:
                # 如果没有API密钥或客户端，使用默认模板
                print(f"[INFO] 未配置{self.api_name}，使用默认模板")
                markdown_content = f"# {name}\n\n{template}"

            # 保存Markdown文件
            date_str = datetime.now().strftime("%Y%m%d")
            output_dir = os.path.join("output", f"toolify_analysis_{date_str}", self.language, "markdown_files")
            os.makedirs(output_dir, exist_ok=True)

            safe_name = "".join([c if c.isalnum() else "_" for c in name.lower()])
            markdown_path = os.path.join(output_dir, f"{rank}-{safe_name}.md")

            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"[OK] 已生成Markdown文件: {markdown_path}")

            return {
                "product": product,
                "markdown_path": markdown_path,
                "markdown_content": markdown_content,
                "elapsed_time": time.time() - start_time,
                "skipped": False
            }

        except Exception as e:
            print(f"[ERROR] 处理产品时出错: {str(e)}")
            traceback.print_exc()
            return {
                "product": product,
                "markdown_path": None,
                "elapsed_time": time.time() - start_time,
                "skipped": True
            }

    def analyze_batch_parallel(self, products, max_workers=5):
        """
        并行处理批量分析请求

        Args:
            products (list): 产品列表
            max_workers (int): 最大并行工作线程数

        Returns:
            list: 分析结果列表
        """
        results = []

        # 如果无法使用并发处理，回退到串行处理
        if not CONCURRENT_AVAILABLE:
            print("[!] 并发处理不可用，使用顺序处理")
            return [self.analyze_product(product) for product in products]

        print(f"[START] 启动并行处理，最大线程数: {max_workers}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_product = {executor.submit(self.analyze_product, product): product for product in products}

            # 使用tqdm创建进度条
            with tqdm(total=len(products), desc="分析进度") as pbar:
                for future in concurrent.futures.as_completed(future_to_product):
                    product = future_to_product[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        print(f"[ERROR] 处理产品时出错: {str(e)}")
                        traceback.print_exc()
                    finally:
                        pbar.update(1)

        return results

    def analyze_batch(self, products, batch_size=5, start_index=0, count=None):
        """
        批量分析产品

        Args:
            products (list): 产品列表
            batch_size (int): 每批次处理的产品数量
            start_index (int): 起始索引
            count (int, optional): 要处理的产品数量，None表示处理所有

        Returns:
            list: 分析结果列表
        """
        if not products:
            print("[!] 没有产品需要分析")
            return []

        # 确定要分析的范围
        total_products = len(products)
        if start_index >= total_products:
            print(f"[ERROR] 起始索引 {start_index} 超出产品总数 {total_products}")
            return []

        # 如果count为None，分析从start_index开始的所有产品
        if count is None:
            end_index = total_products
        else:
            end_index = min(start_index + count, total_products)

        products_to_analyze = products[start_index:end_index]
        count_to_analyze = len(products_to_analyze)

        print(f"[STATS] 准备分析产品: {count_to_analyze} 个 (从索引 {start_index} 到 {end_index-1})")

        # 批次处理
        all_results = []
        for i in range(0, count_to_analyze, batch_size):
            batch = products_to_analyze[i:i+batch_size]
            print(f"\n[BATCH] 处理批次 {i//batch_size + 1}/{(count_to_analyze + batch_size - 1)//batch_size}: {len(batch)} 个产品")

            # 使用GPU加速时启用并行处理
            if self.use_gpu:
                batch_results = self.analyze_batch_parallel(batch)
            else:
                # 顺序处理
                batch_results = [self.analyze_product(product) for product in batch]

            all_results.extend(batch_results)

        # 计算平均时间
        if self.stats["total_products"] > 0:
            self.stats["avg_time_per_product"] = self.stats["total_time"] / self.stats["total_products"]

        # 打印统计信息
        print("\n[STATS] 分析统计:")
        print(f"总产品数: {self.stats['total_products']}")
        print(f"成功分析: {self.stats['successful_analyses']}")
        print(f"失败分析: {self.stats['failed_analyses']}")
        print(f"总耗时: {self.stats['total_time']:.2f}秒")
        print(f"平均每产品耗时: {self.stats['avg_time_per_product']:.2f}秒")

        return all_results

    def save_results(self, results, output_dir="output/toolify_analysis", create_markdown=True):
        """
        保存分析结果

        Args:
            results (list): 分析结果列表
            output_dir (str): 输出目录
            create_markdown (bool): 是否创建Markdown文件

        Returns:
            list: 包含保存路径的结果列表
        """
        # 创建输出目录（转换为Windows风格的路径）
        windows_output_dir = output_dir.replace('/', '\\')
        os.makedirs(windows_output_dir, exist_ok=True)

        # 创建markdown子目录
        markdown_dir = os.path.join(windows_output_dir, "markdown_files")
        os.makedirs(markdown_dir, exist_ok=True)

        for result in results:
            # 如果分析被跳过，不创建文件
            if result.get("skipped", False) or not result.get("markdown_content"):
                continue

            product = result["product"]
            name = product.get("Tool Name") or product.get("工具名称", "unknown")

            # 获取产品排名 - 确保是整数
            try:
                rank = int(product.get("Rank") or product.get("排名", 0))
            except (ValueError, TypeError):
                rank = 0

            # 创建安全的文件名
            safe_name = "".join([c if c.isalnum() else "_" for c in name.lower()])

            # 添加markdown路径到结果
            if create_markdown:
                # 使用实际排名作为前缀
                markdown_path = os.path.join(markdown_dir, f"{rank}-{safe_name}.md")
                with open(markdown_path, 'w', encoding='utf-8') as f:
                    f.write(result["markdown_content"])
                result["markdown_path"] = markdown_path
                print(f"[FILE] 已保存Markdown文件: {markdown_path}")
            else:
                result["markdown_path"] = None

        return results


def main():
    """主函数，处理命令行参数并运行分析"""
    parser = argparse.ArgumentParser(description="Toolify AI产品分析工具")

    # 输入文件参数
    parser.add_argument('-i', '--input', dest='input_file',
                        help='输入的Excel文件路径')

    # 输出目录参数
    parser.add_argument('-o', '--output', dest='output_dir',
                        default='output/toolify_analysis',
                        help='输出目录')

    # 分析框架文件参数
    parser.add_argument('-f', '--framework', dest='framework_file',
                        default='analysis_framework.txt',
                        help='分析框架文件路径')

    # 批处理参数
    parser.add_argument('-b', '--batch-size', dest='batch_size',
                        type=int, default=5,
                        help='每批次处理的产品数量')

    # 起始索引
    parser.add_argument('-s', '--start', dest='start_index',
                        type=int, default=0,
                        help='起始产品索引（基于0）')

    # 产品数量
    parser.add_argument('-c', '--count', dest='count',
                        type=int, default=None,
                        help='要处理的产品数量，默认为全部')

    # API选择
    parser.add_argument('--api', dest='api',
                        choices=['deepseek', 'openai'], default='deepseek',
                        help='使用的API，默认为deepseek')

    # API密钥
    parser.add_argument('-k', '--api-key', dest='api_key',
                        help='API密钥')

    # API URL
    parser.add_argument('-u', '--api-url', dest='api_url',
                        help='API URL')

    # 显示API信息
    parser.add_argument('--show-api', dest='show_api',
                        action='store_true',
                        help='显示完整的API密钥和URL')

    # GPU选项
    parser.add_argument('-g', '--gpu', dest='use_gpu',
                        action='store_true',
                        help='启用GPU加速（如果可用）')

    # 语言选项
    parser.add_argument('-l', '--language', dest='language',
                        choices=['cn', 'en'], default='cn',
                        help='语言选择（cn或en）')

    # 调试选项
    parser.add_argument('-d', '--debug', dest='debug',
                        action='store_true',
                        help='显示调试信息')

    # 解析参数
    args = parser.parse_args()

    # 检查输入文件
    if not args.input_file:
        print("[ERROR] 未指定输入文件")
        parser.print_help()
        return

    if not os.path.exists(args.input_file):
        print(f"[ERROR] 输入文件不存在: {args.input_file}")
        return

    # 获取API密钥和URL
    api = args.api.lower()

    if api == "openai":
        api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
        api_url = args.api_url or os.environ.get("OPENAI_API_URL", "https://api.openai.com/v1")
        api_name = "OpenAI"
    else:  # 默认使用DeepSeek
        api_key = args.api_key or os.environ.get("DEEPSEEK_API_KEY")
        api_url = args.api_url or os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/v1")
        api_name = "DeepSeek"

    # 不显示API信息，只检查是否有API密钥
    if not api_key:
        print(f"[!] 未提供{api_name} API密钥，将使用基本分析")

    # 确保输出路径使用标准化的目录结构
    if not args.output_dir.startswith("output"):
        args.output_dir = f"output/{args.output_dir}"

    # 加载分析框架文件
    try:
        print(f"[SCAN] 正在分析Toolify数据...")

        # 读取Excel文件
        df = pd.read_excel(args.input_file)
        print(f"[OK] 已加载数据: {len(df)} 行")

        # 初始化分析器
        analyzer = ProductAnalyzer(
            api=api,
            api_key=api_key,
            api_url=api_url,
            use_gpu=args.use_gpu,
            language=args.language,
            debug=args.debug
        )

        # 将DataFrame转换为字典列表
        products = df.to_dict('records')

        # 确保每个产品都有有效的排名
        for i, product in enumerate(products):
            rank_field = "Rank" if "Rank" in product else "排名"
            if rank_field not in product or product[rank_field] is None or product[rank_field] == "":
                product[rank_field] = i + 1
            else:
                # 确保排名是整数
                try:
                    product[rank_field] = int(product[rank_field])
                except (ValueError, TypeError):
                    product[rank_field] = i + 1

        # 分析产品
        results = analyzer.analyze_batch(
            products,
            batch_size=args.batch_size,
            start_index=args.start_index,
            count=args.count
        )

        # 保存结果
        if results:
            saved_results = analyzer.save_results(results, args.output_dir)

            # 更新原始Excel文件
            # 确保使用正确的目录路径
            markdown_dir = os.path.join(args.output_dir, "markdown_files")

            # 调用更新函数
            updated_file = update_excel_with_analysis(
                args.input_file,
                saved_results,
                markdown_dir=markdown_dir
            )

            if updated_file:
                print(f"[OK] 已更新Excel文件: {updated_file}")

            print(f"\n[DONE] 所有分析已完成并保存到: {args.output_dir}")
        else:
            print("[!] 没有产生任何分析结果")

    except Exception as e:
        print(f"[ERROR] 程序执行出错: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
