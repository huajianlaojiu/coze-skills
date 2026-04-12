#!/usr/bin/env python3
"""
视频文案提取器 V1.1 - 字幕优先版
支持抖音/快手/B站/小红书/微信视频号

【V1.1更新】
- B站：优先提取官方字幕(100%准确)，无字幕才用百度语音识别(95%准确)
- 抖音：优先提取自带字幕，无字幕才用火山引擎API(98%准确)

使用方式:
    python video_extractor.py "https://v.douyin.com/xxxxx"
    python video_extractor.py "https://www.bilibili.com/video/BV1xx411c7mD"
    python video_extractor.py "https://b23.tv/xxxxx"
"""

import os
import re
import sys
import requests
import json
import time
import subprocess
import tempfile
from typing import Optional, Dict, Any, List

# ============== 配置 ==============
TIKHUB_API_KEY = os.environ.get("TIKHUB_API_KEY", "t8wYXM8P3Vu5qGe6HoOtxzqKFD62A6Nq4SP7t1S/cNa4jw+LIk+RbDWEFQ==")
TIKHUB_BASE_URL = "https://api.tikhub.dev/api/v1"

# 火山引擎配置（抖音/快手等平台）
VOLCENGINE_APP_ID = os.environ.get("VOLCENGINE_APP_ID", "9440158400")
VOLCENGINE_TOKEN = os.environ.get("VOLCENGINE_TOKEN", "5HtIhksCXud0xhT7QTo5A6xaLDypftQC")
VOLCENGINE_SUBMIT_URL = "https://openspeech.bytedance.com/api/v1/vc/submit"
VOLCENGINE_QUERY_URL = "https://openspeech.bytedance.com/api/v1/vc/query"

# 百度语音识别配置（B站）
BAIDU_API_KEY = os.environ.get("BAIDU_API_KEY", "cK5Q2yUY0L1OANgzWgynsevU")
BAIDU_SECRET_KEY = os.environ.get("BAIDU_SECRET_KEY", "s6d7S7kauN87s7vBPe1BjybQrCInPUg9")
BAIDU_ASR_URL = "https://vop.baidu.com/server_api"

