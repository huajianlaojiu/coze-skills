# 抖音视频文案提取 API 调研报告

## 一、调研背景

我们的"视频文案提取器"技能目前使用的第三方API已失效，需要寻找可用的技术方案让技能恢复正常。豆包是抖音自家的AI，理论上应该支持抖音视频文案提取，因此本次调研重点考察火山引擎和TikHub的方案。

## 二、方案对比

### 方案一：火山引擎豆包

#### 2.1.1 视频点播长视频理解

**官方文档**：https://www.volcengine.com/docs/4/1478242

| 项目 | 说明 |
|------|------|
| 功能 | 基于豆包大模型的多模态视频理解，支持画面理解、音频理解、多模态理解三种模式 |
| **关键限制** | **不支持直接输入抖音链接**，需要先将视频上传至火山引擎视频点播服务，获取 Vid 后才能调用 |
| 输入要求 | 视频需上传至视频点播空间，获取 Vid 或 FileName |
| 最长支持 | 2小时视频 |
| 免费额度 | 每日200万Tokens（豆包大模型） |

**开通步骤**：
1. 注册火山引擎账号并完成实名认证
2. 开通视频点播服务并创建空间
3. 将视频上传至点播空间，获取 Vid
4. 开通豆包大模型，创建推理接入点，获取 Endpoint ID
5. 开通语音识别服务，获取 APP ID

**计费组成**：
- 截图费用
- 大模型流式语音识别费用
- 豆包大模型费用（0.15-24元/百万token）

#### 2.1.2 豆包语音妙记 API

**官方文档**：https://www.volcengine.com/docs/6561/1798094

| 项目 | 说明 |
|------|------|
| 功能 | 音视频语音转写，支持字幕生成、全文总结、章节总结等 |
| **关键限制** | **不支持直接输入抖音链接**，需要提供文件 URL |
| 支持格式 | 视频：MP4、AVI、MKV、MOV、FLV、WMV；音频：MP3、WAV、AAC、FLAC、OGG |
| 文件限制 | 文件大小 < 1GB，时长 < 2小时 |
| 计费方式 | 打包计费或按功能分别计费 |

#### 2.1.3 结论

**火山引擎方案不满足需求**。虽然豆包功能强大，但**不支持直接输入抖音链接**。需要先下载视频、上传至火山引擎，这个流程对于我们的技能来说太复杂，且用户无法接受。

---

### 方案二：TikHub API（推荐）

**官网**：https://tikhub.io

| 项目 | 说明 |
|------|------|
| 功能 | 提供抖音、TikTok、小红书等16+平台的社交媒体数据API |
| 抖音接口 | 支持获取视频信息、用户信息、评论、搜索等数据 |
| **关键优势** | **支持直接输入抖音链接或视频ID获取数据** |
| 价格 | 抖音接口约 **0.0015美元/次**（非常便宜） |
| 免费额度 | 注册送0.05美元，每日签到可获取免费额度（不过期） |
| 接口稳定性 | Web接口可能不稳定，建议优先使用App V3 API |

#### 2.2.1 核心接口

**TikTok/Douyin App V3 API**：
```python
# 获取单个视频信息
import requests

url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_one_video"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
params = {"aweme_id": "7350810998023949599"}

response = requests.get(url, headers=headers, params=params)
data = response.json()

# 视频文案在 data['data']['desc'] 字段
print(f"文案: {data['data']['desc']}")
```

**抖音 Web API**：
```python
# 通过抖音分享链接获取视频信息
url = "https://api.tikhub.io/api/v1/douyin/web/fetch_one_video"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
params = {"share_url": "https://v.douyin.com/xxxxx"}

response = requests.get(url, headers=headers, params=params)
```

#### 2.2.2 接入步骤

1. **注册账号**：访问 https://tikhub.io 注册账号
2. **获取API Key**：控制台 → API密钥 → 创建密钥
3. **安装Skill**：使用小龙虾(tikomni)安装 `@tikomni/skills list` skill
4. **配置密钥**：将API Key配置到技能中
5. **测试调用**：传入抖音链接获取视频文案

---

### 方案三：无极引擎（备选）

**官网**：https://agi.wujie-engine.com/tool

| 服务 | 价格 |
|------|------|
| 视频文案提取 | 0.02元/次 |
| 获取抖音视频信息 | 0.1元/次 |
| 获取抖音博主信息 | 0.01元/次 |

价格适中，但接口稳定性不明。

---

## 三、方案对比总结

| 对比项 | 火山引擎 | TikHub | 无极引擎 |
|--------|----------|--------|----------|
| 支持抖音链接 | ❌ 不支持 | ✅ 支持 | ✅ 支持 |
| 直接获取文案 | ❌ 需上传视频 | ✅ 可直接获取 | ✅ 可直接获取 |
| 注册便捷性 | 需实名认证 | 简单注册 | 简单注册 |
| 价格 | 按token计费 | 0.0015美元/次 | 0.02元/次 |
| 免费额度 | 每日200万Tokens | 注册送0.05美元 | 无 |
| 接口稳定性 | 高 | 中等 | 一般 |

