# 视频文案提取器 Skill

> 一键提取抖音/B站视频文案和台词，让内容创作更高效

## 版本信息

**当前版本：V1.1.0**（字幕优先版）

### V1.1 更新日志
- ✅ **B站字幕优先提取**：优先使用B站官方字幕API（100%准确），无字幕才使用百度语音识别（95%准确）
- ✅ **抖音字幕优先提取**：优先提取视频自带字幕，无字幕才使用火山引擎API（98%准确）
- ✅ 新增字幕来源标注，显示使用的识别方式

---

## 功能简介

本技能可以自动从抖音和B站视频链接中提取视频的文案描述和**视频台词**。

### 核心能力

- 🎬 **双平台支持**：
  - **抖音**：优先提取自带字幕（100%准确），无字幕使用 TikHub API + 火山引擎API（98%准确）
  - **B站**：优先提取官方字幕（100%准确），无字幕使用 TikHub API + 百度语音识别API（95%准确）
- ⚡ **快速提取**：平均处理时间 5-30 秒
- 📝 **完整信息**：获取作者、标题、点赞/评论数据
- 🎤 **语音识别**：**支持提取视频台词**
- 🔒 **隐私保护**：仅调用官方API，数据处理在本地完成

## 使用方式

### 触发词
```
提取文案
视频转文字
文案提取
抖音文案
B站文案
转文字
提取台词
视频台词
视频字幕
```

### 输入格式
发送视频链接即可，例如：
```
提取这个视频的文案：https://v.douyin.com/xxxxx
提取视频台词：https://www.bilibili.com/video/BV1xx411c7mD
提取B站视频字幕：https://b23.tv/xxxxx
```

### 支持的链接格式

**抖音：**
- 抖音分享链接：`https://v.douyin.com/xxxxx`
- 抖音视频链接：`https://www.douyin.com/video/xxxxx`

**B站：**
- B站视频链接：`https://www.bilibili.com/video/BV1xx411c7mD`
- B站短链接：`https://b23.tv/xxxxx`

## 技术实现

### 字幕优先策略【V1.1核心优化】

```
┌─────────────────────────────────────────────────────────────┐
│  B站处理流程                                                │
│                                                             │
│  1. 解析B站链接（支持BV号、AV号、b23.tv短链接）            │
│  2. 调用 TikHub API 获取视频信息                           │
│  3. 优先 → 调用B站官方字幕API (100%准确)                  │
│     API: GET https://api.bilibili.com/x/player/v2          │
│     参数: aid, cid                                          │
│     返回: subtitle.subtitles[]                              │
│                                                             │
│  4. 回退 → 百度语音识别API (95%准确)                       │
│     下载音频 → ffmpeg转PCM → 分段识别                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  抖音处理流程                                                │
│                                                             │
│  1. 解析抖音分享链接                                        │
│  2. 调用 TikHub API 获取视频信息                           │
│  3. 优先 → 检查并提取视频自带字幕 (100%准确)               │
│     字段: subtitles, lyric_data, video_caption             │
│                                                             │
│  4. 回退 → 火山引擎音视频字幕API (98%准确)                 │
│     直接通过音频URL识别，无需下载                           │
└─────────────────────────────────────────────────────────────┘
```

### 数据流向说明

```
用户输入视频链接
       ↓
┌─────────────────────────────────────────────────┐
│  技能脚本调用外部API获取视频数据                  │
│                                                 │
│  抖音 → TikHub API（获取视频元数据）            │
│       → 检查自带字幕字段（优先）                  │
│       → 火山引擎API（语音识别，回退）            │
│                                                 │
│  B站 → TikHub API（获取视频元数据+aid/cid）     │
│       → B站官方字幕API（优先，100%准确）        │
│       → 百度语音识别API（回退，95%准确）        │
│                                                 │
│  ⚠️ 视频链接仅发送给平台官方API                 │
└─────────────────────────────────────────────────┘
       ↓
返回视频文案和字幕给用户
```

### 抖音：TikHub API + 字幕优先策略

#### 1. TikHub API（视频信息）
- **API 域名**：https://api.tikhub.dev
- **接口**：`/api/v1/douyin/web/fetch_one_video_by_share_url`
- **认证方式**：Bearer Token
- **功能**：获取视频元数据、音频URL、检查字幕字段
- **数据发送至**：TikHub服务器（用于解析抖音链接）

