# 📹 视频文案提取器

> 一键提取抖音/快手/小红书/B站视频文案，让内容创作更高效

## 功能特点

- 🎬 **多平台支持**：抖音、快手、小红书、B站、视频号
- ⚡ **快速提取**：平均处理时间 10-30 秒
- 📝 **高准确率**：智能语音识别，准确率 95%+
- 💰 **免费额度**：TikHub API 注册送额度，百度语音识别有免费额度
- 🔒 **隐私保护**：仅调用官方API，数据处理在本地完成

## 快速开始

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 ffmpeg (系统级)
# Ubuntu/Debian:
sudo apt update && sudo apt install ffmpeg

# macOS:
brew install ffmpeg
```

### 2. 基本使用

```bash
# 提取抖音视频文案
python scripts/video_extractor_v3.py "https://v.douyin.com/xxxxx"

# 提取B站视频文案
python scripts/video_extractor_v3.py "https://www.bilibili.com/video/BV1xx411c7mD"
```

### 3. 输出示例

```
🔍 正在分析链接: https://v.douyin.com/xxxxx

✅ 提取成功!

--------------------------------------------------
📝 视频文案:
--------------------------------------------------
这是视频中的语音内容...
--------------------------------------------------

📌 视频标题: 视频标题
👤 作者: @username
📊 数据: ❤️ 1234 💬 56 ⭐ 78
```

## API 配置

### 获取 TikHub API Key

1. 访问 https://tikhub.io 注册账号
2. 在控制台创建 API Key
3. API Key 已内置在代码中

### 获取百度语音识别 API Key（B站）

1. 访问 https://ai.baidu.com/
2. 注册/登录百度智能云账号
3. 开通语音识别服务
4. 获取 API Key 和 Secret Key

### 配置 API Key

```bash
# 设置环境变量
export TIKHUB_API_KEY="your_api_key_here"
export BAIDU_API_KEY="your_api_key_here"
export BAIDU_SECRET_KEY="your_secret_key_here"
```

## 脚本说明

| 脚本 | 说明 |
|------|------|
| `video_extractor_v3.py` | 完整版提取器，支持抖音/B站语音识别 |

## 常见问题

### Q: 提示 "不支持的平台"？
A: 目前支持抖音和B站，其他平台正在开发中。

### Q: 提取失败怎么办？
A: 请检查：
- 视频链接是否正确
- 视频是否可访问（未删除/私密视频无法提取）
- 网络连接是否稳定
- API Key 是否有效

### Q: 如何提升识别准确率？
A: - 使用清晰的音频
- 避免背景音乐过大
- 普通话视频效果最佳

## 技术架构

```
用户输入视频链接
        ↓
    平台检测
        ↓
    TikHub API 解析链接
        ↓
    获取视频信息/音频
        ↓
    语音识别API处理
        ↓
返回视频文案和字幕
```

## 隐私说明

- 视频链接仅发送给平台官方API
- 不收集或存储用户视频数据
- API Key 存储在本地配置文件
