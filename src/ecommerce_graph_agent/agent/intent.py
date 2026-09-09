"""Explicit offline parser; it is not an LLM response."""

from typing import Literal

from ..qa.schema import Label, Plan


def local_plan(message, catalog):
    unsupported = ["订单", "物流", "库存", "实时", "优惠券", "删除", "创建节点", "修改价格", "密码", "密钥"]
    if any(word in message for word in unsupported):
        return Plan(intent="unsupported", entity=message[:120])
    names = sorted({r["name"] for r in catalog if r["name"] in message}, key=lambda x: (-len(x), x))
    intent: Literal["price", "tags", "products", "product_detail", "attributes", "category_path"] = (
        "price"
        if any(x in message for x in ["价格", "多少钱", "售价"])
        else (
            "tags"
            if any(x in message for x in ["标签", "特征"])
            else (
                "products"
                if any(x in message for x in ["哪些", "有什么", "有哪些", "商品"])
                else "product_detail"
            )
        )
    )
    if any(x in message for x in ["属性", "SKU", "sku", "规格"]):
        intent = "attributes"
    if any(x in message for x in ["分类链", "属于什么分类", "分类路径"]):
        intent = "category_path"
    label: Label | None = (
        "BaseTrademark"
        if "品牌" in message
        else ("SPU" if intent in ["price", "tags", "attributes", "category_path"] else None)
    )
    if names:
        matching = [
            n for n in names if not label or any(r["name"] == n and r["label"] == label for r in catalog)
        ]
        if matching:
            return Plan(intent=intent, entity=matching[0], label=label)
    entity = message
    for word in [
        "有哪些商品",
        "有什么商品",
        "有哪些",
        "有什么",
        "多少钱",
        "的价格",
        "价格",
        "的标签",
        "标签",
        "的特征",
        "特征",
        "品牌",
        "请问",
        "？",
        "?",
    ]:
        entity = entity.replace(word, "")
    return Plan(intent=intent, entity=(entity.strip() or message)[:120], label=label)
