# Toolify AI 产品分析工具

**作者**: smallzero
**邮箱**: smallzero888@gmail.com

> 本项目在开发过程中使用了 AI 辅助工具进行代码编写和优化。

这是一个用于自动分析 Toolify 网站上的 AI 产品数据的工具集。它可以爬取数据、进行产品分析、生成分析报告，并支持 GPU 加速进行数据处理。

## 功能特点

- 支持爬取 Toolify 网站的 AI 产品排行榜数据（中英文版本）
- 使用 DeepSeek API 或 OpenAI API 进行产品分析
- 生成结构化的产品分析 Markdown 文件
- 通过 TensorFlow 支持 GPU 加速数据分析
- 更新 Excel 文件，包含完整分析结果
- 支持查询域名信息
- 优化的批处理和并行处理能力
- 美观的进度条显示

## 环境要求

### Python 环境
- Python 3.8 或更高版本
- 强烈建议使用虚拟环境(venv)隔离依赖

### 创建虚拟环境
```bash
# 创建虚拟环境
python -m venv toolify_env

# 激活虚拟环境 (Windows)
toolify_env\Scripts\activate

# 激活虚拟环境 (Linux/Mac)
source toolify_env/bin/activate
```

## 安装

1. 克隆此仓库：
```bash
git clone https://github.com/smallzero888/toolify-analysis.git
cd toolify-analysis
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

主要依赖库包括：
- pandas (数据处理)
- openpyxl (Excel文件处理)
- requests (API请求)
- selenium (网页爬虫)
- beautifulsoup4 (HTML解析)
- tqdm (进度条显示)
- python-dotenv (环境变量管理)
- tensorflow (可选，用于GPU加速)

3. 配置环境变量：
   - 复制 `.env.example` 到 `.env`
   - 编辑 `.env` 文件，设置您的 API 密钥和其他配置
   - 在 `.env` 文件中配置 `CHROME_DRIVER_PATH` 变量，指向您系统中 ChromeDriver 的实际路径

## 爬虫配置

### ChromeDriver 安装
1. 下载与您Chrome浏览器版本匹配的ChromeDriver：
   - 访问 [ChromeDriver下载页面](https://chromedriver.chromium.org/downloads)
   - 选择与您Chrome浏览器版本匹配的驱动程序
   - 下载并解压到适当的位置

2. 配置ChromeDriver路径：
   - 在项目根目录创建或编辑`.env`文件
   - 添加以下内容：
     ```
     CHROME_DRIVER_PATH=你的ChromeDriver路径
     ```

### API密钥配置
在`.env`文件中添加以下内容：
```
OPENAI_API_KEY=你的OpenAI API密钥
DEEPSEEK_API_KEY=你的DeepSeek API密钥
```

## 使用方法

### 基本用法

```bash
python run_analysis.py
```

这将执行完整的数据分析流程：
1. 使用最新的本地数据文件（如果存在）
2. 分析中文和英文数据
3. 使用 GPU 加速（如果可用）

### 常用参数

#### 指定分析范围
```bash
# 分析特定排名范围的产品
python run_analysis.py --rank-range 1-10

# 分析特定产品ID
python run_analysis.py --product-ids 1,2,3
```

#### 选择分析API
```bash
# 使用OpenAI进行分析
python run_analysis.py --api openai

# 使用DeepSeek进行分析
python run_analysis.py --api deepseek
```

#### 语言选择
```bash
# 分析中文榜单
python run_analysis.py --language cn

