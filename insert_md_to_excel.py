#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
将已有的Markdown分析文件内容插入到Excel表格中

此脚本用于将已经生成的Markdown分析文件内容插入到对应的Excel表格中。
不需要重新分析产品，只需要读取已有的MD文件并更新Excel。
"""

import os
import sys
import re
import glob
import argparse
import pandas as pd
import traceback
from datetime import datetime

# 导入工具模块
try:
    from toolify_utils import update_excel_with_analysis
except ImportError as e:
    print(f"错误: 无法导入工具模块: {str(e)}")
    traceback.print_exc()
    sys.exit(1)


def insert_md_to_excel(excel_file=None, markdown_dir=None, date_str=None, language="cn"):
    """
    将Markdown文件内容插入到Excel表格中

    Args:
        excel_file (str, optional): Excel文件路径，如果不提供则自动查找
        markdown_dir (str, optional): Markdown文件目录，如果不提供则自动查找
        date_str (str, optional): 日期字符串，如果不提供则使用当前日期
        language (str): 语言，"cn"或"en"

    Returns:
        bool: 是否成功
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")

    # 如果没有提供Excel文件路径，尝试查找
    if excel_file is None:
        data_dir = os.path.join("output", "toolify_data")
        excel_file = os.path.join(data_dir, f"Toolify_Top_AI_Revenue_Rankings_{language.upper()}_{date_str}.xlsx")

        if not os.path.exists(excel_file):
            # 尝试查找其他可能的文件名
            alt_excel_file = os.path.join(data_dir, f"Toolify_AI_Revenue_{language.upper()}_{date_str}.xlsx")
            if os.path.exists(alt_excel_file):
                excel_file = alt_excel_file
            else:
                # 尝试查找任何匹配的Excel文件
                excel_files = glob.glob(os.path.join(data_dir, f"*{language.upper()}*{date_str}*.xlsx"))
                if excel_files:
                    excel_file = excel_files[0]
                else:
                    print(f"错误: 找不到Excel文件，请手动指定 --excel-file 参数")
                    return False

    # 如果没有提供Markdown目录，尝试查找
    if markdown_dir is None:
        markdown_dir = os.path.join("output", f"toolify_analysis_{date_str}", language, "markdown_files")
        if not os.path.exists(markdown_dir):
            print(f"错误: 找不到Markdown文件目录: {markdown_dir}")
            print("请手动指定 --markdown-dir 参数")
            return False

    # 检查文件和目录是否存在
    if not os.path.exists(excel_file):
        print(f"错误: Excel文件不存在: {excel_file}")
        return False

    if not os.path.exists(markdown_dir):
        print(f"错误: Markdown目录不存在: {markdown_dir}")
        return False

    # 读取Excel文件
    try:
        print(f"正在读取Excel文件: {excel_file}")
        tools = pd.read_excel(excel_file).to_dict('records')
        print(f"已加载 {len(tools)} 条产品数据")
    except Exception as e:
        print(f"错误: 无法读取Excel文件: {str(e)}")
        traceback.print_exc()
        return False

    # 获取所有Markdown文件
    md_files = glob.glob(os.path.join(markdown_dir, "*.md"))
    if not md_files:
        print(f"错误: 在 {markdown_dir} 中找不到任何Markdown文件")
        return False

    print(f"找到 {len(md_files)} 个Markdown文件")

    # 准备分析结果
    analysis_results = []
    for md_file in md_files:
        # 从文件名提取排名
        file_name = os.path.basename(md_file)
        rank_match = re.match(r'^(\d+)-', file_name)
        if not rank_match:
            print(f"警告: 无法从文件名提取排名: {file_name}")
            continue

        rank = int(rank_match.group(1))
        print(f"处理排名 {rank} 的产品: {file_name}")

        # 从原始数据中找到对应的产品
        product = None
        for p in tools:
            p_rank = p.get("Rank") or p.get("排名")
            try:
                p_rank = int(p_rank)
            except (ValueError, TypeError):
                continue

            if p_rank == rank:
                product = p
                break

        if not product:
            print(f"警告: 找不到排名为 {rank} 的产品数据")
            continue

        # 从文件内容中检测分析工具
        api_name = "DeepSeek AI"  # 默认值
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 检测是否包含OpenAI或GPT
                if "OpenAI" in content or "GPT" in content:
                    api_name = "OpenAI GPT-4"
                # 检测是否包含DeepSeek
                elif "DeepSeek" in content:
                    api_name = "DeepSeek AI"
                print(f"  检测到分析工具: {api_name}")
        except Exception as e:
            print(f"  警告: 无法读取文件内容: {str(e)}")

        # 添加到分析结果列表
        analysis_results.append({
            "product": product,
            "markdown_path": md_file,
            "api_name": api_name  # 添加分析工具信息
        })

    if not analysis_results:
        print("错误: 没有找到有效的分析结果")
        return False

    print(f"准备更新 {len(analysis_results)} 个产品的分析结果")

    # 更新Excel文件
    try:
        updated_file = update_excel_with_analysis(
            excel_file,
            analysis_results,
            markdown_dir=markdown_dir
        )

        if updated_file:
            print(f"成功更新Excel文件: {updated_file}")
            return True
        else:
            print("错误: 更新Excel文件失败")
            return False
    except Exception as e:
        print(f"错误: 更新Excel文件时出错: {str(e)}")
        traceback.print_exc()
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='将Markdown文件内容插入到Excel表格中')

    parser.add_argument('--excel-file', dest='excel_file',
                        help='Excel文件路径，如果不提供则自动查找')

    parser.add_argument('--markdown-dir', dest='markdown_dir',
                        help='Markdown文件目录，如果不提供则自动查找')

    parser.add_argument('--date', dest='date_str',
                        help='日期字符串，格式为YYYYMMDD，如果不提供则使用当前日期')

    parser.add_argument('--language', dest='language',
                        choices=['cn', 'en'], default='cn',
                        help='语言，"cn"或"en"，默认为"cn"')

    parser.add_argument('--rank-range', dest='rank_range',
                        help='只处理指定排名范围的产品，格式为"1-5"')

    args = parser.parse_args()

    # 如果指定了排名范围，需要过滤Markdown文件
    if args.rank_range:
        try:
            start_rank, end_rank = map(int, args.rank_range.split('-'))
            print(f"只处理排名 {start_rank} 到 {end_rank} 的产品")
        except ValueError:
            print("错误: 排名范围格式不正确，应为如'1-5'这样的格式")
            return False

    # 执行插入操作
    success = insert_md_to_excel(
        excel_file=args.excel_file,
        markdown_dir=args.markdown_dir,
        date_str=args.date_str,
        language=args.language
    )

    if success:
        print("✅ 所有操作完成!")
        return 0
    else:
        print("❌ 操作失败!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
