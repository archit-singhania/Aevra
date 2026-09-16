import json


def build_campaign_prompt(
    *,
    campaign: dict[str, object],
    brand: dict[str, object],
    rules: list[dict[str, object]],
    citations: list[dict[str, object]],
    feedback: str | None,
) -> str:
    evidence = "\n\n".join(
        f"[C{index}] {item['document_title']}: {item['excerpt']}"
        for index, item in enumerate(citations, start=1)
    )
    contract = {
        "master_plan": {
            "objective": "string",
            "message_pillars": ["string"],
            "creative_direction": "string",
        },
        "variants": [
            {
                "platform": "one requested platform",
                "title": "required for youtube; otherwise nullable",
                "caption": "platform-native copy",
                "hashtags": ["#Example"],
                "call_to_action": "string or null",
            }
        ],
    }
    return (
        "Create a grounded social campaign. Use only the supplied evidence for factual claims. "
        "Do not invent capabilities, results, customers, statistics, or guarantees. Produce a "
        "distinct native variant for every requested platform. Return only valid JSON matching "
        f"this contract: {json.dumps(contract)}\n\n"
        f"CAMPAIGN:\n{json.dumps(campaign, ensure_ascii=False)}\n\n"
        f"BRAND:\n{json.dumps(brand, ensure_ascii=False)}\n\n"
        f"RULES:\n{json.dumps(rules, ensure_ascii=False)}\n\n"
        f"EVIDENCE:\n{evidence or 'No evidence was retrieved; avoid factual product claims.'}\n\n"
        f"REVISION FEEDBACK:\n{feedback or 'None'}"
    )
