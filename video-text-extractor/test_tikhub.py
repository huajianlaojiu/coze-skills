#!/usr/bin/env python3
"""
抖音视频文案提取 - TikHub API 测试脚本
使用前请先设置环境变量 TIKHUB_API_KEY

安装依赖:
    pip install requests

使用方式:
    # 设置API Key
    export TIKHUB_API_KEY="your_api_key"
    
    # 运行测试
    python test_tikhub.py "https://v.douyin.com/cDjKxQJsNSk/"
"""

import os
import sys
import requests
from typing import Optional, Dict, Any

# 配置
API_KEY = os.environ.get("TIKHUB_API_KEY", "")
BASE_URL = "https://api.tikhub.io/api/v1"


def get_douyin_video_by_share_url(share_url: str, api_key: str) -> Dict[str, Any]:
    """
    通过抖音分享链接获取视频信息
    
    Args:
        share_url: 抖音分享链接，如 https://v.douyin.com/xxxxx
        api_key: TikHub API Key
    
    Returns:
        API响应结果
    """
    if not api_key:
        return {"success": False, "error": "API Key未设置，请设置环境变量 TIKHUB_API_KEY"}
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 使用抖音Web API
    url = f"{BASE_URL}/douyin/web/fetch_one_video"
    params = {"share_url": share_url}
    
    try:
        print(f"[请求] URL: {url}")
        print(f"[请求] 参数: {params}")
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print(f"[响应] {data}")
        
        if data.get("code") == 200:
            video_data = data.get("data", {})
            return {
                "success": True,
                "title": video_data.get("desc", ""),  # 视频文案/标题
                "video_id": video_data.get("aweme_id", ""),
                "author": video_data.get("author", {}).get("nickname", ""),
                "author_id": video_data.get("author", {}).get("uid", ""),
                "statistics": video_data.get("statistics", {}),
                "duration": video_data.get("video", {}).get("duration", 0),
                "create_time": video_data.get("create_time", ""),
            }
        else:
            return {"success": False, "error": data.get("message", "Unknown error")}
            
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def get_video_by_aweme_id(aweme_id: str, api_key: str) -> Dict[str, Any]:
    """
    通过视频ID获取视频信息（更稳定）
    """
    if not api_key:
        return {"success": False, "error": "API Key未设置"}
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    # 使用 TikTok/Douyin App V3 API
    url = f"{BASE_URL}/tiktok/app/v3/fetch_one_video"
    params = {"aweme_id": aweme_id}
    
    try:
        print(f"[请求] URL: {url}")
        print(f"[请求] 参数: {params}")
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print(f"[响应] {data}")
        
        if data.get("code") == 200:
            video_data = data.get("data", {})
            return {
                "success": True,
                "title": video_data.get("desc", ""),
                "video_id": aweme_id,
                "author": video_data.get("author", {}).get("nickname", ""),
                "statistics": video_data.get("statistics", {}),
            }
        else:
            return {"success": False, "error": data.get("message", "Unknown error")}
            
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def extract_video_id_from_url(share_url: str) -> Optional[str]:
    """
    从分享链接中提取视频ID（如果API不支持分享链接时使用）
    
    注意：这个功能可能需要X-Bogus等参数，TikHub API可以处理
    """
    # 抖音短链接格式: https://v.douyin.com/xxxxx
    # 抖音普通链接格式: https://www.douyin.com/video/xxxxx
    
    import re
    
    # 尝试从普通链接提取
    pattern1 = r'douyin\.com/video/(\d+)'
    match1 = re.search(pattern1, share_url)
    if match1:
        return match1.group(1)
    
    # 短链接需要通过API解析，这里返回None让API处理
    return None


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("=" * 60)
        print("抖音视频文案提取 - TikHub API 测试")
        print("=" * 60)
        print()
        print("使用方法:")
        print("  python test_tikhub.py <抖音链接>")
        print()
        print("示例:")
        print("  python test_tikhub.py https://v.douyin.com/cDjKxQJsNSk/")
        print()
        print("环境变量:")
        print("  export TIKHUB_API_KEY='your_api_key'")
        print()
        print("-" * 60)
        print("提示: 请先访问 https://tikhub.io 注册并获取API Key")
        print("-" * 60)
        sys.exit(1)
    
    # 获取参数
    share_url = sys.argv[1]
    
    print("=" * 60)
    print("抖音视频文案提取测试")
    print("=" * 60)
    print(f"输入链接: {share_url}")
    print()
    
    # 检查API Key
    if not API_KEY:
        print("❌ 错误: TIKHUB_API_KEY 环境变量未设置")
        print()
        print("请先注册 TikHub 并获取 API Key:")
        print("  1. 访问 https://tikhub.io 注册账号")
        print("  2. 控制台 → API密钥 → 创建密钥")
        print("  3. 设置环境变量:")
        print("     export TIKHUB_API_KEY='your_api_key'")
        sys.exit(1)
    
    print(f"✅ API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
    print()
    
    # 调用API
    print("正在获取视频信息...")
    print("-" * 60)
    
    result = get_douyin_video_by_share_url(share_url, API_KEY)
    
    print("-" * 60)
    print()
    
    # 输出结果
    if result["success"]:
        print("✅ 获取成功!")
        print()
        print("📋 视频信息:")
        print(f"   文案/标题: {result.get('title', 'N/A')}")
        print(f"   视频ID: {result.get('video_id', 'N/A')}")
        print(f"   作者: {result.get('author', 'N/A')}")
        print(f"   时长: {result.get('duration', 0) / 1000:.1f}秒")
        
        stats = result.get('statistics', {})
        if stats:
            print(f"   点赞: {stats.get('digg_count', 0)}")
            print(f"   评论: {stats.get('comment_count', 0)}")
            print(f"   转发: {stats.get('share_count', 0)}")
            print(f"   收藏: {stats.get('collect_count', 0)}")
        
        # 保存结果到文件
        output_file = "video_result.json"
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print()
        print(f"💾 结果已保存到: {output_file}")
    else:
        print(f"❌ 获取失败: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