# 分析英文榜单
python run_analysis.py --language en
```

#### 使用本地Excel文件（不爬取数据）
```bash
python run_analysis.py --no-scraping
```

#### 更新Excel文件
```bash
python run_analysis.py --update-excel
```

#### 组合使用
```bash
# 使用OpenAI分析中文榜单中排名1-5的产品，不爬取数据，更新Excel
python run_analysis.py --rank-range 1-5 --api openai --language cn --no-scraping --update-excel
```

#### 其他常用参数
- `--scraping`：重新爬取 Toolify 数据
- `--language [cn|en|both]`：选择语言，`both`表示同时处理中英文数据
- `--use-gpu`：启用 GPU 加速
- `--no-analysis`：只爬取数据，不进行分析
- `--domain-info`：查询域名信息
- `--limit N`：限制处理的产品数量为 N
- `--start N`：从第 N 个产品开始处理
- `--batch-size N`：设置批处理大小为 N
- `--delay N`：设置 API 调用间隔为 N 秒
- `--excel-file PATH`：指定Excel文件路径
- `--retry-count N`：设置API调用失败时的重试次数

### 示例

#### 爬取数据

同时爬取中英文榜单，使用 GPU 加速：
```bash
python run_analysis.py --scraping --language both --use-gpu
```

只爬取中文榜单数据，不进行分析：
```bash
python run_analysis.py --scraping --language cn --no-analysis
```

只爬取英文榜单数据，不进行分析：
```bash
python run_analysis.py --scraping --language en --no-analysis
```

爬取数据并限制数量：
```bash
python run_analysis.py --scraping --language cn --no-analysis --count 10
```

#### 分析数据

使用DeepSeek API分析中文榜单中特定产品ID：
```bash
python run_analysis.py --product-ids 1,2,4,5 --api deepseek --language cn --no-scraping
```

使用DeepSeek API分析英文榜单中特定产品ID：
```bash
python run_analysis.py --product-ids 1,2,4,5 --api deepseek --language en --no-scraping
```

使用DeepSeek API分析中文榜单中排名范围的产品：
```bash
python run_analysis.py --rank-range 1-5 --api deepseek --language cn --no-scraping
```

使用DeepSeek API分析英文榜单中排名范围的产品：
```bash
python run_analysis.py --rank-range 1-5 --api deepseek --language en --no-scraping
```

#### 处理分析结果

将中文Markdown文件插入到Excel表格中：
```bash
python run_analysis.py --insert-md --language cn
```

将英文Markdown文件插入到Excel表格中：
```bash
python run_analysis.py --insert-md --language en
```

同时处理中英文Markdown文件：
```bash
python run_analysis.py --insert-md --language both
```

指定特定的Excel文件和Markdown目录：
```bash
python run_analysis.py --insert-md --excel-file output\toolify_data\Toolify_AI_Revenue_CN_20250422.xlsx --markdown-dir output\toolify_analysis_20250422\cn\markdown_files
```

指定日期处理分析结果：
```bash
python run_analysis.py --insert-md --language cn --date 20250422
```

如果你仍然想使用单独的脚本（不推荐）：
```bash
python fix_md_to_excel.py
```

## 文件结构

- `run_analysis.py`：主脚本，整合所有功能
- `analyze_product.py`：产品分析器，处理 API 调用和数据分析
- `toolify_scraper.py`：网络爬虫，爬取 Toolify 网站数据
- `toolify_utils.py`：工具函数集，提供各种实用函数
- `fix_md_to_excel.py`：单独的Markdown插入工具（功能已集成到主程序）
- `requirements.txt`：依赖库列表
- `.env.example`：环境变量示例文件

## 输出文件

- `output/toolify_data/`：存储爬取的原始数据和分析结果
  - `Toolify_AI_Revenue_CN_*.xlsx`：中文榜单原始数据
  - `Toolify_AI_Revenue_EN_*.xlsx`：英文榜单原始数据
  - `Toolify_AI_Revenue_CN_*_analyzed.xlsx`：包含完整分析的中文榜单

- `output/toolify_analysis_当日日期/`：存储分析结果
  - `cn/markdown_files/`：中文产品分析的 Markdown 文件
  - `en/markdown_files/`：英文产品分析的 Markdown 文件

## 注意事项

- 请确保您拥有合法的 API 密钥（DeepSeek 或 OpenAI）
- GPU 加速需要安装 TensorFlow 和相应的 CUDA 支持
- 爬取数据时需遵守网站的使用条款和爬虫协议

### ChromeDriver 配置

- 爬取数据需要安装与您的 Chrome 浏览器版本匹配的 ChromeDriver
- 您可以从以下地址下载 ChromeDriver：[https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads)
- 安装后，在 `.env` 文件中设置 `CHROME_DRIVER_PATH` 变量指向 ChromeDriver 的实际路径
- 如果未设置，程序将尝试使用相对路径或自动下载 ChromeDriver

## 简洁使用指南

### 环境要求
- Python 3.8+
- 建议使用虚拟环境(venv)

```bash
# 创建并激活虚拟环境
python -m venv toolify_env
toolify_env\Scripts\activate  # Windows
source toolify_env/bin/activate  # Linux/Mac
```

### 安装依赖
```bash
pip install -r requirements.txt
```

主要依赖：pandas, openpyxl, requests, selenium, beautifulsoup4, tqdm, python-dotenv, tensorflow(可选)

### 爬虫和环境配置
1. 下载与 Chrome 浏览器版本匹配的 [ChromeDriver](https://chromedriver.chromium.org/downloads)
2. 复制 `.env.example` 到 `.env` 并进行配置：
   ```
   # ChromeDriver 路径
   # 请将此路径替换为您系统中 ChromeDriver 的实际路径
   # Windows示例: C:/path/to/chromedriver.exe
   # Mac/Linux示例: /path/to/chromedriver
   CHROME_DRIVER_PATH=你的ChromeDriver路径

   # API密钥
   OPENAI_API_KEY=你的OpenAI API密钥
   DEEPSEEK_API_KEY=你的DeepSeek API密钥

   # TensorFlow配置
   TF_ENABLE_ONEDNN_OPTS=1
   TF_GPU_ALLOCATOR=cuda_malloc_async
   TF_XLA_FLAGS=--tf_xla_enable_xla_devices

   # 其他配置选项
   DEBUG_MODE=false
   LOG_LEVEL=info
   ```

### 常用命令

#### 基本用法
```bash
python run_analysis.py
```

#### 常用参数组合

##### 爬取数据
```bash
# 同时爬取中英文榜单，不进行分析
python run_analysis.py --scraping --language both --no-analysis

