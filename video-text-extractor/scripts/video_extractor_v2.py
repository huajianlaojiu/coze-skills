#!/usr/bin/env python3
"""
视频文案提取器 V2 - 全平台支持
支持：抖音、快手、B站、小红书

使用方式:
    python video_extractor_v2.py "https://v.douyin.com/xxxxx"
    python video_extractor_v2.py "https://www.kuaishou.com/short-video/xxxxx" --audio
"""

import os
import re
import requests
import json
import time
import subprocess
import tempfile
from typing import Optional, Dict, Any

# ============== 配置 ==============
TIKHUB_API_KEY = os.environ.get("TIKHUB_API_KEY", "t8wYXM8P3Vu5qGe6HoOtxzqKFD62A6Nq4SP7t1S/cNa4jw+LIk+RbDWEFQ==")
TIKHUB_BASE_URL = "https://api.tikhub.dev/api/v1"

# 百度智能云配置
BAIDU_API_KEY = os.environ.get("BAIDU_API_KEY", "cK5Q2yUY0L1OANgzWgynsevU")
BAIDU_SECRET_KEY = os.environ.get("BAIDU_SECRET_KEY", "s6d7S7kauN87s7vBPe1BjybQrCInPUg9")
BAIDU_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
BAIDU_ASR_URL = "https://vop.baidu.com/server_api"


