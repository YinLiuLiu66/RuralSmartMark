"""Prompt 集中管理（decisions #6/#27）：便于答辩展示与调优。

硬约束：不得编造素材之外的奖项/认证/数据；引用数字必须与给定事实一致。
"""

from typing import Any

STORY_SYSTEM = """你是县域农产品品牌策划，为「麻江蓝莓」写品牌故事。
只输出中文正文，不要解释写作过程，不要 Markdown 标题。
要求：
1. 300–450 字，3–4 段；
2. 用一个具体场景承接农户口述的语感（如清晨采果、冷链发车），
   不得为口述者虚构姓名、年龄、身份或经历；
3. 最多引用两条给定的产业事实，数字必须与给定事实一致；
4. 只能使用给定素材与实时事实中的信息：不得新增人物、年份、年限、距离、销量、
   价格、配送时效、库存承诺或活动；不得编造素材中没有的奖项、认证、地理标志表述；
   引用认证或名次时必须保留素材原文的主语与范围，不得升级表述；
5. 文化母题只作意象借用，不得声称蓝莓与传说存在历史渊源；
6. 结尾单独一行，以「IP 定位：」开头，写一句不超过 30 字的品牌定位语。"""


def _material_block(material: dict[str, Any]) -> str:
    facts = "\n".join(f"- {f['text']}" for f in material["industry_facts"])
    oral = "\n".join(f"- {o['text']}" for o in material["oral_history"])
    motif = material["cultural_motif"]
    return (
        f"产地：{material['county']}\n"
        f"品类：{material['product']}（{material['positioning']}）\n"
        f"产业事实：\n{facts}\n"
        f"农户口述（演示虚构）：\n{oral}\n"
        f"文化母题：{motif['title']}——{motif['text']}\n"
        f"边界提示：{motif['note']}\n"
        f"素材边界：{material['disclaimer']}"
    )


def build_story_messages(
    material: dict[str, Any], facts: list[str]
) -> list[dict[str, str]]:
    facts_text = "\n".join(f"- {f}" for f in facts) or "- （暂无实时数据）"
    return [
        {"role": "system", "content": STORY_SYSTEM},
        {
            "role": "user",
            "content": (
                f"{_material_block(material)}\n\n"
                f"当前供应链实时事实：\n{facts_text}\n\n"
                "请写品牌故事，并在最后给出 IP 定位语。"
            ),
        },
    ]


COPY_SYSTEM = """你是农产品电商内容运营，为「麻江蓝莓」写多平台文案。
只输出中文，按下面三个板块输出，板块名用【】标注，不要额外解释：
【小红书】标题 + 80–120 字正文 + 3 个话题标签
【短视频口播】60 秒内可读完的口播稿，口语化
【客服问答】3 组问答，回答不超过 40 字
要求：只能使用给定素材与实时事实中的信息；不得编造奖项、认证、功效、产地年限、人物故事、
配送时效或库存承诺；数字必须与给定事实一致；引用认证或名次时保留素材原文的主语与范围；
农户口述只可化用语气，不得虚构具体人物或亲历。"""


def build_copy_messages(
    material: dict[str, Any], facts: list[str], story: str | None = None
) -> list[dict[str, str]]:
    facts_text = "\n".join(f"- {f}" for f in facts) or "- （暂无实时数据）"
    story_block = f"\n已定稿品牌故事：\n{story}\n" if story else ""
    return [
        {"role": "system", "content": COPY_SYSTEM},
        {
            "role": "user",
            "content": (
                f"{_material_block(material)}\n"
                f"{story_block}\n"
                f"当前供应链实时事实：\n{facts_text}\n\n"
                "请输出三个平台的文案。"
            ),
        },
    ]
