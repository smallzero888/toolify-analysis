#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单测试OpenAI API连接
"""

import os
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API密钥
api_key = os.environ.get("OPENAI_API_KEY")
print(f"API密钥: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")

# 设置API URL
api_url = "https://api.openai.com/v1/chat/completions"
print(f"API URL: {api_url}")

# 准备请求
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "user", "content": "Say hello"}
    ],
    "temperature": 0.7,
    "max_tokens": 10
}

# 发送请求
try:
    print("正在发送请求...")
    response = requests.post(
        api_url,
        headers=headers,
        json=data,
        timeout=30
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
except Exception as e:
    print(f"错误: {str(e)}")
