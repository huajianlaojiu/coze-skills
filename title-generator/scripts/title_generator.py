#!/usr/bin/env python3
"""
短视频爆款标题生成器 - 核心脚本
基于模板库生成各类爆款标题
"""

import random
from typing import List, Dict

# 标题模板库
TEMPLATES = {
    "悬念式": [
        "原来{content}这么简单，后悔现在才知道",
        "难怪{content}，原来一直都做错了",
        "那个{content}的人，后来怎么样了",
        "{content}的秘密，90%的人都不知道",
        "我还以为{content}，直到亲眼所见",
        "{content}之后，我整个人都变了",
        "终于有人把{content}说清楚了",
        "{content}的真相，看完沉默了",
        "为什么{content}的人越来越多了",
        "{content}内幕曝光，评论区炸了",
    ],
    "数字式": [
        "{num}个技巧，学会受用一生",
        "坚持{num}天，我发生了惊人变化",
        "{num}个{content}，学会了受用一生",
        "{num}元的神仙生活，太羡慕了",
        "{num}天见证改变，方法公开",
        "{num}个小习惯，让生活更美好",
        "分享{num}个私藏好物，第{x}个绝了",
        "{num}岁开始{content}，现在怎么样了",
        "花{num}元改造，结果出乎意料",
        "{num}个动作，坚持做告别{content}",
    ],
    "疑问式": [
        "{content}是真的吗？实测告诉你",
        "{content}真的能成功吗？我替你们试了",
        "为什么大家都在{content}？",
        "{content}和{content2}，到底哪个更好？",
        "你还在{content}吗？快停下来",
        "{content}是什么体验？只有经历过才懂",
        "凭什么{content}的人能成功？",
        "{content}会不会影响{content2}？答案来了",
        "{num}岁还没{content}，还有救吗？",
        "{content}和{content2}，你选哪个？",
    ],
    "反转式": [
        "辞职后比上班还忙，但更快乐了",
        "我宣布退出{content}，理由太离谱",
        "花100块买{content}，结果出乎意料",
        "不{content}的第{num}天，整个人都升华了",
        "别人{content}，我却{content2}，对比太真实",
        "男朋友送我的{content}，气笑了",
        "以为{content}，结果{content2}，人生如戏",
        "我妈说{content}，我信了二十几年",
        "去了{num}次{content}，总结出{num}个坑",
        "甲方让我{content}，改完他哭了",
    ],
    "情感式": [
        "{num}岁才发现，{content}才是最重要的",
        "给{content}的一封信，看哭了无数人",
        "谢谢你{content}，温暖了我的岁月",
        "那些{content}的人，后来都怎么样了",
        "长大后才明白，{content}的意义",
        "如果能重来，我一定{content}",
        "{num}岁，我终于活成了自己想要的样子",
        "普通人如何{content}？这是我的答案",
        "致{content}：对不起，我{content2}了",
        "原来{content}，才是真正的{content2}",
    ],
}

# 平台适配热词
PLATFORM_WORDS = {
    "抖音": ["🔥", "绝了", "YYDS", "真香", "破防", "狠狠", "太可了"],
    "快手": ["老铁", "666", "扎心", "破防了", "整起来", "没毛病"],
    "小红书": ["宝藏", "绝绝子", "哭死", "救大命", "好绝", "种草"],
    "视频号": ["必看", "收藏", "转发", "涨知识", "建议", "转给"],
    "B站": ["绝活", "整活", "芜湖", "知识UP", "真滴", "有内味"],
}


def generate_titles(
    content: str,
    title_type: str = "悬念式",
    platform: str = "抖音",
    num_results: int = 5,
    content2: str = None
) -> List[Dict[str, str]]:
    """
    生成短视频标题
    
    Args:
        content: 视频主题内容
        title_type: 标题类型
        platform: 目标平台
        num_results: 生成数量
        content2: 第二个内容（用于对比类标题）
    
    Returns:
        标题列表，每项包含标题和亮点分析
    """
    if title_type not in TEMPLATES:
        raise ValueError(f"不支持的标题类型: {title_type}")
    
    if title_type == "随机":
        title_type = random.choice(list(TEMPLATES.keys()))
    
    templates = TEMPLATES[title_type]
    platform_words = PLATFORM_WORDS.get(platform, PLATFORM_WORDS["抖音"])
    
    results = []
    used_templates = []
    
    for _ in range(num_results * 2):  # 多生成一些用于筛选
        if len(results) >= num_results:
            break
            
        template = random.choice(templates)
        if template in used_templates and len(templates) > num_results:
            continue
        
        try:
            # 随机数字
            num = random.choice([3, 5, 7, 10, 15, 21, 30, 99, 100])
            x = random.randint(1, num)
            
            # 填充模板
            title = template.format(
                content=content,
                content2=content2 or "躺平",
                num=num,
                x=x
            )
            
            # 平台适配
            if platform != "B站":
                title = f"{title} {random.choice(platform_words)}"
            
            # 去除重复
            if title not in [r["title"] for r in results]:
                used_templates.append(template)
                results.append({
                    "title": title,
                    "type": title_type,
                    "platform": platform,
                    "highlight": _analyze_highlight(title, title_type)
                })
        except KeyError:
            continue
    
    return results[:num_results]


def _analyze_highlight(title: str, title_type: str) -> str:
    """分析标题亮点"""
    highlights = {
        "悬念式": "设置悬念，引发好奇心，促使用户点击探索",
        "数字式": "具体数据增强可信度，让人觉得有价值",
        "疑问式": "抛出问题激发思考，增加互动欲望",
        "反转式": "出人意料的反转，产生冲击感",
        "情感式": "引发共鸣触动内心，激发分享欲望",
    }
    
    highlight = highlights.get(title_type, "具有爆款潜力")
    
    # 添加通用亮点
    if any(c.isdigit() for c in title):
        highlight += " | 含数字更醒目"
    if any(s in title for s in ["！", "？", "🔥", "？"]):
        highlight += " | 标点符号增强语气"
    
    return highlight


def format_output(results: List[Dict[str, str]]) -> str:
    """格式化输出"""
    if not results:
        return "未能生成标题，请尝试更换内容或类型"
    
    title_type = results[0]["type"]
    platform = results[0]["platform"]
    
    output = f"【短视频爆款标题 - {title_type}式】\n"
    output += f"平台：{platform}\n\n"
    
    for i, item in enumerate(results, 1):
        output += f"{i}. {item['title']}\n"
        output += f"   亮点：{item['highlight']}\n\n"
    
    output += f"💡 选用建议：{_get_suggestion(results)}"
    
    return output


def _get_suggestion(results: List[Dict[str, str]]) -> str:
    """获取选用建议"""
    suggestions = [
        "建议选择带数字的标题，点击率更高",
        "悬念式标题适合知识类内容，能有效提升完播率",
        "带有问号的标题更容易引发评论互动",
        "情感类标题容易引发共鸣，适合朋友圈分享",
        "反转式标题冲击力强，适合剧情类内容",
    ]
    return random.choice(suggestions)


# 命令行接口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="短视频爆款标题生成器")
    parser.add_argument("--content", "-c", required=True, help="视频主题内容")
    parser.add_argument("--type", "-t", default="悬念式", help="标题类型")
    parser.add_argument("--platform", "-p", default="抖音", help="目标平台")
    parser.add_argument("--num", "-n", type=int, default=5, help="生成数量")
    
    args = parser.parse_args()
    
    results = generate_titles(
        content=args.content,
        title_type=args.type,
        platform=args.platform,
        num_results=args.num
    )
    
    print(format_output(results))
