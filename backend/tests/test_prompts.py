from ruralsmartmark.agents.base import AgentName
from ruralsmartmark.agents.prompts import agent_brief, build_system_prompt
from ruralsmartmark.models import ProductProfile


def _non_zhaotong_product() -> ProductProfile:
    return ProductProfile(
        slug="ma-jiang-blueberry",
        name="麻江蓝莓",
        county="贵州省麻江县",
        province="贵州省",
        category="鲜果",
        form="1.5kg / 6 盒礼盒",
        specs={
            "brand_name": "麻江蓝莓演示品牌",
            "ip_name": "山野记录者",
        },
    )


def test_non_zhaotong_prompts_use_own_brand_and_ip():
    product = _non_zhaotong_product()
    system = build_system_prompt(product)
    story = agent_brief(AgentName.STORY, product)

    for text in (system, story):
        assert "麻江蓝莓演示品牌" in text
        assert "山野记录者" in text
        assert "乌蒙丑果" not in text
        assert "山风守园人" not in text
        assert "昭通" not in text


def test_zhaotong_prompts_keep_tuned_defaults():
    product = ProductProfile(
        slug="zhaotong-ugly-apple",
        name="昭通丑苹果",
        county="云南省昭通市昭阳区",
        province="云南省",
        category="鲜果",
        form="5kg / 12 枚礼盒",
        specs={"brand_name": "乌蒙丑果", "ip_name": "山风守园人"},
    )

    story = agent_brief(AgentName.STORY, product)
    assert "山风守园人" in story
    assert "不套袋" in story
