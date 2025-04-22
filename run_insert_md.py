#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import traceback
from datetime import datetime
from insert_md_to_excel import insert_md_to_excel

def main():
    try:
        # 获取当前日期
        date_str = datetime.now().strftime("%Y%m%d")
        
        # 设置默认路径
        excel_file = os.path.join("output", "toolify_data", f"Toolify_AI_Revenue_CN_{date_str}.xlsx")
        markdown_dir = os.path.join("output", f"toolify_analysis_{date_str}", "cn", "markdown_files")
        
        print("\n=== 环境检查 ===")
        print(f"当前工作目录: {os.getcwd()}")
        print(f"Excel文件路径: {excel_file}")
        print(f"Markdown目录: {markdown_dir}")
        
        # 检查文件和目录是否存在
        if not os.path.exists(excel_file):
            # 尝试查找其他可能的文件名
            alt_excel_file = os.path.join("output", "toolify_data", f"Toolify_Top_AI_Revenue_Rankings_CN_{date_str}.xlsx")
            if os.path.exists(alt_excel_file):
                excel_file = alt_excel_file
                print(f"找到替代Excel文件: {excel_file}")
            else:
                print(f"错误: Excel文件不存在: {excel_file}")
                print(f"替代文件也不存在: {alt_excel_file}")
                return False
        
        if not os.path.exists(markdown_dir):
            print(f"错误: Markdown目录不存在: {markdown_dir}")
            # 列出父目录内容
            parent_dir = os.path.dirname(markdown_dir)
            if os.path.exists(parent_dir):
                print(f"\n父目录 {parent_dir} 中的内容:")
                for item in os.listdir(parent_dir):
                    print(f"  - {item}")
            return False
        
        # 列出Markdown目录中的文件
        md_files = [f for f in os.listdir(markdown_dir) if f.endswith('.md')]
        print(f"\n找到 {len(md_files)} 个Markdown文件:")
        for md_file in md_files[:5]:  # 只显示前5个文件
            print(f"  - {md_file}")
        if len(md_files) > 5:
            print(f"  ... 还有 {len(md_files)-5} 个文件")
        
        print("\n=== 开始处理 ===")
        # 执行插入操作
        success = insert_md_to_excel(
            excel_file=excel_file,
            markdown_dir=markdown_dir,
            date_str=date_str,
            language="cn"
        )
        
        if success:
            print("\n✅ 成功完成MD文件插入到Excel")
        else:
            print("\n❌ MD文件插入失败")
        
        return success
        
    except Exception as e:
        print(f"\n❌ 发生错误:")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print("\n详细错误追踪:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
