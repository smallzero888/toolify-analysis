#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查OpenAI API密钥状态

此脚本用于检查OpenAI API密钥的状态，包括：
1. 密钥是否有效
2. 密钥的配额使用情况
3. 密钥的模型访问权限
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def check_api_key(api_key=None):
    """检查API密钥状态"""
    # 获取API密钥
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("错误: 未找到OpenAI API密钥")
        print("请通过以下方式提供API密钥:")
        print("1. 在.env文件中设置OPENAI_API_KEY")
        print("2. 作为命令行参数传递: python check_openai_key_status.py YOUR_API_KEY")
        return False
    
    # 打印API密钥的前5位和后5位字符（保护隐私）
    print(f"正在检查API密钥: {api_key[:5]}...{api_key[-5:]}")
    
    # 设置API URL
    api_url = "https://api.openai.com/v1"
    
    # 准备请求头
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 检查模型列表（验证密钥是否有效）
    try:
        print("\n1. 检查API密钥有效性和可用模型...")
        response = requests.get(
            f"{api_url}/models",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            models = response.json()
            print(f"✅ API密钥有效! 找到 {len(models['data'])} 个可用模型")
            
            # 显示一些常用模型是否可用
            common_models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "text-embedding-ada-002"]
            available_models = [model["id"] for model in models["data"]]
            
            print("\n可用的常用模型:")
            for model in common_models:
                if any(m.startswith(model) for m in available_models):
                    print(f"  ✓ {model}")
                else:
                    print(f"  ✗ {model}")
        else:
            print(f"❌ API密钥无效或已过期: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 检查模型列表时出错: {str(e)}")
        return False
    
    # 测试简单的API调用（检查配额）
    try:
        print("\n2. 测试API调用（检查配额）...")
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Hello, this is a test message. Please respond with 'OK'."}
            ],
            "temperature": 0.7,
            "max_tokens": 10
        }
        
        response = requests.post(
            f"{api_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result["choices"][0]["message"]["content"]
            print(f"✅ API调用成功! 响应: {message}")
            
            # 显示使用情况
            usage = result.get("usage", {})
            if usage:
                print(f"  令牌使用情况: 提示={usage.get('prompt_tokens', 0)}, 完成={usage.get('completion_tokens', 0)}, 总计={usage.get('total_tokens', 0)}")
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
            # 检查是否是配额问题
            if response.status_code == 429:
                error_data = response.json().get("error", {})
                if error_data.get("type") == "insufficient_quota":
                    print("\n⚠️ 配额不足! 您的API密钥已超出使用限制。")
                    print("请访问 https://platform.openai.com/account/billing 检查您的账单和使用情况。")
                    print("如果您使用的是免费试用额度，可能已经用完。")
            return False
    except Exception as e:
        print(f"❌ 测试API调用时出错: {str(e)}")
        return False
    
    print("\n✅ API密钥检查完成，密钥有效且可用!")
    return True

if __name__ == "__main__":
    # 检查是否提供了命令行参数
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        check_api_key(api_key)
    else:
        check_api_key()
