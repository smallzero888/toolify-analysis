#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
产品分析稳定性增强工具

此脚本用于增强产品分析的稳定性，主要功能包括：
1. 检查分析结果的完整性
2. 识别未完成或内容不完整的产品分析
3. 重新分析这些产品
4. 提供状态跟踪和报告

使用:
    python product_stability.py --check-completeness
    python product_stability.py --reanalyze-missing
"""

import os
import sys
import argparse
import json
import time
import traceback
from datetime import datetime
import pandas as pd
import glob
import re
import subprocess

# 最小有效文件大小（字节）
MIN_VALID_FILE_SIZE = 1000

def get_current_date_str():
    """获取当前日期字符串，格式为YYYYMMDD"""
    return datetime.now().strftime("%Y%m%d")

def find_analysis_directory(base_dir="output", date_str=None):
    """
    查找分析目录
    
    Args:
        base_dir (str): 基础目录
        date_str (str, optional): 日期字符串，如果不提供则使用当前日期
        
    Returns:
        str: 分析目录路径
    """
    if date_str is None:
        date_str = get_current_date_str()
    
    analysis_dir = os.path.join(base_dir, f"toolify_analysis_{date_str}")
    
    if not os.path.exists(analysis_dir):
        print(f"[ERROR] 分析目录不存在: {analysis_dir}")
        return None
    
    return analysis_dir

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

def check_analysis_completeness(language="cn", date_str=None, base_dir="output"):
    """
    检查分析结果的完整性
    
    Args:
        language (str): 语言，"cn"或"en"
        date_str (str, optional): 日期字符串，如果不提供则使用当前日期
        base_dir (str): 基础目录
        
    Returns:
        tuple: (完整性报告, 缺失的产品列表)
    """
    if date_str is None:
        date_str = get_current_date_str()
    
    # 查找分析目录
    analysis_dir = find_analysis_directory(base_dir, date_str)
    if not analysis_dir:
        return None, []
    
    # 查找数据文件
    data_file = find_data_file(base_dir, language, date_str)
    if not data_file:
        return None, []
    
    # 读取数据文件
    try:
        df = pd.read_excel(data_file)
        total_products = len(df)
        print(f"[INFO] 数据文件中共有 {total_products} 个产品")
    except Exception as e:
        print(f"[ERROR] 读取数据文件时出错: {str(e)}")
        return None, []
    
    # 查找markdown文件目录
    markdown_dir = os.path.join(analysis_dir, language, "markdown_files")
    if not os.path.exists(markdown_dir):
        print(f"[ERROR] Markdown目录不存在: {markdown_dir}")
        return None, []
    
    # 获取所有markdown文件
    markdown_files = glob.glob(os.path.join(markdown_dir, "*.md"))
    
    # 统计文件数量
    file_count = len(markdown_files)
    print(f"[INFO] 找到 {file_count} 个Markdown文件")
    
    # 检查文件大小
    small_files = []
    for file_path in markdown_files:
        file_size = os.path.getsize(file_path)
        if file_size < MIN_VALID_FILE_SIZE:
            small_files.append(os.path.basename(file_path))
    
    # 提取所有已分析的产品排名
    analyzed_ranks = set()
    for file_path in markdown_files:
        file_name = os.path.basename(file_path)
        # 使用正则表达式提取排名
        match = re.match(r'^(\d+)-', file_name)
        if match:
            rank = int(match.group(1))
            if os.path.getsize(file_path) >= MIN_VALID_FILE_SIZE:
                analyzed_ranks.add(rank)
    
    # 找出缺失的产品
    missing_ranks = []
    for i in range(1, total_products + 1):
        if i not in analyzed_ranks:
            missing_ranks.append(i)
    
    # 生成报告
    report = {
        "date": date_str,
        "language": language,
        "total_products": total_products,
        "analyzed_products": len(analyzed_ranks),
        "missing_products": len(missing_ranks),
        "small_files": len(small_files),
        "completion_percentage": round(len(analyzed_ranks) / total_products * 100, 2) if total_products > 0 else 0,
        "missing_ranks": missing_ranks,
        "small_files_list": small_files
    }
    
    return report, missing_ranks

def reanalyze_missing_products(missing_ranks, language="cn", date_str=None, base_dir="output", batch_size=5, use_gpu=True):
    """
    重新分析缺失的产品
    
    Args:
        missing_ranks (list): 缺失的产品排名列表
        language (str): 语言，"cn"或"en"
        date_str (str, optional): 日期字符串，如果不提供则使用当前日期
        base_dir (str): 基础目录
        batch_size (int): 批处理大小
        use_gpu (bool): 是否使用GPU
        
    Returns:
        bool: 是否成功
    """
    if not missing_ranks:
        print("[INFO] 没有缺失的产品需要重新分析")
        return True
    
    if date_str is None:
        date_str = get_current_date_str()
    
    # 查找数据文件
    data_file = find_data_file(base_dir, language, date_str)
    if not data_file:
        return False
    
    # 设置输出目录
    output_dir = os.path.join(base_dir, f"toolify_analysis_{date_str}", language)
    
    # 按批次处理缺失的产品
    success = True
    for i in range(0, len(missing_ranks), batch_size):
        batch = missing_ranks[i:i+batch_size]
        
        # 构建排名范围字符串
        if len(batch) == 1:
            rank_range = f"{batch[0]}-{batch[0]}"
        else:
            rank_range = f"{batch[0]}-{batch[-1]}"
        
        print(f"[INFO] 重新分析排名 {rank_range} 的产品 (批次 {i//batch_size + 1}/{(len(missing_ranks) + batch_size - 1)//batch_size})")
        
        # 构建命令
        cmd = [
            "python", "run_analysis.py",
            "--rank-range", rank_range,
            "--language", language,
            "--batch-size", str(min(batch_size, len(batch)))
        ]
        
        # 添加GPU标志
        if use_gpu:
            cmd.append("--gpu")
        
        # 执行命令
        try:
            print(f"[EXEC] 执行命令: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # 实时输出
            while True:
                if process.stdout is None:
                    break
                
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            # 获取返回码
            return_code = process.poll()
            
            if return_code == 0:
                print(f"[SUCCESS] 批次 {i//batch_size + 1} 分析完成")
            else:
                print(f"[ERROR] 批次 {i//batch_size + 1} 分析失败，返回码: {return_code}")
                success = False
                
                # 打印错误输出
                if process.stderr is not None:
                    stderr = process.stderr.read()
                    if stderr:
                        print(f"错误信息:\n{stderr}")
            
            # 等待一段时间，避免API限制
            time.sleep(2)
            
        except Exception as e:
            print(f"[ERROR] 执行命令时出错: {str(e)}")
            traceback.print_exc()
            success = False
    
    return success

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='产品分析稳定性增强工具')
    parser.add_argument('--check-completeness', action='store_true',
                        help='检查分析结果的完整性')
    parser.add_argument('--reanalyze-missing', action='store_true',
                        help='重新分析缺失的产品')
    parser.add_argument('--language', choices=['cn', 'en'], default='cn',
                        help='语言，"cn"或"en"')
    parser.add_argument('--date', type=str, default=None,
                        help='日期字符串，格式为YYYYMMDD，默认为当前日期')
    parser.add_argument('--base-dir', type=str, default='output',
                        help='基础目录')
    parser.add_argument('--batch-size', type=int, default=5,
                        help='批处理大小')
    parser.add_argument('--no-gpu', action='store_true',
                        help='不使用GPU')
    
    args = parser.parse_args()
    
    # 如果没有指定操作，显示帮助信息
    if not args.check_completeness and not args.reanalyze_missing:
        parser.print_help()
        return
    
    # 检查分析结果的完整性
    if args.check_completeness:
        print(f"[INFO] 检查{args.language.upper()}分析结果的完整性...")
        report, missing_ranks = check_analysis_completeness(
            language=args.language,
            date_str=args.date,
            base_dir=args.base_dir
        )
        
        if report:
            print("\n[REPORT] 完整性报告:")
            print(f"日期: {report['date']}")
            print(f"语言: {report['language'].upper()}")
            print(f"总产品数: {report['total_products']}")
            print(f"已分析产品数: {report['analyzed_products']}")
            print(f"缺失产品数: {report['missing_products']}")
            print(f"内容不完整文件数: {report['small_files']}")
            print(f"完成百分比: {report['completion_percentage']}%")
            
            if report['missing_products'] > 0:
                print(f"\n缺失的产品排名: {report['missing_ranks']}")
            
            if report['small_files'] > 0:
                print(f"\n内容不完整的文件: {report['small_files_list']}")
        else:
            print("[ERROR] 无法生成完整性报告")
    
    # 重新分析缺失的产品
    if args.reanalyze_missing:
        print(f"[INFO] 重新分析{args.language.upper()}缺失的产品...")
        
        # 先检查完整性
        report, missing_ranks = check_analysis_completeness(
            language=args.language,
            date_str=args.date,
            base_dir=args.base_dir
        )
        
        if not report:
            print("[ERROR] 无法检查完整性，无法重新分析")
            return
        
        # 合并缺失的产品和内容不完整的产品
        all_missing = missing_ranks.copy()
        
        # 从内容不完整的文件中提取排名
        for file_name in report['small_files_list']:
            match = re.match(r'^(\d+)-', file_name)
            if match:
                rank = int(match.group(1))
                if rank not in all_missing:
                    all_missing.append(rank)
        
        # 排序
        all_missing.sort()
        
        if not all_missing:
            print("[INFO] 没有缺失或内容不完整的产品需要重新分析")
            return
        
        print(f"[INFO] 需要重新分析的产品排名: {all_missing}")
        
        # 重新分析
        success = reanalyze_missing_products(
            all_missing,
            language=args.language,
            date_str=args.date,
            base_dir=args.base_dir,
            batch_size=args.batch_size,
            use_gpu=not args.no_gpu
        )
        
        if success:
            print("[SUCCESS] 所有缺失的产品已重新分析")
        else:
            print("[WARNING] 部分产品重新分析失败")
        
        # 再次检查完整性
        print("\n[INFO] 重新检查完整性...")
        new_report, new_missing = check_analysis_completeness(
            language=args.language,
            date_str=args.date,
            base_dir=args.base_dir
        )
        
        if new_report:
            print("\n[REPORT] 更新后的完整性报告:")
            print(f"完成百分比: {new_report['completion_percentage']}%")
            print(f"缺失产品数: {new_report['missing_products']}")
            
            if new_report['missing_products'] > 0:
                print(f"仍然缺失的产品排名: {new_report['missing_ranks']}")
                
                # 如果仍有缺失，建议再次运行
                print("\n[SUGGESTION] 仍有缺失的产品，建议再次运行此脚本进行重新分析")
            else:
                print("[SUCCESS] 所有产品已成功分析!")

if __name__ == "__main__":
    main()
