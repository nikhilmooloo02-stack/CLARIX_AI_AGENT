"""Offline tests for clarix_core. Run with:  python test_core.py
No API key or internet needed.
"""
import json
import os
from types import SimpleNamespace

import clarix_core as core


def names(result):
    return [r["name"] for r in result["results"]]


# --- search ---
r = core.search_products("A4 paper")
assert any("Butterfly" in n for n in names(r)) and any("Rotatrim" in n for n in names(r)), r
assert core.search_products("gloves")["results"][0]["sku"] == "PPE-002"
assert core.search_products("standing desk")["count"] == 0
assert core.search_products("3D printer")["count"] == 0
assert core.search_products("PPE")["count"] == 4
assert core.search_products("stationery")["count"] >= 8
assert core.search_products("OFF-005")["results"][0]["name"] == "Shredder 10 Sheet"

# --- stock status ---
assert core.get_product("WRI-002")["stock_status"] == "out_of_stock"
assert core.get_product("WRI-003")["stock_status"] == "discontinued"
assert core.get_product("PPE-002")["stock_status"] == "low_stock"
assert core.get_product("STA-001")["stock_status"] == "in_stock"
assert "error" in core.get_product("NOPE-1")

# --- VAT ---
assert core.calculate_vat(5500) == {"amount_excl_vat": 5500.0, "vat_15_percent": 825.0, "amount_incl_vat": 6325.0}
assert core.calculate_vat(6325, "remove")["amount_excl_vat"] == 5500.0

# --- quote: bulk tiers, VAT, PDF ---
q = core.create_quote("Thandi Mokoena", "Bright Dental", [
    {"sku": "HOU-002", "quantity": 10},   # bulk min 12 not met -> R65
    {"sku": "WRI-001", "quantity": 5},    # bulk min 5 met -> R110
])
assert q["subtotal_excl_vat"] == 1200.0 and q["vat_15_percent"] == 180.0 and q["total_incl_vat"] == 1380.0, q
assert os.path.exists(q["pdf_file"]) and os.path.getsize(q["pdf_file"]) > 1000

q = core.create_quote("A", "B", [{"sku": "STA-001", "quantity": 10}])
assert q["subtotal_excl_vat"] == 820.0 and q["total_incl_vat"] == 943.0

# discontinued and unknown items are excluded, not quoted at R0
q = core.create_quote("A", "B", [
    {"sku": "WRI-003", "quantity": 5},
    {"sku": "ZZZ-999", "quantity": 1},
    {"sku": "OFF-001", "quantity": 20},
])
assert len(q["lines"]) == 1 and len(q["excluded"]) == 2 and q["subtotal_excl_vat"] == 800.0

# shortfall warning and consultant note
q = core.create_quote("A", "B", [{"sku": "OFF-005", "quantity": 10}])
assert q["subtotal_excl_vat"] == 11300.0 and q["total_incl_vat"] == 12995.0
assert q["warnings"] and q["notes"]

# validation
assert "error" in core.create_quote("", "B", [{"sku": "STA-001", "quantity": 1}])
assert "error" in core.create_quote("A", "B", [])
assert "error" in core.create_quote("A", "B", [{"sku": "WRI-003", "quantity": 1}])
assert "error" in core.run_tool("nope", "{}")
assert "error" in core.run_tool("get_product", "{}")
assert "error" in core.run_tool("get_product", "not json")


# --- agent loop with a scripted fake model ---
def tool_call(call_id, name, args):
    return SimpleNamespace(id=call_id, function=SimpleNamespace(name=name, arguments=json.dumps(args)))


def reply(content=None, calls=None):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=calls))])


class FakeClient:
    def __init__(self, scripted):
        self.scripted = list(scripted)
        self.seen = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.seen.append(kwargs["messages"][:])
        item = self.scripted.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


fake = FakeClient([
    reply(calls=[tool_call("c1", "create_quote", {
        "customer_name": "Sam", "company_name": "Acme",
        "items": [{"sku": "STA-001", "quantity": 5}]})]),
    reply(content="Quote ready."),
])
text, pdf = core.run_agent(fake, "m", [{"role": "user", "content": "quote please"}])
assert text == "Quote ready." and pdf and os.path.exists(pdf)
second_call_messages = fake.seen[1]
assert second_call_messages[-2]["role"] == "assistant" and second_call_messages[-2]["tool_calls"][0]["id"] == "c1"
assert second_call_messages[-1]["role"] == "tool" and second_call_messages[-1]["tool_call_id"] == "c1"
assert "pdf_file" not in second_call_messages[-1]["content"]

# transient API error is retried once
fake = FakeClient([RuntimeError("boom"), reply(content="ok")])
assert core.run_agent(fake, "m", [{"role": "user", "content": "hi"}])[0] == "ok"

# persistent API error returns the friendly fallback, not a crash
fake = FakeClient([RuntimeError("a"), RuntimeError("b")])
assert core.run_agent(fake, "m", [{"role": "user", "content": "hi"}])[0] == core.FALLBACK_REPLY

# a model that never stops calling tools is cut off
loop = [reply(calls=[tool_call(f"c{i}", "list_categories", {})]) for i in range(10)]
assert core.run_agent(FakeClient(loop), "m", [{"role": "user", "content": "hi"}])[0] == core.FALLBACK_REPLY

print("All tests passed.")
