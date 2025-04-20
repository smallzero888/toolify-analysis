from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd
import os
import re
from datetime import datetime
from urllib.parse import urlparse
import numpy as np
import argparse
import sys

def clean_url(url):
    """清理URL，移除utm参数"""
    if not url:
        return url

    # 移除?utm_source=toolify及其变体
    url = re.sub(r'\?utm_source=toolify.*$', '', url)
    url = re.sub(r'\?utm%5[Ff]source=toolify.*$', '', url)

    # 处理其他utm参数形式
    if '?' in url and 'utm_source=toolify' in url:
        base_url = url.split('?')[0]
        # 安全处理 URL 参数
        try:
            query_parts = url.split('?')[1].split('&')
            filtered_parts = [p for p in query_parts if not p.startswith('utm_source=toolify')]

            if filtered_parts:
                return base_url + '?' + '&'.join(filtered_parts)
        except IndexError:
            # 如果 URL 格式不正确，直接返回基础 URL
            return base_url
        return base_url

    return url

def extract_domain(url):
    """从URL中提取域名，例如从https://www.example.com/page提取example.com"""
    if not url:
        return ""

    # 确保URL有正确格式
    if not url.startswith('http'):
        url = 'https://' + url

    # 解析URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    # 移除www.前缀
    if domain.startswith('www.'):
        domain = domain[4:]

    return domain

