import os
import time
import pandas as pd
from datetime import datetime
import re
import json
import subprocess
import sys
from dotenv import load_dotenv
from openai import OpenAI
import glob

# 加载环境变量
load_dotenv()

# 读取产品分析框架
def load_analysis_framework():
    """从文件加载分析框架"""
    try:
        framework_file = "analysis_framework.txt"
        if os.path.exists(framework_file):
            with open(framework_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            print(f"⚠️ 未找到分析框架文件 {framework_file}，将使用默认框架")
            return """
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
"""
    except Exception as e:
        print(f"❌ 加载分析框架文件时出错: {str(e)}，将使用默认框架")
        return """## 产品分析框架\n\n💡 这个产品解决的是什么问题？\n\n👤 用户是谁？\n\n..."""

# 产品分析框架
ANALYSIS_FRAMEWORK = load_analysis_framework()

class ProductAnalysisIntegrator:
    def __init__(self, data_dir="./toolify_data", output_dir="./output", batch_size=5, timeout=120, delay=2):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.batch_size = batch_size
        self.timeout = timeout
        self.delay = delay
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            print("⚠️ 未找到DEEPSEEK_API_KEY环境变量，请在.env文件中设置")
            self.client = None
        else:
            self.base_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1")
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)

    def find_excel_files(self, pattern=None):
        """查找所有需要处理的Excel文件"""
        if pattern is None:
            pattern = os.path.join(self.data_dir, "Toolify_Top_AI_Revenue_Rankings_*.xlsx")
        
        files = glob.glob(pattern)
        if not files:
            print(f"❌ 未找到匹配的Excel文件: {pattern}")
            print("📥 尝试运行爬虫获取数据...")
            self.run_scraper()
            # 重新检查文件
            files = glob.glob(pattern)
            if not files:
                print("⚠️ 爬虫运行后仍未找到匹配的文件")
                return []
        
        print(f"✅ 找到 {len(files)} 个Excel文件")
        for file in files:
            print(f"   - {os.path.basename(file)}")
        
        return files
    
    def run_scraper(self):
        """运行爬虫获取数据"""
        scraper_path = "toolify_scraper.py"
        if not os.path.exists(scraper_path):
            print(f"❌ 未找到爬虫脚本: {scraper_path}")
            return False
        
        try:
            print(f"🔍 开始运行爬虫: {scraper_path}")
            cmd = [sys.executable, scraper_path]
            subprocess.run(cmd, check=True)
            print("✅ 爬虫运行完成")
            return True
        except subprocess.SubprocessError as e:
            print(f"❌ 爬虫运行失败: {str(e)}")
            return False

    def load_excel(self, file_path):
        """加载Excel文件"""
        try:
            df = pd.read_excel(file_path)
            print(f"✅ 成功加载Excel文件: {file_path} (共 {len(df)} 条记录)")
            
            # 检测是否是中文文件
            is_chinese = False
            if "排名" in df.columns:
                is_chinese = True
                # 映射中文列名到英文
                column_mapping = {
                    "排名": "Ranking",
                    "工具名称": "Tool Name",
                    "工具链接": "Tool Link",
                    "网站": "Website",
                    "支付平台": "Payment Platform", 
                    "月访问量": "Monthly Visits",
                    "描述": "Description"
                }
                df = df.rename(columns=column_mapping)
            
            # 打印列名，便于调试
            print(f"📋 数据框列名: {list(df.columns)}")
            
            return df, is_chinese
        
        except Exception as e:
            print(f"❌ 加载Excel文件失败: {str(e)}")
            return None, False

    def analyze_product(self, product_data):
        """使用DeepSeek API分析产品"""
        try:
            # 构建分析提示
            product_name = product_data.get("Tool Name", "")
            product_desc = product_data.get("Description", "")
            product_website = product_data.get("Website", "")
            product_revenue = product_data.get("Revenue", "未知")
            product_visits = product_data.get("Monthly Visits", "未知")

            # 如果客户端未初始化，使用模拟分析
            if self.client is None:
                print(f"⚠️ API客户端未初始化，生成模拟分析: {product_name}")
                analysis = self.generate_mock_analysis(product_name, product_desc, product_website)
                core_value, target_users, revenue_model, pitch = self.extract_key_points(analysis)
                
                # 只返回成功提取到的内容
                result = {"完整分析": analysis}
                
                if core_value != "未提取到":
                    result["核心价值"] = core_value
                
                if target_users != "未提取到":
                    result["目标用户"] = target_users
                
                if revenue_model != "未提取到":
                    result["收入模式"] = revenue_model
                
                if pitch != "未提取到":
                    result["一句话推销"] = pitch
                    
                return result
            
            prompt = f"""
我需要你深入分析以下AI产品:

产品名称: {product_name}
产品描述: {product_desc}
产品网站: {product_website}
月收入: {product_revenue}
月访问量: {product_visits}

请按照以下框架分析这个产品:
{ANALYSIS_FRAMEWORK}

回答要针对性强，清晰易懂，不要有冗余内容。不需要添加额外的标题，直接回答问题即可。
回答要有洞察力，说出产品成功的关键点，尤其是关于商业模式、用户获取和价值主张的部分。
基于现有信息，可以适当推测，但要合理。如遇信息不足，请坦诚说明并给出最佳推测。

请给出分析的同时，提取以下几个关键点并用简短的一句话总结：
1. 核心价值：产品最主要解决的问题
2. 目标用户：产品面向的主要用户群体
3. 收入模式：产品主要的赚钱方式
4. 一句话推销：最有力的推广语
"""

            # 调用API
            try:
                if self.client is None:
                    raise Exception("API客户端未初始化，请确保提供有效的API密钥")
                
                response = self.client.chat.completions.create(
                    model="deepseek-reasoner",  # 使用更强大的模型
                    messages=[
                        {"role": "system", "content": "你是一位资深产品专家，擅长分析产品的商业模式、用户需求和市场策略"},
                        {"role": "user", "content": prompt}
                    ],
                    stream=False
                )
                
                analysis = response.choices[0].message.content
            except Exception as api_error:
                print(f"⚠️ API调用失败: {str(api_error)}，将使用分析框架作为提示")
                # 如果API调用失败，直接返回分析框架作为提示
                analysis = f"""## {product_name} 产品分析
                
{ANALYSIS_FRAMEWORK}

(API调用失败，请直接按照以上框架分析该产品)

核心价值：请根据产品信息分析核心价值
目标用户：请根据产品信息分析目标用户
收入模式：请根据产品信息分析收入模式
一句话推销：请根据产品特点提炼推广语
"""
            
            # 提取关键分析点
            core_value, target_users, revenue_model, pitch = self.extract_key_points(analysis)
            
            # 只返回成功提取到的内容
            result = {"完整分析": analysis}
            
            if core_value != "未提取到":
                result["核心价值"] = core_value
            
            if target_users != "未提取到":
                result["目标用户"] = target_users
            
            if revenue_model != "未提取到":
                result["收入模式"] = revenue_model
            
            if pitch != "未提取到":
                result["一句话推销"] = pitch
                
            return result
        
        except Exception as e:
            print(f"❌ 分析产品时出错: {str(e)}")
            return {
                "完整分析": f"分析失败: {str(e)}"
            }
    
    def extract_key_points(self, analysis):
        """从完整分析中提取关键点"""
        # 默认值
        core_value = "未提取到"
        target_users = "未提取到"
        revenue_model = "未提取到"
        pitch = "未提取到"
        
        # 尝试提取核心价值
        if "💡 这个产品解决的是什么问题？" in analysis:
            parts = analysis.split("💡 这个产品解决的是什么问题？")
            if len(parts) > 1:
                value_section = parts[1].split("\n\n")[0].strip()
                if value_section:
                    core_value = value_section[:100] + "..." if len(value_section) > 100 else value_section
        
        # 尝试提取目标用户
        if "👤 用户是谁？" in analysis:
            parts = analysis.split("👤 用户是谁？")
            if len(parts) > 1:
                user_section = parts[1].split("\n\n")[0].strip()
                if user_section:
                    target_users = user_section[:100] + "..." if len(user_section) > 100 else user_section
        
        # 尝试提取收入模式
        if "💰 它赚钱吗？多少？" in analysis:
            parts = analysis.split("💰 它赚钱吗？多少？")
            if len(parts) > 1:
                revenue_section = parts[1].split("\n\n")[0].strip()
                if revenue_section:
                    revenue_model = revenue_section[:100] + "..." if len(revenue_section) > 100 else revenue_section
        
        # 尝试提取一句话推销
        if "🤗 一句话推销：" in analysis:
            parts = analysis.split("🤗 一句话推销：")
            if len(parts) > 1:
                pitch_section = parts[1].split("\n\n")[0].strip()
                if pitch_section:
                    pitch = pitch_section[:100] + "..." if len(pitch_section) > 100 else pitch_section
        
        return core_value, target_users, revenue_model, pitch
    
    def generate_mock_analysis(self, name, desc, website):
        """生成模拟的分析数据（当API不可用时使用）"""
        # 使用简短占位符内容来替代完整的分析框架
        mock_responses = {
            "问题": f"{name}帮助用户自动化完成复杂的任务，提高工作效率，减少重复劳动。",
            "用户": "主要面向专业人士、创意工作者和需要提高工作效率的知识工作者。",
            "需求": "用户需要它来节省时间，提高生产力，减少重复性工作，获得更高质量的输出结果。",
            "评价": "大多数用户对产品的易用性和功能强大给予好评，但也有人提到希望改进的方面。",
            "获客": "主要通过社交媒体营销、内容营销和口碑传播获取用户。",
            "盈利": "是的，通过订阅模式和增值服务实现盈利，具体收入未公开。",
            "学到": "优秀的产品需要同时关注用户体验和解决实际问题的能力，产品功能要聚焦核心价值。",
            "难点": "建立用户信任和构建复杂而直观的用户界面是最具挑战性的部分。",
            "推销": f"{name}让你以十倍速度完成工作，同时提高输出质量。",
            "方法": "与竞品相比，该产品更注重用户体验和自动化程度，而非单纯功能堆砌。",
            "可行": "技术上可行，但需要较强的产品设计能力和对用户需求的深刻理解。",
            "用户": "可以通过内容营销、社区建设和提供免费试用吸引初始用户。",
            "为何": "如果你对这个领域有热情和独特见解，那么你有机会开发类似产品。",
            "坚持": "这取决于你的热情和对解决用户问题的承诺，以及长期投入的能力。"
        }
        
        # 分析框架的行
        framework_lines = ANALYSIS_FRAMEWORK.strip().split('\n')
        
        # 构建响应
        response_parts = []
        current_key = None
        
        for line in framework_lines:
            line = line.strip()
            if not line:
                continue
                
            # 框架的标题行
            if line.startswith('##'):
                continue
                
            # 检测问题行
            if any(emoji in line for emoji in ["💡", "👤", "🤔", "🗣️", "🔍", "💰", "🧠", "🤗", "🎉", "🧭", "❤️"]):
                question = line
                response_parts.append(question)
                
                # 确定当前问题的键
                if "解决的是什么问题" in line:
                    current_key = "问题"
                elif "用户是谁" in line:
                    current_key = "用户"
                elif "为什么需要它" in line:
                    current_key = "需求"
                elif "如何评价" in line:
                    current_key = "评价"
                elif "如何找到用户" in line:
                    current_key = "获客"
                elif "赚钱" in line:
                    current_key = "盈利"
                elif "学到了什么" in line:
                    current_key = "学到"
                elif "什么做法不容易" in line:
                    current_key = "难点"
                elif "一句话推销" in line:
                    current_key = "推销"
                elif "不同的方法" in line:
                    current_key = "方法"
                elif "能做出来" in line:
                    current_key = "可行"
                elif "找到用户" in line:
                    current_key = "用户"
                elif "为什么是我" in line:
                    current_key = "为何"
                elif "能坚持" in line:
                    current_key = "坚持"
                else:
                    current_key = None
                
                # 添加对应的模拟回答
                if current_key and current_key in mock_responses:
                    response_parts.append(mock_responses[current_key])
                else:
                    response_parts.append("暂无数据。")
                
                # 添加空行
                response_parts.append("")
        
        # 连接所有部分
        return "\n".join(response_parts)

    def process_excel_file(self, file_path, limit=None):
        """处理单个Excel文件"""
        # 加载数据
        df, is_chinese = self.load_excel(file_path)
        if df is None:
            return False
        
        # 限制处理的行数（如果需要）
        if limit is not None and limit > 0:
            df = df.head(limit)
        
        # 准备新的列
        df["完整分析"] = ""
        
        # 逐行处理数据
        print(f"🔍 开始分析产品 (共 {len(df)} 个)")
        
        # 使用range和整数索引避免linter错误
        for idx in range(len(df)):
            row = df.iloc[idx]
            product_data = row.to_dict()
            product_name = product_data.get("Tool Name", f"产品 {idx+1}")
            
            print(f"\n📊 分析第 {idx+1}/{len(df)} 个产品: {product_name}")
            
            # 分析产品
            analysis_results = self.analyze_product(product_data)
            
            # 更新DataFrame - 只添加有内容的列
            for key, value in analysis_results.items():
                if key not in df.columns and key != "完整分析":
                    df[key] = ""
                if key == "完整分析":
                    df.at[idx, key] = value
                elif key in df.columns:
                    df.at[idx, key] = value
            
            print(f"✅ 产品分析完成: {product_name}")
            
            # 每处理一个批次后保存进度
            if (idx + 1) % self.batch_size == 0 or idx == len(df) - 1:
                self.save_progress(df, file_path)
            
            # 添加延迟，避免API请求过于频繁
            if idx < len(df) - 1:
                print(f"⏳ 等待 {self.delay} 秒...")
                time.sleep(self.delay)
        
        # 移除所有值为空字符串的列
        for col in df.columns:
            if col not in ["Ranking", "Tool Name", "Tool Link", "Website", "Payment Platform", "Monthly Visits", "Description", "Revenue"]:
                # 检查列是否全为空或"未提取到"
                if df[col].astype(str).str.strip().isin(["", "未提取到"]).all():
                    df = df.drop(columns=[col])
        
        # 保存最终结果
        output_path = self.save_final_result(df, file_path)
        
        print(f"\n✅ 文件处理完成: {os.path.basename(file_path)}")
        print(f"✅ 结果已保存至: {output_path}")
        
        return output_path
    
    def save_progress(self, df, original_file_path):
        """保存处理进度"""
        try:
            # 生成临时文件名
            basename = os.path.basename(original_file_path)
            filename, ext = os.path.splitext(basename)
            progress_path = os.path.join(self.output_dir, f"{filename}_progress{ext}")
            
            # 保存DataFrame
            df.to_excel(progress_path, index=False)
            
            print(f"✅ 进度已保存至: {progress_path}")
            return progress_path
        
        except Exception as e:
            print(f"❌ 保存进度失败: {str(e)}")
            return None
    
    def save_final_result(self, df, original_file_path):
        """保存最终结果"""
        try:
            # 生成输出文件名
            basename = os.path.basename(original_file_path)
            filename, ext = os.path.splitext(basename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"{filename}_analyzed_{timestamp}{ext}")
            
            # 保存DataFrame
            df.to_excel(output_path, index=False)
            
            return output_path
        
        except Exception as e:
            print(f"❌ 保存最终结果失败: {str(e)}")
            return None
    
    def run(self, limit=None, language=None):
        """运行处理流程"""
        # 查找Excel文件
        if language == "cn":
            pattern = os.path.join(self.data_dir, "Toolify_Top_AI_Revenue_Rankings_CN_*.xlsx")
        elif language == "en":
            pattern = os.path.join(self.data_dir, "Toolify_Top_AI_Revenue_Rankings_EN_*.xlsx")
        else:
            pattern = os.path.join(self.data_dir, "Toolify_Top_AI_Revenue_Rankings_*.xlsx")
        
        excel_files = self.find_excel_files(pattern)
        
        if not excel_files:
            return False
        
        # 处理每个文件
        results = []
        for file_path in excel_files:
            output_path = self.process_excel_file(file_path, limit)
            if output_path:
                results.append(output_path)
        
        if results:
            print(f"\n✅ 全部处理完成，共处理 {len(results)} 个文件:")
            for path in results:
                print(f"   - {path}")
            return True
        else:
            print("\n❌ 没有成功处理任何文件")
            return False

