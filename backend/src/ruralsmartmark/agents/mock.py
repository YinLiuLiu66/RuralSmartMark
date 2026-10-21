"""无 key / 测试环境的确定性兜底文案（decisions #11 断网演示）。

只用于 mock 路径；真实演示走 LLM。内容仍遵守"不编造认证"的约束。
"""

from typing import Any


def render(agent_type: str, material: dict[str, Any], facts: list[str]) -> str:
    county = material["county"]
    product = material["product"]
    fact_line = facts[0] if facts else f"{county}出产{product}。"
    quote = material["oral_history"][0]["text"]

    if agent_type == "copy":
        return (
            "【小红书】# 一盒来自麻江的蓝莓，甜得很克制\n"
            f"{fact_line} 山雾、蓝染、苗寨的清晨，都装进这一盒。"
            "冷链到家，果霜还在。\n"
            "#麻江蓝莓 #中国蓝莓之乡 #县域好物\n\n"
            "【短视频口播】清晨的麻江，雾还没散，果农已经上山了。"
            "摘下来的蓝莓直接进冷链，温度一路盯着。"
            "从山里到你家，这一盒只走了该走的路。\n\n"
            "【客服问答】\n问：蓝莓为什么有果霜？答：果霜是自然分泌的果粉，越新鲜越明显。\n"
            "问：怎么保存？答：冷藏 2–8℃，食用前再清洗。\n"
            "问：产地在哪里？答：贵州省黔东南州麻江县。"
        )

    return (
        f"{county}的清晨，雾从山坳里升起来，蓝莓叶上挂着水珠。"
        f"果农说：{quote}\n\n"
        "过去，果子挑到县城卖，一筐挣不了几个钱。冷链仓建起来之后，"
        "采摘、预冷、装车被拆成了几个明确的节点，每一车温度都有人盯着。"
        f"{fact_line}\n\n"
        "这不是把山货包装成故事，而是把山里本来就有的东西，"
        "用一条看得见的链路送到更远的地方。\n\n"
        "IP 定位：雾养麻江蓝莓，一盒看得见的山地清甜。"
    )