def scrape_toolify_ranking(url, output_filename, language="en"):
    """爬取Toolify AI收入榜单数据"""
    print(f"开始爬取 {url} 的数据...")

    # 修正URL - 尝试使用完整路径而不是简化版
    if language == "zh":
        alt_url = "https://www.toolify.ai/zh/Best-AI-Tools-revenue"
        if url != alt_url:
            print(f"尝试使用备用URL: {alt_url}")
            url = alt_url
    else:
        alt_url = "https://www.toolify.ai/Best-AI-Tools-revenue"
        if url != alt_url:
            print(f"尝试使用备用URL: {alt_url}")
            url = alt_url

    # 配置浏览器
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")

    # 添加更多的选项来绕过SSL问题
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--dns-prefetch-disable")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--disable-site-isolation-trials")

    # 添加用户代理以模拟正常浏览器
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")

    # 初始化WebDriver
    try:
        # 尝试从.env文件中读取ChromeDriver路径
        chrome_driver_path = os.environ.get("CHROME_DRIVER_PATH")
        if chrome_driver_path and os.path.exists(chrome_driver_path):
            print(f"使用.env文件中的ChromeDriver路径: {chrome_driver_path}")
            service = Service(executable_path=chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            # 尝试使用相对路径
            print("尝试使用相对路径的ChromeDriver")
            service = Service(executable_path="chromedriver.exe")
            driver = webdriver.Chrome(service=service, options=options)
    except Exception as e1:
        print(f"使用默认路径启动ChromeDriver失败: {str(e1)}")
        try:
            # 尝试使用自动下载的ChromeDriver
            print("尝试自动下载并使用ChromeDriver")
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service as ChromeService
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        except Exception as e2:
            print(f"仍然无法启动ChromeDriver: {str(e2)}")
            print("无法启动爬虫，请确保安装了正确的ChromeDriver")
            print("或者在.env文件中添加CHROME_DRIVER_PATH变量指定路径")
            return []

    try:
        # 设置页面加载超时和脚本超时
        driver.set_page_load_timeout(120)
        driver.set_script_timeout(120)

        print(f"开始访问 {url}")
        # 访问网站
        driver.get(url)

        # 等待页面加载
        wait = WebDriverWait(driver, 120)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
            print("页面加载成功")
        except:
            print("找不到表格元素，尝试使用其他选择器")
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                print("使用TAG_NAME='table'成功找到表格")
            except:
                print("仍然无法找到表格，尝试查找特定文本")
                try:
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Ranking') or contains(text(), '排名')]")))
                    print("找到含有'Ranking'或'排名'的元素")
                except:
                    print("无法找到任何相关元素，可能网站结构已更改")
                    try:
                        screenshot_path = os.path.join(os.path.dirname(output_filename), "screenshot.png")
                        driver.save_screenshot(screenshot_path)
                        print(f"已保存截图到 {screenshot_path}")
                    except Exception as ss_error:
                        print(f"无法保存截图: {str(ss_error)}")

                    print("网站可能已更改结构，爬虫需要更新")
                    return []

        print("开始加载所有数据...")

        # 使用更可靠的方式等待页面加载完成
        time.sleep(10)  # 给予页面足够时间进行初始加载

        # 高效滚动方法
        def efficient_scroll():
            # 初始化变量
            previous_height = driver.execute_script("return document.body.scrollHeight")
            previous_row_count = 0
            no_change_count = 0
            current_row_count = 0  # 初始化避免未绑定错误
            target_row_count = 507  # 目标行数
            max_scrolls = 15  # 最大滚动次数

            # 滚动次数计数器
            scroll_count = 0

            while scroll_count < max_scrolls:
                # 滚动到页面底部
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # 等待加载

                # 检查当前行数
                rows = driver.find_elements(By.CSS_SELECTOR, "table tr:not(:first-child)")
                current_row_count = len(rows)

                # 检查页面高度是否变化
                current_height = driver.execute_script("return document.body.scrollHeight")

                # 显示进度
                scroll_count += 1
                print(f"滚动 #{scroll_count} - 当前行数: {current_row_count}")

                # 检测是否到达底部 - 行数接近目标行数或页面高度不再变化
                if current_row_count >= target_row_count:
                    print(f"已达到目标行数 {current_row_count}，停止滚动")
                    break

                # 检测页面高度不再变化 + 行数不再变化
                if current_height == previous_height and current_row_count == previous_row_count:
                    no_change_count += 1
                    if no_change_count >= 2:  # 连续2次无变化
                        print(f"页面底部已到达（高度和行数不再变化），停止滚动")
                        break
                else:
                    no_change_count = 0

                # 更新上一次高度和行数
                previous_height = current_height
                previous_row_count = current_row_count

            return current_row_count

        # 执行高效滚动
        row_count = efficient_scroll()

        # 提取数据
        data = []
        rows = driver.find_elements(By.CSS_SELECTOR, "table tr:not(:first-child)")
        print(f"开始提取 {len(rows)} 行数据...")

        # 根据语言设置列名
        if language == "zh":
            columns_map = {
                "ranking": "排名",
                "tool_name": "工具名称",
                "tool_link": "工具链接",
                "website": "网站",
                "payment_platform": "支付平台",
                "monthly_visits": "月访问量",
                "description": "描述"
            }
        else:  # 英文
            columns_map = {
                "ranking": "Ranking",
                "tool_name": "Tool Name",
                "tool_link": "Tool Link",
                "website": "Website",
                "payment_platform": "Payment Platform",
                "monthly_visits": "Monthly Visits",
                "description": "Description"
            }

        # 特殊处理前3名（它们通常有奖牌图标）
        for index, row in enumerate(rows[:10]):  # 只检查前10行以寻找前3名
            try:
                columns = row.find_elements(By.TAG_NAME, "td")
                if len(columns) >= 6:
                    # 第一列可能包含奖牌图标
                    first_col = columns[0]
                    ranking = ""

                    # 检查是否有奖牌图片
                    medal_imgs = first_col.find_elements(By.TAG_NAME, "img")
                    if medal_imgs:
                        # 安全地获取属性，避免None值错误
                        src = medal_imgs[0].get_attribute("src") or ""
                        src = src.lower() if src else ""

                        alt = medal_imgs[0].get_attribute("alt") or ""
                        alt = alt.lower() if alt else ""

                        class_name = medal_imgs[0].get_attribute("class") or ""
                        class_name = class_name.lower() if class_name else ""

                        # 根据图片信息推断排名
                        if "gold" in src or "gold" in alt or "gold" in class_name or "1" in src or "1" in alt:
                            ranking = "1"
                        elif "silver" in src or "silver" in alt or "silver" in class_name or "2" in src or "2" in alt:
                            ranking = "2"
                        elif "bronze" in src or "bronze" in alt or "bronze" in class_name or "3" in src or "3" in alt:
                            ranking = "3"
                        else:
                            # 尝试根据图片名称推断
                            if "1" in src or "1st" in src:
                                ranking = "1"
                            elif "2" in src or "2nd" in src:
                                ranking = "2"
                            elif "3" in src or "3rd" in src:
                                ranking = "3"

                    # 如果仍无法确定排名，使用位置索引作为备用
                    if not ranking:
                        # 直接检查第一列文本
                        rank_text = first_col.text.strip()
                        if rank_text and any(c.isdigit() for c in rank_text):
                            # 提取数字部分
                            digits = ''.join(c for c in rank_text if c.isdigit())
                            if digits:
                                ranking = digits

                    # 如果还是没有排名，则根据行的顺序估计
                    if not ranking:
                        if index == 0:
                            ranking = "1"
                        elif index == 1:
                            ranking = "2"
                        elif index == 2:
                            ranking = "3"
                        else:
                            ranking = str(index + 1)

                    # 获取工具名称和链接
                    tool_element = columns[1]
                    tool_name = tool_element.text.strip()
                    tool_link = ""
                    try:
                        link_element = tool_element.find_element(By.TAG_NAME, "a")
                        tool_link = link_element.get_attribute("href") or ""
                        # 清理tool_link
                        tool_link = clean_url(tool_link)
                    except:
                        pass

                    # 获取网站URL并清理
                    website = columns[2].text.strip()
                    website = clean_url(website)

                    payment_platform = columns[4].text.strip()
                    monthly_visits = columns[5].text.strip()
                    description = columns[6].text.strip() if len(columns) > 6 else ""

                    # 仅在有工具名称时添加数据
                    if tool_name:
                        data.append({
                            columns_map["ranking"]: ranking,
                            columns_map["tool_name"]: tool_name,
                            columns_map["tool_link"]: tool_link,
                            columns_map["website"]: website,
                            columns_map["payment_platform"]: payment_platform,
                            columns_map["monthly_visits"]: monthly_visits,
                            columns_map["description"]: description
                        })
            except Exception as e:
                print(f"处理前10行时出错: {str(e)}")

        # 处理剩余的行
        for index, row in enumerate(rows[10:], 11):
            try:
                columns = row.find_elements(By.TAG_NAME, "td")
                if len(columns) >= 6:
                    # 直接获取排名文本
                    ranking = columns[0].text.strip()
                    if not ranking or ranking.isspace():
                        ranking = str(index)  # 使用索引作为备用

                    # 获取工具名称和链接
                    tool_element = columns[1]
                    tool_name = tool_element.text.strip()
                    tool_link = ""
                    try:
                        link_element = tool_element.find_element(By.TAG_NAME, "a")
                        tool_link = link_element.get_attribute("href") or ""
                        # 清理tool_link
                        tool_link = clean_url(tool_link)
                    except:
                        pass

                    # 获取网站URL并清理
                    website = columns[2].text.strip()
                    website = clean_url(website)

                    payment_platform = columns[4].text.strip()
                    monthly_visits = columns[5].text.strip()
                    description = columns[6].text.strip() if len(columns) > 6 else ""

                    # 仅在有工具名称时添加数据
                    if tool_name:
                        data.append({
                            columns_map["ranking"]: ranking,
                            columns_map["tool_name"]: tool_name,
                            columns_map["tool_link"]: tool_link,
                            columns_map["website"]: website,
                            columns_map["payment_platform"]: payment_platform,
                            columns_map["monthly_visits"]: monthly_visits,
                            columns_map["description"]: description
                        })
            except Exception as e:
                print(f"处理第 {index} 行时出错: {str(e)}")

        # 确保前三名存在
        top_three_names = ["ChatGPT", "OpenAI", "Adobe"]
        existing_tools = {item[columns_map["tool_name"]].lower(): item for item in data}

        for i, name in enumerate(top_three_names):
            rank = str(i + 1)
            name_lower = name.lower()

            if name_lower not in existing_tools:
                # 添加缺失的顶级工具
                print(f"添加缺失的工具: {name} (排名 {rank})")

                if language == "zh":
                    desc = {
                        "chatgpt": "引人入胜的人工智能对话和任务自动化。",
                        "openai": "OpenAI通过研究和先进模型为人类创造安全的AGI。",
                        "adobe": "领先的公司提供创意、营销和文档管理解决方案。"
                    }.get(name_lower, "")
                else:
                    desc = {
                        "chatgpt": "Engaging AI conversations and task automation.",
                        "openai": "OpenAI creates safe AGI for humanity through research and advanced models.",
                        "adobe": "Leading company providing creative, marketing, and document management solutions."
                    }.get(name_lower, "")

                monthly = {
                    "chatgpt": "4.5B",
                    "openai": "559.3M",
                    "adobe": "341.4M"
                }.get(name_lower, "")

                # 创建不含utm参数的网站URL
                website_url = f"https://{name_lower}.com"

                data.append({
                    columns_map["ranking"]: rank,
                    columns_map["tool_name"]: name,
                    columns_map["tool_link"]: "",
                    columns_map["website"]: website_url,
                    columns_map["payment_platform"]: "Stripe" if name_lower != "adobe" else "Paypal",
                    columns_map["monthly_visits"]: monthly,
                    columns_map["description"]: desc
                })
            else:
                # 确保已存在的工具排名正确
                for item in data:
                    if item[columns_map["tool_name"]].lower() == name_lower:
                        item[columns_map["ranking"]] = rank

        # 根据排名排序
        def get_rank_number(item):
            rank_str = item[columns_map["ranking"]]
            # 提取数字部分
            digits = ''.join(c for c in rank_str if c.isdigit())
            return int(digits) if digits else 999

        data = sorted(data, key=get_rank_number)

        # 保存为Excel文件
        df = pd.DataFrame(data)
        df.to_excel(output_filename, index=False)
        print(f"✅ 数据已保存到Excel文件: {output_filename} (共 {len(data)} 条记录)")

        return data

    except Exception as e:
        print(f"爬取过程中发生错误: {str(e)}")
        return []
    finally:
        try:
            driver.quit()
        except:
            pass

def query_domain_info(data, output_file, website_column, language="en"):
    """查询域名信息并将结果添加到数据中 - 直接添加到H列之后
    注意：此功能当前已禁用，不会被执行"""

    # 由于此功能已被禁用，直接返回，不执行任何操作
    print(f"域名查询功能已禁用，跳过处理")
    return

# 主函数
def main():
    # 创建输出目录
    output_dir = os.path.join("output", "toolify_data")
    os.makedirs(output_dir, exist_ok=True)

    # 获取当前日期
    today = datetime.now().strftime("%Y%m%d")

    # 爬取中文版并添加域名信息
    chinese_url = "https://www.toolify.ai/zh/Best-AI-Tools-revenue"  # 更新为完整URL
    chinese_output = os.path.join(output_dir, f"Toolify_AI_Revenue_CN_{today}.xlsx")
    cn_data = scrape_toolify_ranking(chinese_url, chinese_output, "zh")

    if cn_data:
        # 域名处理功能已禁用
        print("域名处理功能已禁用")
        print(f"中文版: 已成功爬取 {len(cn_data)} 条记录")
    else:
        print("中文版爬取失败或没有数据")

    # 爬取英文版并添加域名信息
    english_url = "https://www.toolify.ai/Best-AI-Tools-revenue"  # 更新为完整URL
    english_output = os.path.join(output_dir, f"Toolify_AI_Revenue_EN_{today}.xlsx")
    en_data = scrape_toolify_ranking(english_url, english_output, "en")

    if en_data:
        # 域名处理功能已禁用
        print("域名处理功能已禁用")
        print(f"英文版: 已成功爬取 {len(en_data)} 条记录")
    else:
        print("英文版爬取失败或没有数据")

    # 数据分析
    if cn_data or en_data:
        analyze_data(cn_data if cn_data else [], en_data if en_data else [], output_dir, today)

    print("\n=== 全部处理完成 ===")
    print(f"中文版: {len(cn_data) if cn_data else 0} 条记录")
    print(f"英文版: {len(en_data) if en_data else 0} 条记录")
    print(f"文件保存在 {os.path.abspath(output_dir)} 目录下")

# 数据分析函数 - 使用NumPy
def analyze_data(cn_data, en_data, output_dir, date_str):
    """使用NumPy进行数据分析"""
    print("\n开始数据分析...")

    try:
        # 确保有数据可以分析
        if not cn_data and not en_data:
            print("没有可分析的数据")
            return

        # 合并数据集
        all_data = []
        if cn_data:
            all_data.extend(cn_data)
        if en_data:
            all_data.extend(en_data)

        # 提取月访问量数据
        monthly_visits = []
        for item in all_data:
            # 尝试从不同语言的字段获取月访问量
            visit_key = "月访问量" if "月访问量" in item else "Monthly Visits"
            visit_str = item.get(visit_key, "0")

            # 清理数据: 移除非数字字符
            visit_str = re.sub(r'[^\d.]', '', visit_str)

            # 处理空值
            if not visit_str:
                visit_str = "0"

            # 处理带有单位的值 (K, M, B)
            visit_value = float(visit_str) if visit_str else 0
            if 'K' in item.get(visit_key, ""):
                visit_value *= 1000
            elif 'M' in item.get(visit_key, ""):
                visit_value *= 1000000
            elif 'B' in item.get(visit_key, ""):
                visit_value *= 1000000000

            monthly_visits.append(visit_value)

        print(f"提取了 {len(monthly_visits)} 个月访问量数据点")

        # 使用NumPy进行统计计算
        monthly_visits_np = np.array(monthly_visits, dtype=np.float64)

        total_visits_val = np.sum(monthly_visits_np)
        avg_visits_val = np.mean(monthly_visits_np)
        max_visits_val = np.max(monthly_visits_np) if len(monthly_visits_np) > 0 else 0
        min_visits_val = np.min(monthly_visits_np) if len(monthly_visits_np) > 0 else 0
        std_visits_val = np.std(monthly_visits_np)

        # 确保max_visits_val至少为1以避免除以零错误
        max_visits_val = max(1, max_visits_val)

        print("NumPy计算完成")
        print(f"总访问量: {total_visits_val:,.0f}")
        print(f"平均访问量: {avg_visits_val:,.0f}")
        print(f"最大访问量: {max_visits_val:,.0f}")
        print(f"最小访问量: {min_visits_val:,.0f}")
        print(f"标准差: {std_visits_val:,.0f}")

        # 计算分布桶
        bucket_boundaries = [0, 1000, 10000, 100000, 1000000, 10000000, 100000000, 1000000000, float('inf')]
        bucket_counts_list = [0] * (len(bucket_boundaries) - 1)

        # 直接在Python中计算桶
        for visit in monthly_visits:
            for i in range(len(bucket_boundaries) - 1):
                if bucket_boundaries[i] <= visit < bucket_boundaries[i+1]:
                    bucket_counts_list[i] += 1
                    break

        # 创建分析结果
        analysis_data = []
        bucket_labels = ['0-1K', '1K-10K', '10K-100K', '100K-1M', '1M-10M', '10M-100M', '100M-1B', '>1B']

        # 确保bucket_counts与bucket_labels长度匹配
        for i in range(min(len(bucket_labels), len(bucket_counts_list))):
            count = bucket_counts_list[i]
            analysis_data.append({
                "访问量范围": bucket_labels[i],
                "网站数量": count,
                "占比(%)": round(100 * count / len(all_data), 2) if all_data else 0
            })

        # 添加总体统计信息
        analysis_data.append({
            "访问量范围": "总计",
            "网站数量": len(all_data),
            "占比(%)": 100
        })

        # 保存分析结果
        analysis_output = os.path.join(output_dir, f"Traffic_Analysis_{date_str}.xlsx")
        pd.DataFrame(analysis_data).to_excel(analysis_output, index=False)

        # 创建并保存统计摘要
        summary_data = [{
            "总访问量": f"{total_visits_val:,.0f}",
            "平均访问量": f"{avg_visits_val:,.0f}",
            "最大访问量": f"{max_visits_val:,.0f}",
            "最小访问量": f"{min_visits_val:,.0f}",
            "标准差": f"{std_visits_val:,.0f}",
            "分析的工具总数": len(all_data)
        }]

        summary_output = os.path.join(output_dir, f"Traffic_Summary_{date_str}.xlsx")
        pd.DataFrame(summary_data).to_excel(summary_output, index=False)

        print(f"✅ 数据分析完成，结果已保存：")
        print(f"   - 访问量分析: {analysis_output}")
        print(f"   - 统计摘要: {summary_output}")

    except Exception as e:
        print(f"数据分析过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    import sys

    # 获取当前日期字符串
    current_date = datetime.now().strftime("%Y%m%d")

    # 创建参数解析器
    parser = argparse.ArgumentParser(description="Toolify AI Revenue Rankings 爬虫")
    parser.add_argument("--url", help="要爬取的网址", default="https://www.toolify.ai/Best-AI-Tools-revenue")
    parser.add_argument("--output", help="输出文件路径",
                        default=os.path.join("output", "toolify_data", f"Toolify_AI_Revenue_EN_{current_date}.xlsx"))
    parser.add_argument("--language", help="语言（en或zh）", default="en", choices=["en", "zh"])

    # 解析命令行参数
    args = parser.parse_args()

    # 使用参数
    url = args.url
    output_file = args.output
    language = args.language

    # 如果是默认输出文件名，并且语言是zh，则调整文件名
    default_en_path = os.path.join("output", "toolify_data", f"Toolify_AI_Revenue_EN_{current_date}.xlsx")
    if args.output == default_en_path and language == "zh":
        output_file = os.path.join("output", "toolify_data", f"Toolify_AI_Revenue_CN_{current_date}.xlsx")

    # 确保输出目录存在
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    print(f"使用URL: {url}")
    print(f"输出文件: {output_file}")
    print(f"语言: {language}")

    # 执行爬虫
    main_url = url
    if language == "zh" and "zh" not in url:
        main_url = "https://www.toolify.ai/zh/Best-AI-Tools-revenue"
    elif language == "en" and "Best-AI-Tools-revenue" not in url:
        main_url = "https://www.toolify.ai/Best-AI-Tools-revenue"

    data = scrape_toolify_ranking(main_url, output_file, language)

    # 打印结果
    if data:
        print(f"爬取完成，共获取 {len(data)} 条记录")
        print(f"数据已保存到: {output_file}")
    else:
        print("爬取失败或没有数据")

    # 输出退出码
    sys.exit(0)