class VideoExtractorV2:
    """全平台视频文案提取器"""
    
    def __init__(self):
        self.baidu_access_token = None
        self.baidu_token_expire_time = 0
    
    # ============== 平台识别 ==============
    def detect_platform(self, url: str) -> str:
        """识别链接所属平台"""
        url_lower = url.lower()
        
        if 'douyin.com' in url_lower:
            return 'douyin'
        elif 'kuaishou.com' in url_lower:
            return 'kuaishou'
        elif 'bilibili.com' in url_lower or 'b23.tv' in url_lower:
            return 'bilibili'
        elif 'xiaohongshu.com' in url_lower or 'xhslink.com' in url_lower:
            return 'xiaohongshu'
        else:
            return 'unknown'
    
    # ============== 抖音 ==============
    def get_douyin_video(self, share_url: str) -> Dict[str, Any]:
        """获取抖音视频信息"""
        headers = {
            "Authorization": f"Bearer {TIKHUB_API_KEY}",
            "Content-Type": "application/json"
        }
        
        url = f"{TIKHUB_BASE_URL}/douyin/web/fetch_one_video_by_share_url"
        params = {"share_url": share_url}
        
        try:
            print(f"[抖音] 获取视频信息...")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 200:
                aweme = data.get("data", {}).get("aweme_detail", {})
                video_info = aweme.get("video", {})
                
                # 提取音频URL
                audio_url = self._extract_douyin_audio(aweme)
                
                return {
                    "success": True,
                    "platform": "抖音",
                    "video_id": aweme.get("aweme_id", ""),
                    "title": aweme.get("desc", ""),
                    "author": aweme.get("author", {}).get("nickname", ""),
                    "duration": video_info.get("duration", 0) // 1000,
                    "statistics": aweme.get("statistics", {}),
                    "audio_url": audio_url,
                }
            else:
                return {"success": False, "error": data.get("message", "获取失败")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_douyin_audio(self, aweme: dict) -> str:
        """提取抖音音频URL"""
        music_info = aweme.get("music", {})
        play_url = music_info.get("play_url", {})
        if isinstance(play_url, dict):
            url_list = play_url.get("url_list", [])
            if url_list:
                print(f"[抖音] 使用music音频URL")
                return url_list[0]
        
        video_info = aweme.get("video", {})
        play_addr = video_info.get("play_addr", {})
        if isinstance(play_addr, dict):
            url_list = play_addr.get("url_list", [])
            if url_list:
                return url_list[0]
        return None
    
    # ============== 快手 ==============
    def get_kuaishou_video(self, share_url: str) -> Dict[str, Any]:
        """获取快手视频信息"""
        headers = {
            "Authorization": f"Bearer {TIKHUB_API_KEY}",
            "Content-Type": "application/json"
        }
        
        url = f"{TIKHUB_BASE_URL}/kuaishou/web/fetch_one_video_by_share_url"
        params = {"share_url": share_url}
        
        try:
            print(f"[快手] 获取视频信息...")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 200:
                video_data = data.get("data", {})
                
                audio_url = video_data.get("playUrl", "")
                
                return {
                    "success": True,
                    "platform": "快手",
                    "video_id": video_data.get("photoId", ""),
                    "title": video_data.get("caption", ""),
                    "author": video_data.get("userName", ""),
                    "duration": video_data.get("duration", 0) // 1000,
                    "statistics": {
                        "view_count": video_data.get("viewCount", 0),
                        "like_count": video_data.get("likeCount", 0),
                    },
                    "audio_url": audio_url,
                }
            else:
                return {"success": False, "error": data.get("message", "获取失败")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============== B站 ==============
    def get_bilibili_video(self, url: str) -> Dict[str, Any]:
        """获取B站视频信息"""
        headers = {
            "Authorization": f"Bearer {TIKHUB_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 提取BV号
        bv_match = re.search(r'BV[\w]+', url)
        av_match = re.search(r'av(\d+)', url)
        
        bvid = bv_match.group() if bv_match else None
        avid = av_match.group(1) if av_match else None
        
        if not bvid and not avid:
            return {"success": False, "error": "无法识别B站视频ID"}
        
        api_url = f"{TIKHUB_BASE_URL}/bilibili/web/fetch_one_video"
        params = {"bvid": bvid} if bvid else {"aid": avid}
        
        try:
            print(f"[B站] 获取视频信息... ({bvid or f'av{avid}'})")
            response = requests.get(api_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 200:
                v = data.get("data", {})
                
                return {
                    "success": True,
                    "platform": "B站",
                    "video_id": v.get("bvid", ""),
                    "title": v.get("title", ""),
                    "author": v.get("owner", {}).get("name", ""),
                    "duration": v.get("duration", 0),
                    "statistics": {
                        "view_count": v.get("stat", {}).get("view", 0),
                        "like_count": v.get("stat", {}).get("like", 0),
                        "comment_count": v.get("stat", {}).get("reply", 0),
                    },
                    "audio_url": None,  # B站音频需要额外处理
                    "desc": v.get("desc", ""),
                }
            else:
                return {"success": False, "error": data.get("message", "获取失败")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============== 小红书 ==============
    def get_xiaohongshu_note(self, share_url: str) -> Dict[str, Any]:
        """获取小红书笔记信息"""
        headers = {
            "Authorization": f"Bearer {TIKHUB_API_KEY}",
            "Content-Type": "application/json"
        }
        
        url = f"{TIKHUB_BASE_URL}/xiaohongshu/web/fetch_one_note_by_share_url"
        params = {"share_url": share_url}
        
        try:
            print(f"[小红书] 获取笔记信息...")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 200:
                note = data.get("data", {})
                video = note.get("video", {})
                
                # 提取视频音频URL
                audio_url = None
                if video:
                    stream = video.get("media", {}).get("stream", {})
                    h264_list = stream.get("h264", [])
                    if h264_list:
                        audio_url = h264_list[0].get("masterUrl", "")
                
                return {
                    "success": True,
                    "platform": "小红书",
                    "note_id": note.get("noteId", ""),
                    "title": note.get("title", ""),
                    "desc": note.get("desc", ""),
                    "author": note.get("user", {}).get("nickname", ""),
                    "type": "视频" if video else "图文",
                    "audio_url": audio_url,
                    "statistics": {
                        "like_count": note.get("interactInfo", {}).get("likedCount", 0),
                    },
                }
            else:
                return {"success": False, "error": data.get("message", "获取失败")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============== 百度语音识别 ==============
    def get_baidu_token(self) -> str:
        """获取百度Token"""
        if self.baidu_access_token and time.time() < self.baidu_token_expire_time:
            return self.baidu_access_token
        
        url = f"{BAIDU_TOKEN_URL}?grant_type=client_credentials&client_id={BAIDU_API_KEY}&client_secret={BAIDU_SECRET_KEY}"
        response = requests.post(url, timeout=10)
        data = response.json()
        
        if "access_token" in data:
            self.baidu_access_token = data["access_token"]
            self.baidu_token_expire_time = time.time() + data.get("expires_in", 2592000) - 3600
            return self.baidu_access_token
        raise Exception("获取Token失败")
    
    def convert_audio_for_baidu(self, audio_data: bytes) -> bytes:
        """转换音频为PCM格式"""
        try:
            print("[转换] 音频转PCM...")
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                f.write(audio_data)
                input_path = f.name
            
            output_path = input_path.replace('.mp3', '.pcm')
            
            cmd = ['ffmpeg', '-y', '-i', input_path, '-f', 's16le', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', output_path]
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            
            if result.returncode != 0:
                return None
            
            with open(output_path, 'rb') as f:
                pcm_data = f.read()
            
            os.unlink(input_path)
            os.unlink(output_path)
            
            print(f"[转换] 完成: {len(pcm_data)/1024:.2f}KB")
            return pcm_data
        except Exception as e:
            print(f"[转换] 失败: {e}")
            return None
    
    def speech_to_text(self, audio_data: bytes) -> str:
        """百度语音识别"""
        try:
            token = self.get_baidu_token()
            print(f"[百度] 识别中...")
            
            pcm_data = self.convert_audio_for_baidu(audio_data)
            if not pcm_data:
                return "[格式转换失败]"
            
            url = f"{BAIDU_ASR_URL}?cuid=video_extractor&token={token}&dev_pid=1537&format=pcm&rate=16000"
            headers = {"Content-Type": "audio/pcm; rate=16000"}
            
            response = requests.post(url, headers=headers, data=pcm_data, timeout=60)
            result = response.json()
            
            if result.get("err_no") == 0:
                print(f"[百度] 识别成功!")
                return result.get("result", [""])[0]
            return f"[识别失败: {result.get('err_msg')}]"
        except Exception as e:
            return f"[识别异常: {e}]"
    
    def download_audio(self, url: str) -> bytes:
        """下载音频"""
        print(f"[下载] 开始...")
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        
        data = b""
        for chunk in response.iter_content(chunk_size=8192):
            data += chunk
            if len(data) > 10 * 1024 * 1024:
                raise Exception("文件过大")
        
        print(f"[下载] 完成: {len(data)/1024:.2f}KB")
        return data
    
    # ============== 主入口 ==============
    def extract(self, url: str, include_audio: bool = False) -> Dict[str, Any]:
        """提取视频文案"""
        platform = self.detect_platform(url)
        print(f"[识别] 平台: {platform}")
        
        # 获取视频信息
        if platform == 'douyin':
            info = self.get_douyin_video(url)
        elif platform == 'kuaishou':
            info = self.get_kuaishou_video(url)
        elif platform == 'bilibili':
            info = self.get_bilibili_video(url)
        elif platform == 'xiaohongshu':
            info = self.get_xiaohongshu_note(url)
        else:
            info = {"success": False, "error": f"不支持的平台"}
        
        if not info.get("success"):
            return info
        
        # 提取台词
        if include_audio and info.get("audio_url"):
            try:
                audio_data = self.download_audio(info["audio_url"])
                info["audio_text"] = self.speech_to_text(audio_data)
            except Exception as e:
                info["audio_text"] = f"[提取失败: {e}]"
        elif include_audio:
            info["audio_text"] = "[暂不支持该平台台词提取]"
        
        return info


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="全平台视频文案提取器")
    parser.add_argument("url", help="视频链接")
    parser.add_argument("--audio", action="store_true", help="提取台词")
    
    args = parser.parse_args()
    
    extractor = VideoExtractorV2()
    result = extractor.extract(args.url, include_audio=args.audio)
    
    print("\n" + "="*50)
    print(json.dumps(result, ensure_ascii=False, indent=2))
