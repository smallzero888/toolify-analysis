#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
重新格式化产品分析报告

此脚本读取现有的产品分析 Markdown 文件，并按照指定的模板重新格式化它们。
"""

import os
import re
import glob
import argparse
import traceback
from datetime import datetime

# 这些模板已经内置在代码中，不再需要单独定义

def extract_product_info(content):
    """从现有内容中提取产品信息"""
    info = {}

    # 提取产品名称
    name_match = re.search(r'^# (.+?)$', content, re.MULTILINE)
    if name_match:
        info['name'] = name_match.group(1).strip()

    # 尝试提取其他信息
    patterns = {
        'rank': r'排名:\s*(.+?)$',
        'revenue': r'收入:\s*(.+?)$',
        'product_link': r'产品链接:\s*(.+?)$',
        'analysis_link': r'分析链接:\s*(.+?)$',
        'monthly_visits': r'月访问量:\s*(.+?)$',
        'company': r'公司:\s*(.+?)$',
        'founded_date': r'成立日期:\s*(.+?)$',
        'pricing': r'定价:\s*(.+?)$',
        'platform': r'平台:\s*(.+?)$',
        'core_features': r'核心功能:\s*(.+?)$',
        'use_cases': r'应用场景:\s*(.+?)$',
        'analysis_time': r'分析时间:\s*(.+?)$',
        'analysis_tool': r'分析工具:\s*(.+?)$'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            info[key] = match.group(1).strip()

    return info

def extract_analysis_content(content):
    """从现有内容中提取分析内容"""
    # 创建一个字典来存储所有提取的内容
    extracted = {}

    # 提取产品分析框架部分
    framework_match = re.search(r'## 产品分析框架应用\s*\n(.*?)(?=##|\Z)', content, re.DOTALL)
    if framework_match:
        extracted['framework'] = framework_match.group(1).strip()
    else:
        # 尝试提取其他分析内容
        analysis_match = re.search(r'## 产品分析\s*\n(.*?)(?=##|\Z)', content, re.DOTALL)
        if analysis_match:
            extracted['framework'] = analysis_match.group(1).strip()
        else:
            extracted['framework'] = ""

    # 提取SWOT分析
    swot_match = re.search(r'## SWOT分析\s*\n(.*?)(?=##|\Z)', content, re.DOTALL)
    if swot_match:
        extracted['swot'] = swot_match.group(1).strip()
    else:
        extracted['swot'] = ""

    # 提取评分体系
    score_match = re.search(r'## 评分体系.*?\n(.*?)(?=##|\Z)', content, re.DOTALL)
    if score_match:
        extracted['score'] = score_match.group(1).strip()
    else:
        extracted['score'] = ""

    # 提取关键洞察与建议
    insights_match = re.search(r'## 关键洞察与建议\s*\n(.*?)(?=##|\Z)', content, re.DOTALL)
    if insights_match:
        extracted['insights'] = insights_match.group(1).strip()
    else:
        extracted['insights'] = ""

    # 提取总结部分（如果有）
    summary_match = re.search(r'## 总结\s*\n(.*?)(?=##|\Z)', content, re.DOTALL)
    if summary_match:
        extracted['summary'] = summary_match.group(1).strip()
    else:
        extracted['summary'] = ""

    # 提取产品描述（如果有）
    description_match = re.search(r'## 产品描述\s*\n(.*?)(?=##|\Z)', content, re.DOTALL)
    if description_match:
        extracted['description'] = description_match.group(1).strip()
    else:
        extracted['description'] = ""

    return extracted

def reformat_markdown(file_path):
    """重新格式化 Markdown 文件"""
    try:
        # 读取原始文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取产品信息
        product_info = extract_product_info(content)

        # 提取分析内容
        analysis_content = extract_analysis_content(content)

        # 构建新的 Markdown 内容
        new_content = f"# {product_info.get('name', 'Unknown Product')}\n\n"

        # 添加产品信息部分
        new_content += "## 产品信息\n\n"
        new_content += f"📊 排名: {product_info.get('rank', '')}\n\n"
        new_content += f"💰 收入: {product_info.get('revenue', '')}\n\n"
        new_content += f"🔗 产品链接: {product_info.get('product_link', '')}\n\n"
        new_content += f"🔍 分析链接: {product_info.get('analysis_link', '')}\n\n"
        new_content += f"👀 月访问量: {product_info.get('monthly_visits', '')}\n\n"
        new_content += f"🏢 公司: {product_info.get('company', '')}\n\n"
        new_content += f"🗓️ 成立日期: {product_info.get('founded_date', '')}\n\n"
        new_content += f"💲 定价: {product_info.get('pricing', '')}\n\n"
        new_content += f"📱 平台: {product_info.get('platform', '')}\n\n"
        new_content += f"🔧 核心功能: {product_info.get('core_features', '')}\n\n"
        new_content += f"🌐 应用场景: {product_info.get('use_cases', '')}\n\n"
        new_content += f"⏱️ 分析时间: {product_info.get('analysis_time', datetime.now().strftime('%Y年%m月%d日'))}\n\n"
        new_content += f"🤖 分析工具: {product_info.get('analysis_tool', 'DeepSeek AI')}\n\n"

        # 添加产品分析框架部分
        new_content += "## 产品分析框架\n\n"

        # 从原始内容中提取各个部分
        framework = analysis_content.get('framework', '')

        # 尝试从分析内容中提取问题答案
        problem_match = re.search(r'解决什么问题.*?(?:-|\n\n)', framework, re.DOTALL)
        problem = problem_match.group(0).strip() if problem_match else ""
        new_content += f"💡 这个产品解决的是什么问题？\n{problem}\n\n"

        users_match = re.search(r'目标用户.*?(?:-|\n\n)', framework, re.DOTALL)
        users = users_match.group(0).strip() if users_match else ""
        new_content += f"👤 用户是谁？\n{users}\n\n"

        needs_match = re.search(r'用户需求.*?(?:-|\n\n)', framework, re.DOTALL)
        needs = needs_match.group(0).strip() if needs_match else ""
        new_content += f"🤔 用户为什么需要它？\n{needs}\n\n"

        reviews_match = re.search(r'用户评价.*?(?:-|\n\n)', framework, re.DOTALL)
        reviews = reviews_match.group(0).strip() if reviews_match else ""
        new_content += f"🗣️ 用户是如何评价它的？\n{reviews}\n\n"

        acquisition_match = re.search(r'用户获取.*?(?:-|\n\n)', framework, re.DOTALL)
        acquisition = acquisition_match.group(0).strip() if acquisition_match else ""
        new_content += f"🔍 它是如何找到用户的？\n{acquisition}\n\n"

        business_match = re.search(r'商业模式.*?(?:-|\n\n)', framework, re.DOTALL)
        business = business_match.group(0).strip() if business_match else ""
        new_content += f"💰 它赚钱吗？多少？\n{business}\n\n"

        insights_match = re.search(r'产品洞察.*?(?:-|\n\n)', framework, re.DOTALL)
        insights = insights_match.group(0).strip() if insights_match else ""
        new_content += f"🧠 我从这个产品身上学到了什么？\n{insights}\n\n"

        challenges_match = re.search(r'实现挑战.*?(?:-|\n\n)', framework, re.DOTALL)
        challenges = challenges_match.group(0).strip() if challenges_match else ""
        new_content += f"🤔 它的什么做法不容易？\n{challenges}\n\n"

        pitch_match = re.search(r'一句话推销.*?(?:-|\n\n)', framework, re.DOTALL)
        pitch = pitch_match.group(0).strip() if pitch_match else ""
        new_content += f"🤗 一句话推销：\n{pitch}\n\n"

        diff_match = re.search(r'差异化方法.*?(?:-|\n\n)', framework, re.DOTALL)
        diff = diff_match.group(0).strip() if diff_match else ""
        new_content += f"💡 不同的方法：\n{diff}\n\n"

        feasibility_match = re.search(r'可行性分析.*?(?:-|\n\n)', framework, re.DOTALL)
        feasibility = feasibility_match.group(0).strip() if feasibility_match else ""
        new_content += f"🎉 我能做出来吗？\n{feasibility}\n\n"

        strategy_match = re.search(r'获客策略.*?(?:-|\n\n)', framework, re.DOTALL)
        strategy = strategy_match.group(0).strip() if strategy_match else ""
        new_content += f"🧭 如何找到用户？\n{strategy}\n\n"

        team_match = re.search(r'团队优势.*?(?:-|\n\n)', framework, re.DOTALL)
        team = team_match.group(0).strip() if team_match else ""
        new_content += f"🤔 为什么是我？\n{team}\n\n"

        persistence_match = re.search(r'持续性评估.*?(?:-|\n\n)', framework, re.DOTALL)
        persistence = persistence_match.group(0).strip() if persistence_match else ""
        new_content += f"❤️ 我能坚持吗？\n{persistence}\n\n"

        # 添加其他部分（如果有）
        if analysis_content.get('swot', ''):
            new_content += f"## SWOT分析\n\n{analysis_content['swot']}\n\n"

        if analysis_content.get('score', ''):
            new_content += f"## 评分体系\n\n{analysis_content['score']}\n\n"

        if analysis_content.get('insights', ''):
            new_content += f"## 关键洞察与建议\n\n{analysis_content['insights']}\n\n"

        if analysis_content.get('summary', ''):
            new_content += f"## 总结\n\n{analysis_content['summary']}\n\n"

        # 直接覆盖原始文件
        output_path = file_path

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"已重新格式化: {output_path}")
        return output_path

    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")
        traceback.print_exc()
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="重新格式化产品分析报告")
    parser.add_argument('-i', '--input', dest='input_path', required=True,
                        help='输入文件或目录路径')
    parser.add_argument('-r', '--recursive', dest='recursive',
                        action='store_true',
                        help='递归处理子目录')

    args = parser.parse_args()

    # 检查输入路径是否存在
    if not os.path.exists(args.input_path):
        print(f"错误: 输入路径不存在: {args.input_path}")
        return

    # 处理单个文件
    if os.path.isfile(args.input_path):
        if args.input_path.endswith('.md'):
            reformat_markdown(args.input_path)
        else:
            print(f"跳过非 Markdown 文件: {args.input_path}")

    # 处理目录
    elif os.path.isdir(args.input_path):
        # 确定搜索模式
        if args.recursive:
            search_pattern = os.path.join(args.input_path, '**', '*.md')
            md_files = glob.glob(search_pattern, recursive=True)
        else:
            search_pattern = os.path.join(args.input_path, '*.md')
            md_files = glob.glob(search_pattern)

        # 处理找到的所有 Markdown 文件
        if md_files:
            print(f"找到 {len(md_files)} 个 Markdown 文件")
            for file_path in md_files:
                reformat_markdown(file_path)
        else:
            print(f"在 {args.input_path} 中未找到 Markdown 文件")

if __name__ == "__main__":
    main()
