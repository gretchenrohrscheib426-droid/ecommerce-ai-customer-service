"""Bounded single-process tool workflow. No autonomous agent or invented model answer."""

import json
import secrets
import threading
import time
from pathlib import Path

from ..config import Settings
from ..graph.queries import compile_plan, execute
from ..llm.deepseek_client import DeepSeek, OnlineBlocked
from ..logging_config import event
from ..qa.schema import Answer
from .intent import local_plan
from .state import AgentState


def render_rows(rows, intent):
    lines = []
    for row in rows:
        if "attribute" in row:
            lines.append(
                f"{row['sku']}：{row['attribute'] or '属性缺失'} = {row['value'] or '值缺失'}。[{row['sku_id']}]"
            )
        elif "category1" in row:
            lines.append(
                f"{row['product']}：{row['category1']} → {row['category2']} → {row['category3']}。[{row['source_id']}]"
            )
        elif "price" in row:
            lines.append(
                f"{row['sku']}：资料价格 {row['price']} 元；上架标记 {row['is_sale']}。[{row['sku_id']}]"
            )
        elif "tag" in row:
            origin = (
                "独立示例人工标注"
                if row.get("model_version", "").startswith("independent-manual-fixture")
                else "模型抽取"
            )
            lines.append(
                f"{row['product']}：{origin}「{row['tag']}」，原文位置 [{row['start']}, {row['end']})；待人工核实。[{row['source_id']}]"
            )
        elif "description" in row:
            lines.append(
                f"{row['product']}；品牌：{row.get('brand') or '缺失'}；分类：{row.get('category') or '缺失'}。资料描述：{row['description']} [{row['source_id']}]"
            )
        else:
            lines.append(f"{row['product']} [{row['source_id']}]")
    return "\n".join(lines) + "\n数据来自本地演示资料，不代表实时售价、库存或已核实产品承诺。"


class ChatService:
    def __init__(self, root, retriever, instance, online=False, dataset="course-private"):
        self.root = Path(root)
        self.retriever = retriever
        self.driver = instance
        self.online = online
        self.dataset = dataset
        self.pending = {}
        self.lock = threading.Lock()
        self.provider = DeepSeek(root)

    def chat(self, question):
        trace = secrets.token_hex(8)
        steps = ["parse"]
        begin = time.monotonic()
        answer = Answer(message="", status="error", trace_id=trace)
        state = AgentState(question=question.message, trace_id=trace)
        try:
            if question.choice or question.clarification_token:
                if not question.choice or not question.clarification_token:
                    raise ValueError("Choice and clarification token are both required")
                with self.lock:
                    pending = self.pending.get(question.clarification_token)
                    if not pending or pending["expires"] < time.monotonic():
                        raise ValueError("Clarification expired; repeat original question")
                    if question.message != pending["message"]:
                        raise ValueError("Question changed; request a new clarification")
                    matches = [e for e in pending["candidates"] if e["canonical_id"] == question.choice]
                    if len(matches) != 1:
                        raise ValueError("Choice outside issued candidates")
                    plan = pending["plan"]
                    entity = matches[0]
                    del self.pending[question.clarification_token]
                steps.append("confirmed-entity")
            else:
                plan = (
                    self.provider.plan(question.message)
                    if self.online
                    else local_plan(question.message, self.retriever.catalog())
                )
                if plan.intent == "unsupported":
                    answer.status = "unsupported"
                    answer.message = (
                        "本示例支持商品、分类、品牌、资料价格和抽取标签；该请求缺少受支持的数据或操作。"
                    )
                    return answer
                steps.append("align")
                aligned = self.retriever.align(plan.entity, plan.label)
                if aligned["status"] == "no_match":
                    answer.status = "no_match"
                    answer.message = "没有找到足够接近的实体，请补充完整商品名、品牌或类别。"
                    return answer
                if aligned["status"] == "clarify":
                    token = secrets.token_urlsafe(24)
                    with self.lock:
                        self.pending = {
                            k: v for k, v in self.pending.items() if v["expires"] > time.monotonic()
                        }
                        if len(self.pending) >= 1000:
                            raise RuntimeError("Clarification capacity reached")
                        self.pending[token] = {
                            "expires": time.monotonic() + 300,
                            "plan": plan,
                            "candidates": aligned["candidates"],
                            "message": question.message,
                        }
                    answer.status = "clarify"
                    answer.message = "请确认您指的是哪一个实体。"
                    answer.candidates = aligned["candidates"]
                    answer.clarification_token = token
                    return answer
                entity = aligned["entity"]
            steps.append("compile")
            state.intent = plan.intent
            state.entities = [{"query": plan.entity, "label": plan.label}]
            state.aligned_entities = [entity]
            query, params = compile_plan(plan, entity, Settings.load(self.root).query_max_rows)
            state.query_plan = {"template_intent": plan.intent, "parameters": params}
            if self.online and Settings.load(self.root).profile == "course-reference":
                generated, proposed = self.provider.course_query(
                    json.dumps(
                        {
                            "question": question.message,
                            "resolved_entity": entity,
                            "required_parameters": params,
                        },
                        ensure_ascii=False,
                    ),
                    [query],
                )
                if generated != query or proposed != params:
                    raise ValueError("Generated query changed the resolved entity or approved template")
                query, params = generated, proposed
            steps.append("query")
            rows = execute(self.driver, query, params)
            state.query_result = rows
            if not rows:
                answer.status = "no_results"
                answer.message = "实体已找到，但本地资料没有该问题对应的记录。"
                return answer
            steps.append("answer")
            if self.online:
                rows = self.provider.answer(question.message, rows, self.dataset)
                answer.generation = "deepseek-evidence-selection-and-local-fact-rendering"
            answer.status = "ok"
            answer.evidence = rows
            answer.message = render_rows(rows, plan.intent)
            answer.grounded = True
            return answer
        except OnlineBlocked:
            state.errors.append("LLM service unavailable")
            answer.status = "online_unavailable"
            answer.message = "LLM service unavailable：在线模型未配置、未获授权或调用失败。"
            return answer
        except ValueError as error:
            answer.status = "invalid_request"
            answer.message = str(error)
            return answer
        finally:
            state.answer = answer.message
            event(
                "ecommerce_graph_agent.chat",
                trace,
                answer.status,
                input_length=len(question.message),
                evidence_rows=len(answer.evidence),
            )
            answer.steps = steps
            if len(steps) > 6:
                raise RuntimeError("Workflow exceeded six steps")
            report = self.root / "reports/private/chat-events.jsonl"
            report.parent.mkdir(parents=True, exist_ok=True)
            with self.lock, report.open("a", encoding="utf-8") as log:
                log.write(
                    json.dumps(
                        {
                            "trace_id": trace,
                            "status": answer.status,
                            "steps": steps,
                            "elapsed_ms": round((time.monotonic() - begin) * 1000),
                            "input_length": len(question.message),
                            "evidence_rows": len(answer.evidence),
                            "generation": answer.generation,
                        }
                    )
                    + "\n"
                )