# 只爬取中文榜单数据，不进行分析
python run_analysis.py --scraping --language cn --no-analysis

# 只爬取英文榜单数据，不进行分析
python run_analysis.py --scraping --language en --no-analysis

# 爬取数据并限制数量
python run_analysis.py --scraping --language cn --no-analysis --count 10

# 使用GPU加速爬取数据
python run_analysis.py --scraping --language both --no-analysis --gpu
```

##### 分析数据
```bash
# 使用DeepSeek分析中文榜单中特定产品ID
python run_analysis.py --product-ids 1,2,4,5 --api deepseek --language cn --no-scraping

# 使用DeepSeek分析英文榜单中特定产品ID
python run_analysis.py --product-ids 1,2,4,5 --api deepseek --language en --no-scraping

# 使用DeepSeek分析中文榜单中排名1-5的产品
python run_analysis.py --rank-range 1-5 --api deepseek --language cn --no-scraping

# 使用DeepSeek分析英文榜单中排名1-5的产品
python run_analysis.py --rank-range 1-5 --api deepseek --language en --no-scraping

# 使用OpenAI分析中文榜单中排名1-5的产品，更新Excel
python run_analysis.py --rank-range 1-5 --api openai --language cn --no-scraping --update-excel

# 指定特定Excel文件进行分析
python run_analysis.py --product-ids 1,2 --api deepseek --language cn --no-scraping --excel-file output\toolify_data\Toolify_AI_Revenue_CN_20250422.xlsx
```

##### 处理分析结果
```bash
# 将中文Markdown文件插入到Excel表格中
python run_analysis.py --insert-md --language cn

# 将英文Markdown文件插入到Excel表格中
python run_analysis.py --insert-md --language en

# 同时处理中英文Markdown文件
python run_analysis.py --insert-md --language both

# 指定特定的Excel文件和Markdown目录
python run_analysis.py --insert-md --excel-file output\toolify_data\Toolify_AI_Revenue_CN_20250422.xlsx --markdown-dir output\toolify_analysis_20250422\cn\markdown_files

# 指定日期处理分析结果
python run_analysis.py --insert-md --language cn --date 20250422
```

###### Markdown插入参数说明
- `--insert-md`：启用Markdown插入功能
- `--excel-file PATH`：指定Excel文件路径，如果不提供则自动查找
- `--markdown-dir PATH`：指定Markdown文件目录，如果不提供则自动查找
- `--date DATE`：指定日期字符串，格式为YYYYMMDD，如果不提供则使用当前日期
- `--language {cn|en|both}`：指定语言，默认为"both"

输出文件保存在`output/toolify_data/`目录下，文件名格式为`Toolify_AI_Revenue_XX_YYYYMMDD_analyzed.xlsx`。

> 注意：`fix_md_to_excel.py`的功能已经集成到主程序`run_analysis.py`中，推荐使用主程序的`--insert-md`参数。

#### 常用参数说明
- `--rank-range X-Y`: 分析特定排名范围的产品
- `--product-ids X,Y,Z`: 分析特定产品ID
- `--api [openai|deepseek]`: 选择分析API
- `--language [cn|en]`: 选择语言
- `--no-scraping`: 使用本地Excel文件，不爬取数据
- `--update-excel`: 将分析结果更新到Excel文件
- `--retry RETRY_COUNT`: 设置重试次数
- `--gpu`: 使用GPU加速
- `--timeout N`: 设置API超时时间(秒)

### TensorFlow 和 GPU 加速
本工具支持使用 GPU 加速数据处理，需要正确配置 TensorFlow 环境：

1. 安装支持 GPU 的 TensorFlow 版本：
   ```bash
   pip install tensorflow==2.10.0
   ```

2. 安装对应版本的 CUDA 和 cuDNN（参考 [TensorFlow GPU 支持文档](https://www.tensorflow.org/install/gpu)）

3. 在 `.env` 文件中配置以下参数以优化 GPU 性能：
   ```
   TF_ENABLE_ONEDNN_OPTS=1
   TF_GPU_ALLOCATOR=cuda_malloc_async
   TF_XLA_FLAGS=--tf_xla_enable_xla_devices
   ```

4. 运行时使用 `--gpu` 参数启用 GPU 加速：
   ```bash
   python run_analysis.py --gpu
   ```

### 常见问题
- **ChromeDriver版本不匹配**: 下载与Chrome浏览器版本匹配的驱动
- **API调用失败**: 检查API密钥和网络连接
- **分析工具名称不正确**: 确保模板文件中使用`{api_name}`占位符
- **程序运行缓慢**: 尝试使用`--gpu`参数启用GPU加速
- **GPU 不可用**: 检查 CUDA 和 cuDNN 安装，确保与 TensorFlow 版本兼容
- **GPU多线程异常**: 开启GPU辅助加速调用DeepSeek或OpenAI API时可能出现多线程异常。解决方法：
  1. 使用`--retry`参数增加重试次数
  2. 尝试关闭GPU加速，使用CPU模式
  3. 减小并行处理的产品数量，使用`--product-ids`参数指定少量产品

## 许可

MIT