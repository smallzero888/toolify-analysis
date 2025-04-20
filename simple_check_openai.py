#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单检查OpenAI API密钥
"""

import os
import sys
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API密钥
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key and len(sys.argv) > 1:
    api_key = sys.argv[1]

if not api_key:
    print("错误: 未找到OpenAI API密钥")
    sys.exit(1)

print(f"API密钥: {api_key[:5]}...{api_key[-5:]}")

# 设置API URL
api_url = "https://api.openai.com/v1/models"

# 准备请求头
headers = {
    "Authorization": f"Bearer {api_key}"
}

# 发送请求
try:
    print("正在检查API密钥有效性...")
    response = requests.get(api_url, headers=headers, timeout=30)
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("API密钥有效!")
        models = response.json()
        print(f"找到 {len(models['data'])} 个可用模型")
    else:
        print(f"API密钥无效或已过期: {response.text}")
except Exception as e:
    print(f"错误: {str(e)}")