## 四、推荐方案

### 首选：TikHub API

**推荐理由**：
1. ✅ **支持直接输入抖音链接**，无需下载和上传视频
2. ✅ **价格便宜**，0.0015美元/次，约0.01元人民币/次
3. ✅ **有免费额度**，注册送0.05美元
4. ✅ 接入相对简单，支持扣子平台插件方式接入

**接入方式**：
1. 注册 TikHub 账号
2. 创建 API Key
3. 在扣子平台创建云侧插件，配置 TikHub API
4. 或安装小龙虾 skill `@tikomni/skills list`

---

## 五、测试代码示例

### 5.1 TikHub API 测试

```python
import requests
import json

# TikHub API 配置
API_KEY = "YOUR_TIKHUB_API_KEY"
BASE_URL = "https://api.tikhub.io/api/v1"

def get_douyin_video_info(share_url: str) -> dict:
    """
    通过抖音分享链接获取视频信息
    
    Args:
        share_url: 抖音分享链接，如 https://v.douyin.com/xxxxx
    
    Returns:
        包含视频信息的字典
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 使用抖音Web API
    url = f"{BASE_URL}/douyin/web/fetch_one_video"
    params = {"share_url": share_url}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 200:
            video_data = data.get("data", {})
            return {
                "success": True,
                "title": video_data.get("desc", ""),  # 视频文案/标题
                "video_id": video_data.get("aweme_id", ""),
                "author": video_data.get("author", {}).get("nickname", ""),
                "statistics": video_data.get("statistics", {})
            }
        else:
            return {"success": False, "error": data.get("message", "Unknown error")}
            
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def get_video_script_from_aweme_id(aweme_id: str) -> dict:
    """
    通过视频ID获取视频完整信息（更稳定的方式）
    
    Args:
        aweme_id: 抖音视频ID
    
    Returns:
        包含视频文案信息的字典
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 使用 TikTok/Douyin App V3 API
    url = f"{BASE_URL}/tiktok/app/v3/fetch_one_video"
    params = {"aweme_id": aweme_id}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 200:
            video_data = data.get("data", {})
            return {
                "success": True,
                "title": video_data.get("desc", ""),
                "video_id": aweme_id,
                "author": video_data.get("author", {}).get("nickname", ""),
                "statistics": video_data.get("statistics", {}),
                "music": video_data.get("music", {}).get("title", "")
            }
        else:
            return {"success": False, "error": data.get("message", "Unknown error")}
            
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

# 测试
if __name__ == "__main__":
    # 测试链接
    test_url = "https://v.douyin.com/cDjKxQJsNSk/"
    
    print("正在获取抖音视频信息...")
    result = get_douyin_video_info(test_url)
    
    if result["success"]:
        print(f"✅ 获取成功!")
        print(f"视频文案: {result['title']}")
        print(f"视频ID: {result['video_id']}")
        print(f"作者: {result['author']}")
    else:
        print(f"❌ 获取失败: {result['error']}")
```

### 5.2 扣子插件配置（JSON格式）

```json
{
  "api_path": "/api/v1/douyin/web/fetch_one_video",
  "method": "GET",
  "headers": {
    "Authorization": "Bearer {{api_key}}"
  },
  "params": {
    "share_url": {
      "type": "string",
      "required": true,
      "description": "抖音分享链接"
    }
  },
  "response": {
    "title": {
      "path": "data.desc",
      "description": "视频文案/标题"
    },
    "video_id": {
      "path": "data.aweme_id",
      "description": "视频ID"
    },
    "author": {
      "path": "data.author.nickname",
      "description": "作者昵称"
    }
  }
}
```

---

## 六、注意事项

1. **合规性**：TikHub 明确禁止用于爬虫、恶意采集、商业泄露等违规行为
2. **接口稳定性**：Web接口可能不稳定，建议：
   - 优先使用 App V3 API
   - 添加重试机制
   - 做好接口失效的降级处理
3. **成本控制**：建议设置每日调用上限，避免意外超支
4. **数据预处理**：TikHub 返回的是视频标题/描述文案，如需提取语音内容（如视频中口播的文字），需额外使用 ASR 服务

---

## 七、结论

| 方案 | 可用性 | 推荐度 | 说明 |
|------|--------|--------|------|
| 火山引擎视频理解 | ❌ 不推荐 | - | 不支持抖音链接，需上传视频 |
| TikHub API | ✅ 推荐 | ⭐⭐⭐⭐ | 支持抖音链接，价格便宜 |
| 无极引擎 | ⚠️ 备选 | ⭐⭐⭐ | 可用但稳定性不明 |

**最终推荐**：使用 **TikHub API** 作为主要方案。其优势在于支持直接输入抖音链接获取视频文案，价格便宜（约0.01元/次），有免费额度可以测试。

---

*报告生成时间：2026-04-10*