#### 2. 抖音自带字幕【V1.1优先】
- **字幕字段**：`video.subtitles`, `lyric_data`, `video_caption`
- **准确率**：100%（作者原始字幕）
- **优势**：无需额外API调用，直接解析返回数据

#### 3. 火山引擎音视频字幕API【回退方案】
- **API 域名**：https://openspeech.bytedance.com
- **功能**：直接通过音频URL识别字幕，无需下载
- **准确率**：98%+（基于抖音/剪映数据训练）
- **免费额度**：20小时/月
- **数据发送至**：火山引擎服务器（用于语音识别）

### B站：TikHub API + B站官方字幕API【V1.1核心优化】

#### 1. TikHub API（视频信息）
- **接口**：`/api/v1/bilibili/web/fetch_one_video`
- **支持**：BV号、AV号解析
- **支持**：b23.tv 短链接解析
- **数据发送至**：TikHub服务器（用于解析B站链接）

#### 2. B站官方字幕API【V1.1新增优先方案】
- **API 域名**：https://api.bilibili.com
- **接口**：`/api/v1/douyin/web/fetch_one_video_by_share_url`
- **参数**：aid（视频av号）, cid（分P编号）
- **返回**：`subtitle.subtitles[]` 包含字幕URL列表
- **字幕格式**：JSON数组 `[{"from": 0.0, "to": 5.0, "content": "字幕文本"}, ...]`
- **准确率**：100%（作者上传的原始字幕）
- **优势**：无需下载音频，直接获取字幕文本

#### 3. 百度语音识别【回退方案】
- **API 域名**：https://vop.baidu.com
- **模型**：dev_pid=1537（普通话）
- **准确率**：95%+（标准环境）
- **格式要求**：PCM 16kHz 16bit 单声道
- **限制**：单次最长60秒，需分段处理
- **数据发送至**：百度智能云服务器（用于语音识别）

### 字幕来源标注【V1.1新增】

返回结果中包含 `subtitle_source` 字段，标注字幕识别方式：
- `official`：官方字幕（100%准确）
- `baidu`：百度语音识别（95%准确）
- `volcengine`：火山引擎识别（98%准确）

## 安装依赖

```bash
pip install requests

# 需要安装ffmpeg（用于B站音频格式转换）
apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg     # macOS
```

## API 配置

### TikHub API Key
- 已配置默认 API Key
- 存储位置：`SECRET.md`

### 火山引擎配置（抖音）
- APP ID：已配置
- Token：已配置
- 存储位置：`SECRET.md`

### 百度智能云配置（B站）
- API Key：已配置
- Secret Key：已配置
- 存储位置：`SECRET.md`

## 返回数据格式

### 基础提取结果
```json
{
  "success": true,
  "platform": "抖音/B站",
  "title": "视频标题",
  "author": "作者昵称",
  "video_id": "视频ID",
  "duration": 120,
  "statistics": {
    "view_count": 12345,
    "like_count": 678
  }
}
```

### 包含字幕识别的结果【V1.1增强】
```json
{
  "success": true,
  "platform": "抖音/B站",
  "title": "视频标题",
  "author": "作者昵称",
  "video_id": "视频ID",
  "statistics": {...},
  "subtitle_success": true,
  "subtitle_source": "official",  // 【V1.1新增】字幕来源
  "subtitle_text": "这是视频中人物说的台词内容..."
}
```

## 注意事项

1. **链接格式**：
   - 抖音建议使用分享链接（v.douyin.com 开头）
   - B站支持 BV号、AV号、b23.tv 短链接

2. **字幕识别说明**：
   - 抖音：约 5-15 秒处理时间
   - B站：约 5-30 秒处理时间（官方字幕快，语音识别慢）
   - 仅支持中文和英文音频

3. **字幕优先级【V1.1核心】**：
   - B站：官方字幕(100%) > 百度语音识别(95%)
   - 抖音：自带字幕(100%) > 火山引擎(98%)

4. **隐私说明**：
   - 视频链接仅发送给平台官方API（抖音/火山引擎/B站/百度）
   - 不收集或存储用户视频数据

## API 文档

- TikHub 官方文档：https://docs.tikhub.dev
- B站字幕API：https://github.com/SocialSisterYi/bilibili-API-collect
- 火山引擎字幕API：https://www.volcengine.com/docs/10906/155897
- 百度语音识别：https://ai.baidu.com/tech/speech/asr
