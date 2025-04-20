#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OpenAI API测试脚本

按照OpenAI API文档 (https://platform.openai.com/docs/api-reference/introduction) 实现的测试脚本
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_openai_api(api_key=None):
    """测试OpenAI API"""
    # 获取API密钥
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("错误: 未找到OpenAI API密钥")
        print("请通过以下方式提供API密钥:")
        print("1. 在.env文件中设置OPENAI_API_KEY")
        print("2. 作为命令行参数传递: python openai_api_test.py YOUR_API_KEY")
        return False
    
    # 打印API密钥的前5位和后5位字符（保护隐私）
    print(f"使用API密钥: {api_key[:5]}...{api_key[-5:]}")
    
    # 设置API基础URL
    api_base = "https://api.openai.com/v1"
    
    # 准备请求头
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 测试1: 获取模型列表
    print("\n1. 测试获取模型列表...")
    try:
        response = requests.get(
            f"{api_base}/models",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            models = response.json()
            print(f"✅ 成功获取模型列表! 找到 {len(models['data'])} 个模型")
        else:
            print(f"❌ 获取模型列表失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 获取模型列表时出错: {str(e)}")
        return False
    
    # 测试2: 创建聊天完成
    print("\n2. 测试创建聊天完成...")
    try:
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, can you hear me?"}
            ],
            "temperature": 0.7,
            "max_tokens": 50
        }
        
        response = requests.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result["choices"][0]["message"]["content"]
            print(f"✅ 成功创建聊天完成!")
            print(f"响应: {message}")
            
            # 显示使用情况
            usage = result.get("usage", {})
            if usage:
                print(f"令牌使用情况: 提示={usage.get('prompt_tokens', 0)}, 完成={usage.get('completion_tokens', 0)}, 总计={usage.get('total_tokens', 0)}")
        else:
            print(f"❌ 创建聊天完成失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
            # 检查是否是配额问题
            if response.status_code == 429:
                error_data = response.json().get("error", {})
                if error_data.get("type") == "insufficient_quota":
                    print("\n⚠️ 配额不足! 您的API密钥已超出使用限制。")
                    print("请访问 https://platform.openai.com/account/billing 检查您的账单和使用情况。")
            return False
    except Exception as e:
        print(f"❌ 创建聊天完成时出错: {str(e)}")
        return False
    
    # 测试3: 创建嵌入
    print("\n3. 测试创建嵌入...")
    try:
        data = {
            "model": "text-embedding-ada-002",
            "input": "The food was delicious and the waiter..."
        }
        
        response = requests.post(
            f"{api_base}/embeddings",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            embedding = result["data"][0]["embedding"]
            print(f"✅ 成功创建嵌入!")
            print(f"嵌入维度: {len(embedding)}")
            
            # 显示使用情况
            usage = result.get("usage", {})
            if usage:
                print(f"令牌使用情况: 提示={usage.get('prompt_tokens', 0)}, 总计={usage.get('total_tokens', 0)}")
        else:
            print(f"❌ 创建嵌入失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 创建嵌入时出错: {str(e)}")
        return False
    
    print("\n✅ 所有测试完成! API密钥有效且可用。")
    return True

if __name__ == "__main__":
    # 检查是否提供了命令行参数
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        test_openai_api(api_key)
    else:
        test_openai_api()