def main():
    import argparse
    
    # 获取D盘下的工作目录
    d_drive_path = "D:\\code\\chromedriver-win64"
    if os.path.exists(d_drive_path):
        os.chdir(d_drive_path)
        print(f"✅ 已切换到工作目录: {d_drive_path}")
    
    parser = argparse.ArgumentParser(description="Toolify数据分析集成工具")
    parser.add_argument("-d", "--data-dir", default="./toolify_data", help="数据目录路径")
    parser.add_argument("-o", "--output-dir", default="./output", help="输出目录路径")
    parser.add_argument("-b", "--batch-size", type=int, default=5, help="批处理大小")
    parser.add_argument("-l", "--limit", type=int, help="每个文件处理的最大记录数")
    parser.add_argument("-t", "--timeout", type=int, default=120, help="API调用超时时间(秒)")
    parser.add_argument("-w", "--wait", type=int, default=2, help="API调用间延迟(秒)")
    parser.add_argument("--language", choices=["cn", "en", "all"], default="all", help="处理的语言版本")
    
    args = parser.parse_args()
    
    language = None if args.language == "all" else args.language
    
    integrator = ProductAnalysisIntegrator(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        timeout=args.timeout,
        delay=args.wait
    )
    
    integrator.run(limit=args.limit, language=language)

if __name__ == "__main__":
    main() 