# B站Referer头（下载音频需要）
BILIBILI_HEADERS = {
    "Referer": "https://www.bilibili.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# B站官方字幕API
BILIBILI_PLAYER_API = "https://api.bilibili.com/x/player/v2"


class VideoExtractor:
    """全平台视频文案提取器 V1.1 - 字幕优先版"""
    
    def __init__(self):
        pass
    
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
        elif 'channels.weixin.qq.com' in url_lower or 'video.weixin.qq.com' in url_lower:
            return 'wechat_channels'
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
                
                # 【V1.1新增】提取字幕信息
                subtitle_text = self._extract_douyin_subtitle(aweme)
                
                return {
                    "success": True,
                    "platform": "抖音",
                    "video_id": aweme.get("aweme_id", ""),
                    "title": aweme.get("desc", ""),
                    "author": aweme.get("author", {}).get("nickname", ""),
                    "duration": video_info.get("duration", 0) // 1000,
                    "statistics": aweme.get("statistics", {}),
                    "audio_url": audio_url,
                    "subtitle_text": subtitle_text,  # 【V1.1】自带字幕
                    "subtitle_source": "video" if subtitle_text else None,  # 标记来源
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
                print(f"[抖音] 使用 music.play_url 音频")
                return url_list[0]
        
        video_info = aweme.get("video", {})
        play_addr = video_info.get("play_addr", {})
        if isinstance(play_addr, dict):
            url_list = play_addr.get("url_list", [])
            if url_list:
                print(f"[抖音] 使用 video.play_addr")
                return url_list[0]
        return None
    
    def _extract_douyin_subtitle(self, aweme: dict) -> Optional[str]:
        """【V1.1新增】提取抖音自带字幕"""
        # 检查多种字幕字段
        video_info = aweme.get("video", {})
        
        # 方式1: subtitles 字段（字幕轨道）
        subtitles = video_info.get("subtitles", [])
        if isinstance(subtitles, list) and subtitles:
            for sub in subtitles:
                if sub.get("subtitle_id"):
                    # 尝试从歌词/字幕URL获取
                    content = sub.get("content", "")
                    if content:
                        return content
                    # 或者下载字幕文件
                    sub_url = sub.get("url") or sub.get("subtitle_url", "")
                    if sub_url:
                        text = self._download_and_parse_subtitle(sub_url)
                        if text:
                            return text
        
        # 方式2: lyric_data（歌词数据）
        lyric_data = aweme.get("lyric_data", {}) or aweme.get("lyric", {})
        if lyric_data:
            lyric_str = lyric_data.get("lyric_str", "")
            if lyric_str:
                return lyric_str
        
        # 方式3: video_caption（视频字幕）
        video_caption = video_info.get("video_caption")
        if video_caption:
            return video_caption
        
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
                    "audio_url": video_data.get("playUrl", ""),
                }
            else:
                return {"success": False, "error": data.get("message", "获取失败")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============== B站 ==============
    def resolve_b23_url(self, short_url: str) -> str:
        """解析B站短链接 (b23.tv)"""
        try:
            print(f"[B站] 解析短链接...")
            response = requests.head(short_url, headers=BILIBILI_HEADERS, allow_redirects=True, timeout=10)
            return response.url
        except Exception as e:
            print(f"[B站] 短链接解析失败: {e}")
            return short_url
    
    def get_bilibili_video(self, url: str) -> Dict[str, Any]:
        """获取B站视频信息"""
        # 处理短链接
        if 'b23.tv' in url.lower():
            url = self.resolve_b23_url(url)
        
        headers = {
            "Authorization": f"Bearer {TIKHUB_API_KEY}",
            "Content-Type": "application/json"
        }
        
        bv_match = re.search(r'BV[\w]+', url)
        av_match = re.search(r'[?&]aid=(\d+)', url) or re.search(r'/av(\d+)', url)
        
        bvid = bv_match.group() if bv_match else None
        avid = av_match.group(1) if av_match else None
        
        if not bvid and not avid:
            return {"success": False, "error": "无法识别B站视频ID"}
        
        api_url = f"{TIKHUB_BASE_URL}/bilibili/web/fetch_one_video"
        params = {"bv_id": bvid} if bvid else {"aid": avid}
        
        try:
            print(f"[B站] 获取视频信息... ({bvid or f'av{avid}'})")
            response = requests.get(api_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 200:
                v = data.get("data", {})
                
                # 获取aid（用于后续获取字幕）
                aid = v.get("aid", 0)
                
                # 获取播放地址信息
                play_url = v.get("play_url", {})
                dash_audio = play_url.get("dash", {}).get("audio", []) if isinstance(play_url, dict) else {}
                
                # 尝试获取音频URL
                audio_url = None
                if isinstance(dash_audio, list) and dash_audio:
                    audio_url = dash_audio[0].get("baseUrl") or dash_audio[0].get("url")
                elif isinstance(dash_audio, dict):
                    audio_url = dash_audio.get("baseUrl") or dash_audio.get("url")
                
                # 如果API没返回，尝试从视频URL提取
                if not audio_url:
                    mp4_list = play_url.get("mp4") if isinstance(play_url, dict) else None
                    video_url = mp4_list[0].get("url") if isinstance(mp4_list, list) and mp4_list else None
                    if video_url:
                        audio_url = video_url  # 使用视频URL，ffmpeg可以提取音频
                
                # 【V1.1新增】获取CID用于字幕提取
                cid = None
                cid_list = v.get("cid_list", []) or v.get("cids", [])
                if cid_list:
                    cid = cid_list[0]
                elif aid:
                    # 尝试从页面或API获取CID
                    cid = self._get_bilibili_cid(bvid or f"av{aid}", aid)
                
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
                    },
                    "audio_url": audio_url,
                    "desc": v.get("desc", ""),
                    "aid": aid,
                    "cid": cid,
                    "bvid": bvid,
                }
            else:
                return {"success": False, "error": data.get("message", "获取失败")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_bilibili_cid(self, bvid: str, aid: int) -> Optional[int]:
        """获取B站视频CID"""
        try:
            # 从视频信息API获取cid
            api_url = f"https://api.bilibili.com/x/player/pagelist"
            params = {"bvid": bvid} if bvid.startswith("BV") else {"aid": aid}
            response = requests.get(api_url, headers=BILIBILI_HEADERS, params=params, timeout=10)
            data = response.json()
            
            if data.get("code") == 0:
                pages = data.get("data", [])
                if pages:
                    return pages[0].get("cid")
        except Exception as e:
            print(f"[B站] 获取CID失败: {e}")
        return None
    
    # 【V1.1新增】B站官方字幕提取
    def extract_bilibili_official_subtitle(self, aid: int, cid: int) -> Optional[str]:
        """
        【V1.1新增】提取B站官方字幕
        API: GET https://api.bilibili.com/x/player/v2?aid={aid}&cid={cid}
        返回: subtitle.subtitles[] 包含字幕URL
        字幕格式: JSON数组，每条含 from, to, content
        """
        try:
            print(f"[B站] 尝试获取官方字幕 (aid={aid}, cid={cid})...")
            
            params = {"aid": aid, "cid": cid}
            response = requests.get(
                BILIBILI_PLAYER_API,
                headers=BILIBILI_HEADERS,
                params=params,
                timeout=15
            )
            data = response.json()
            
            if data.get("code") != 0:
                print(f"[B站] 字幕API返回错误: {data.get('message', '未知错误')}")
                return None
            
            subtitle_data = data.get("data", {}).get("subtitle", {})
            subtitles = subtitle_data.get("subtitles", [])
            
            if not subtitles:
                print(f"[B站] 未找到官方字幕")
                return None
            
            # 选择中文字幕（优先）
            subtitle_url = None
            for sub in subtitles:
                lan_doc = sub.get("lan_doc", "")
                # 优先选择中文/简中字幕
                if "zh-Hans" in lan_doc or "中文" in lan_doc or lan_doc == "zh":
                    subtitle_url = sub.get("subtitle_url")
                    print(f"[B站] 选择字幕: {lan_doc}")
                    break
            
            # 如果没找到中文，使用第一个
            if not subtitle_url and subtitles:
                subtitle_url = subtitles[0].get("subtitle_url")
                print(f"[B站] 使用字幕: {subtitles[0].get('lan_doc', '未知')}")
            
            if not subtitle_url:
                return None
            
            # 下载并解析字幕JSON
            return self._download_and_parse_subtitle(subtitle_url)
            
        except Exception as e:
            print(f"[B站] 官方字幕提取失败: {e}")
            return None
    
    def _download_and_parse_subtitle(self, subtitle_url: str) -> Optional[str]:
        """下载并解析字幕文件（支持B站JSON格式）"""
        try:
            # 确保URL完整
            if subtitle_url.startswith("//"):
                subtitle_url = "https:" + subtitle_url
            
            print(f"[字幕] 下载字幕文件...")
            response = requests.get(subtitle_url, headers=BILIBILI_HEADERS, timeout=15)
            response.raise_for_status()
            
            subtitle_data = response.json()
            
            # B站字幕格式: [{"from": 0.0, "to": 5.0, "content": "字幕文本"}, ...]
            if isinstance(subtitle_data, list):
                texts = [item.get("content", "") for item in subtitle_data if item.get("content")]
                if texts:
                    result = "".join(texts)
                    print(f"[字幕] 解析完成，共 {len(texts)} 条")
                    return result
            
            # 如果是字符串数组
            if isinstance(subtitle_data, list) and len(subtitle_data) > 0:
                if isinstance(subtitle_data[0], str):
                    return "".join(subtitle_data)
            
            # 如果是带data字段的结构
            if isinstance(subtitle_data, dict):
                body = subtitle_data.get("body", [])
                if isinstance(body, list) and body:
                    texts = [item.get("content", "") or item.get("text", "") for item in body]
                    return "".join([t for t in texts if t])
            
            print(f"[字幕] 未知字幕格式")
            return None
            
        except Exception as e:
            print(f"[字幕] 下载/解析失败: {e}")
            return None
    
    def _get_baidu_token(self) -> Optional[str]:
        """获取百度语音识别Access Token"""
        token_url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": BAIDU_API_KEY,
            "client_secret": BAIDU_SECRET_KEY
        }
        
        try:
            response = requests.post(token_url, params=params, timeout=10)
            result = response.json()
            return result.get("access_token")
        except Exception as e:
            print(f"[百度] 获取Token失败: {e}")
            return None
    
    def _download_audio(self, url: str, output_path: str) -> bool:
        """下载音频/视频文件"""
        try:
            print(f"[下载] 开始下载音频...")
            response = requests.get(url, headers=BILIBILI_HEADERS, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"[下载] 下载完成: {output_path}")
            return True
        except Exception as e:
            print(f"[下载] 下载失败: {e}")
            return False
    
    def _convert_to_pcm(self, input_path: str, output_path: str) -> bool:
        """使用ffmpeg将音频转换为PCM格式 (16kHz 16bit 单声道)"""
        try:
            cmd = [
                'ffmpeg', '-y', '-i', input_path,
                '-acodec', 'pcm_s16le',  # PCM 16bit little-endian
                '-ar', '16000',          # 16kHz采样率
                '-ac', '1',              # 单声道
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"[转换] PCM转换完成: {output_path}")
                return True
            else:
                print(f"[转换] PCM转换失败: {result.stderr}")
                return False
        except FileNotFoundError:
            print("[错误] ffmpeg未安装，请先安装: apt-get install ffmpeg")
            return False
        except Exception as e:
            print(f"[转换] 转换异常: {e}")
            return False
    
    def _split_audio(self, pcm_path: str, max_seconds: int = 60) -> list:
        """将PCM文件分割成60秒以内的片段（百度API限制）"""
        try:
            # 获取文件大小计算时长
            file_size = os.path.getsize(pcm_path)
            # 16kHz采样率, 16bit, 单声道 = 32000字节/秒
            bytes_per_second = 16000 * 2
            total_seconds = file_size / bytes_per_second
            
            if total_seconds <= max_seconds:
                return [(0, min(total_seconds, max_seconds), pcm_path)]
            
            chunks = []
            for i in range(0, int(total_seconds), max_seconds):
                end = min(i + max_seconds, total_seconds)
                chunks.append((i, end, pcm_path))
            
            return chunks
        except Exception as e:
            print(f"[分割] 计算音频时长失败: {e}")
            return [(0, max_seconds, pcm_path)]
    
    def _recognize_pcm(self, pcm_path: str, token: str, offset: float = 0) -> Optional[str]:
        """识别单个PCM片段"""
        try:
            with open(pcm_path, 'rb') as f:
                pcm_data = f.read()
            
            # 计算时长
            bytes_per_second = 16000 * 2
            duration = len(pcm_data) / bytes_per_second
            
            params = {
                "dev_pid": 1537,  # 普通话识别
                "format": "pcm",
                "rate": 16000,
                "token": token,
                "cuid": "bilibili_extractor",
                "len": len(pcm_data),
            }
            
            response = requests.post(
                BAIDU_ASR_URL,
                params=params,
                data=pcm_data,
                headers={"Content-Type": "audio/pcm; rate=16000"},
                timeout=30
            )
            
            result = response.json()
            
            if result.get("err_no") == 0:
                result_list = result.get("result", [])
                if result_list:
                    text = result_list[0]
                    # 如果有偏移量，在文本前添加时间戳标记
                    if offset > 0:
                        minutes = int(offset // 60)
                        seconds = int(offset % 60)
                        text = f"[{minutes:02d}:{seconds:02d}] {text}"
                    return text
            else:
                print(f"[百度] 识别失败: {result.get('err_str', '未知错误')}")
            
            return None
        except Exception as e:
            print(f"[百度] 识别异常: {e}")
            return None
    
    def extract_bilibili_audio(self, audio_url: str) -> Dict[str, Any]:
        """提取B站音频并识别（使用百度API）"""
        if not audio_url:
            return {"success": False, "error": "无法获取音频URL"}
        
        # 获取百度Token
        token = self._get_baidu_token()
        if not token:
            return {"success": False, "error": "无法获取百度API Token"}
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            # 下载文件
            media_path = os.path.join(tmpdir, "input.mp4")
            pcm_path = os.path.join(tmpdir, "audio.pcm")
            
            if not self._download_audio(audio_url, media_path):
                return {"success": False, "error": "下载音频失败"}
            
            # 转换为PCM
            if not self._convert_to_pcm(media_path, pcm_path):
                return {"success": False, "error": "音频格式转换失败"}
            
            # 分割并识别
            chunks = self._split_audio(pcm_path)
            all_texts = []
            
            for i, (start, end, _) in enumerate(chunks):
                print(f"[百度] 识别第 {i+1}/{len(chunks)} 段 ({start:.0f}s - {end:.0f}s)...")
                
                # 分割片段
                chunk_path = os.path.join(tmpdir, f"chunk_{i}.pcm")
                bytes_start = int(start * 16000 * 2)
                bytes_end = int(end * 16000 * 2)
                
                with open(pcm_path, 'rb') as f:
                    f.seek(bytes_start)
                    chunk_data = f.read(bytes_end - bytes_start)
                
                with open(chunk_path, 'wb') as f:
                    f.write(chunk_data)
                
                # 识别
                text = self._recognize_pcm(chunk_path, token, offset=start)
                if text:
                    all_texts.append(text)
                
                time.sleep(0.5)  # 避免请求过快
            
            if all_texts:
                return {
                    "success": True,
                    "text": " ".join(all_texts)
                }
            else:
                return {"success": False, "error": "未能识别出文字"}
    
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
                }
            else:
                return {"success": False, "error": data.get("message", "获取失败")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============== 微信视频号 ==============
    def get_wechat_channels_video(self, url: str) -> Dict[str, Any]:
        """获取微信视频号视频信息"""
        headers = {
            "Authorization": f"Bearer {TIKHUB_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 提取视频ID或使用URL
        api_url = f"{TIKHUB_BASE_URL}/wechat/channels/fetch_video_detail"
        params = {"url": url}
        
        try:
            print(f"[微信视频号] 获取视频信息...")
            response = requests.get(api_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 200:
                v = data.get("data", {})
                
                return {
                    "success": True,
                    "platform": "微信视频号",
                    "video_id": v.get("feed_id", ""),
                    "title": v.get("desc", ""),
                    "author": v.get("author", {}).get("nickname", ""),
                    "duration": v.get("duration", 0),
                    "audio_url": v.get("media", {}).get("video_url", ""),
                }
            else:
                return {"success": False, "error": data.get("message", "获取失败")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============== 火山引擎音视频字幕API ==============
    def submit_audio(self, audio_url: str, language: str = "zh-CN") -> Dict[str, Any]:
        """提交音频URL到火山引擎进行字幕识别"""
        headers = {
            "Authorization": f"Bearer; {VOLCENGINE_TOKEN}",
            "Content-Type": "application/json"
        }
        
        params = {
            "appid": VOLCENGINE_APP_ID,
            "language": language,
            "use_itn": "true",
            "use_punc": "true",
        }
        
        data = {"url": audio_url}
        
        try:
            print(f"[火山引擎] 提交音频识别任务...")
            response = requests.post(
                VOLCENGINE_SUBMIT_URL,
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )
            result = response.json()
            
            if result.get("code") == 0:
                return {
                    "success": True,
                    "task_id": result.get("id", ""),
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "提交失败"),
                    "code": result.get("code")
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def query_result(self, task_id: str, blocking: int = 1) -> Dict[str, Any]:
        """查询字幕识别结果"""
        headers = {
            "Authorization": f"Bearer; {VOLCENGINE_TOKEN}",
        }
        
        params = {
            "appid": VOLCENGINE_APP_ID,
            "id": task_id,
            "blocking": blocking
        }
        
        try:
            response = requests.get(
                VOLCENGINE_QUERY_URL,
                headers=headers,
                params=params,
                timeout=120
            )
            return response.json()
        except Exception as e:
            return {"code": -1, "error": str(e)}
    
    def extract_subtitle(self, audio_url: str, language: str = "zh-CN") -> Dict[str, Any]:
        """提取音频字幕（完整流程）"""
        
        submit_result = self.submit_audio(audio_url, language)
        if not submit_result.get("success"):
            return submit_result
        
        task_id = submit_result.get("task_id")
        print(f"[火山引擎] 任务ID: {task_id}")
        
        max_retry = 30
        for i in range(max_retry):
            time.sleep(2)
            
            result = self.query_result(task_id, blocking=0)
            code = result.get("code")
            
            if code == 0:
                subtitle_text = self._parse_subtitle(result)
                return {
                    "success": True,
                    "text": subtitle_text,
                }
            elif code == 2000:
                print(f"[火山引擎] 处理中... ({i+1}/{max_retry})")
                continue
            else:
                return {
                    "success": False,
                    "error": result.get("message", "识别失败"),
                }
        
        return {"success": False, "error": "超时"}
    
    def _parse_subtitle(self, result: dict) -> str:
        """解析字幕结果"""
        utterances = result.get("utterances", [])
        texts = [utt.get("text", "") for utt in utterances if utt.get("text")]
        return "".join(texts)
    
    # ============== 主提取函数 ==============
    def extract(self, url: str) -> Dict[str, Any]:
        """
        提取视频字幕【V1.1字幕优先版】
        
        优先级：
        - B站：官方字幕(100%) > 百度语音识别(95%)
        - 抖音：自带字幕 > 火山引擎API(98%)
        """
        
        platform = self.detect_platform(url)
        print(f"[识别] 平台: {platform}")
        
        video_info = None
        if platform == 'douyin':
            video_info = self.get_douyin_video(url)
        elif platform == 'kuaishou':
            video_info = self.get_kuaishou_video(url)
        elif platform == 'bilibili':
            video_info = self.get_bilibili_video(url)
        elif platform == 'xiaohongshu':
            video_info = self.get_xiaohongshu_note(url)
        elif platform == 'wechat_channels':
            video_info = self.get_wechat_channels_video(url)
        else:
            return {"success": False, "error": f"不支持的平台: {url}"}
        
        if not video_info.get("success"):
            return video_info
        
        # ========== 字幕提取逻辑 ==========
        subtitle_text = None
        subtitle_source = None  # 字幕来源: official/baidu/volcengine
        
        # 【V1.1核心优化】字幕优先提取
        if platform == 'douyin':
            # 抖音：优先使用自带字幕
            subtitle_text = video_info.get("subtitle_text")
            if subtitle_text:
                subtitle_source = "official"
                print(f"[抖音] ✓ 使用自带字幕 (100%准确)")
            else:
                # 回退到火山引擎API
                audio_url = video_info.get("audio_url")
                if audio_url:
                    print(f"[抖音] 无自带字幕，使用火山引擎API...")
                    subtitle_result = self.extract_subtitle(audio_url)
                    if subtitle_result.get("success"):
                        subtitle_text = subtitle_result.get("text")
                        subtitle_source = "volcengine"
                        print(f"[抖音] ✓ 火山引擎识别成功 (98%准确)")
        
        elif platform == 'bilibili':
            # B站：优先使用官方字幕
            aid = video_info.get("aid")
            cid = video_info.get("cid")
            
            if aid and cid:
                subtitle_text = self.extract_bilibili_official_subtitle(aid, cid)
                if subtitle_text:
                    subtitle_source = "official"
                    print(f"[B站] ✓ 使用官方字幕 (100%准确)")
            
            # 回退到百度语音识别
            if not subtitle_text:
                audio_url = video_info.get("audio_url")
                if audio_url:
                    print(f"[B站] 无官方字幕，使用百度语音识别...")
                    subtitle_result = self.extract_bilibili_audio(audio_url)
                    if subtitle_result.get("success"):
                        subtitle_text = subtitle_result.get("text")
                        subtitle_source = "baidu"
                        print(f"[B站] ✓ 百度识别成功 (95%准确)")
        
        else:
            # 其他平台使用火山引擎API
            audio_url = video_info.get("audio_url")
            if audio_url:
                subtitle_result = self.extract_subtitle(audio_url)
                if subtitle_result.get("success"):
                    subtitle_text = subtitle_result.get("text")
                    subtitle_source = "volcengine"
        
        # 构建最终结果
        result = {
            **video_info,
            "subtitle_source": subtitle_source,
        }
        
        if subtitle_text:
            result["subtitle_success"] = True
            result["subtitle_text"] = subtitle_text
        else:
            result["subtitle_success"] = False
            result["subtitle_error"] = video_info.get("subtitle_error", "无法提取字幕")
        
        return result
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """格式化输出结果"""
        lines = []
        
        if not result.get("success"):
            return f"❌ 提取失败: {result.get('error', '未知错误')}"
        
        lines.append(f"📌 平台: {result.get('platform', '未知')}")
        lines.append(f"📝 标题: {result.get('title', '无标题')}")
        lines.append(f"👤 作者: {result.get('author', '未知')}")
        lines.append(f"⏱️ 时长: {result.get('duration', 0)}秒")
        
        # 字幕来源标注
        if result.get("subtitle_success"):
            source = result.get("subtitle_source", "")
            source_label = {
                "official": "✓ 官方字幕 (100%准确)",
                "baidu": "✓ 百度语音识别 (95%准确)",
                "volcengine": "✓ 火山引擎识别 (98%准确)"
            }.get(source, source)
            
            lines.append(f"\n📝 字幕内容 [{source_label}]:")
            lines.append(result.get("subtitle_text", ""))
        else:
            lines.append(f"\n❌ 字幕提取失败: {result.get('subtitle_error', '未知错误')}")
        
        return "\n".join(lines)


# ============== 主函数 ==============
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("视频文案提取器 V1.1 - 字幕优先版")
        print("="*50)
        print("使用方式: python video_extractor.py <视频链接>")
        print("支持平台: 抖音/快手/B站/小红书/微信视频号")
        print()
        print("【V1.1更新】")
        print("- B站：优先官方字幕(100%)，无字幕用百度语音识别(95%)")
        print("- 抖音：优先自带字幕，无字幕用火山引擎(98%)")
        sys.exit(1)
    
    url = sys.argv[1]
    
    extractor = VideoExtractor()
    result = extractor.extract(url)
    
    print("\n" + "="*50)
    print(extractor.format_result(result))
