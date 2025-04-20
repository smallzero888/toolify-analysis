#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查Markdown文件的完整性

此脚本用于检查Markdown文件的完整性，主要功能包括：
1. 检查文件大小
2. 检查文件内容是否包含必要的部分
"""

import os
import sys
import glob
import pandas as pd

# 最小有效文件大小（字节）
MIN_VALID_FILE_SIZE = 1000

def main():
    """主函数"""
    # 设置日期字符串
    date_str = "20250420"
    
    # 设置输入文件
    input_file = f"output/toolify_data/Toolify_Top_AI_Revenue_Rankings_CN_{date_str}.xlsx"
    
    # 设置输出目录
    output_dir = f"output/toolify_analysis_{date_str}/cn/markdown_files"
    
    # 读取数据文件
    try:
        df = pd.read_excel(input_file)
        total_products = len(df)
        print(f"数据文件中共有 {total_products} 个产品")
    except Exception as e:
        print(f"读取数据文件时出错: {str(e)}")
        sys.exit(1)
    
    # 获取所有markdown文件
    markdown_files = glob.glob(os.path.join(output_dir, "*.md"))
    print(f"找到 {len(markdown_files)} 个Markdown文件")
    
    # 检查文件大小
    small_files = []
    for file_path in markdown_files:
        file_size = os.path.getsize(file_path)
        if file_size < MIN_VALID_FILE_SIZE:
            small_files.append((os.path.basename(file_path), file_size))
    
    if small_files:
        print(f"\n发现 {len(small_files)} 个文件大小小于 {MIN_VALID_FILE_SIZE} 字节:")
        for file_name, file_size in small_files:
            print(f"  {file_name}: {file_size} 字节")
    else:
        print(f"\n所有文件大小均大于 {MIN_VALID_FILE_SIZE} 字节")
    
    # 检查文件内容
    incomplete_files = []
    for file_path in markdown_files:
        if os.path.getsize(file_path) >= MIN_VALID_FILE_SIZE:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # 检查是否包含必要的部分
                    if "## 产品信息" not in content:
                        incomplete_files.append((os.path.basename(file_path), "缺少产品信息部分"))
                    elif "## 产品分析框架" not in content:
                        incomplete_files.append((os.path.basename(file_path), "缺少产品分析框架部分"))
                    elif "## SWOT分析" not in content:
                        incomplete_files.append((os.path.basename(file_path), "缺少SWOT分析部分"))
                    elif "## 评分体系" not in content:
                        incomplete_files.append((os.path.basename(file_path), "缺少评分体系部分"))
                    elif "## 关键洞察与建议" not in content:
                        incomplete_files.append((os.path.basename(file_path), "缺少关键洞察与建议部分"))
            except Exception as e:
                incomplete_files.append((os.path.basename(file_path), f"读取文件时出错: {str(e)}"))
    
    if incomplete_files:
        print(f"\n发现 {len(incomplete_files)} 个内容不完整的文件:")
        for file_name, reason in incomplete_files:
            print(f"  {file_name}: {reason}")
    else:
        print("\n所有文件内容均完整")
    
    # 提取所有已分析的产品排名
    analyzed_ranks = set()
    for file_path in markdown_files:
        file_name = os.path.basename(file_path)
        # 使用文件名提取排名
        try:
            rank = int(file_name.split('-')[0])
            if os.path.getsize(file_path) >= MIN_VALID_FILE_SIZE:
                analyzed_ranks.add(rank)
        except (ValueError, IndexError):
            pass
    
    # 找出缺失的产品
    missing_ranks = []
    for i in range(1, total_products + 1):
        if i not in analyzed_ranks:
            missing_ranks.append(i)
    
    if missing_ranks:
        print(f"\n发现 {len(missing_ranks)} 个产品尚未被分析:")
        print(f"  {missing_ranks}")
    else:
        print("\n所有产品均已被分析")
    
    # 统计完成率
    completion_rate = len(analyzed_ranks) / total_products * 100
    print(f"\n完成率: {completion_rate:.2f}%")

if __name__ == "__main__":
    main()
