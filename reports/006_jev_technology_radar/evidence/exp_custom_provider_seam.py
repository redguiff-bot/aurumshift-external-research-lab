import json
from system_one_adapter import SystemOneAdapterClient, Noul, Choice, Score
from system_one_adapter.providers import ProviderResult
from typesafe_sdk import TypeSafeError

class RuleProvider:
    """Deterministic baseline plugged through the adapter's provider seam."""
    model_name = "rules-v0"
    def request(self, messages, *, schema, structured):
        doc = messages[-1].content.lower()
        props = schema["properties"]["answers"]
        # resolve $ref
        defs = schema.get("$defs", {})
        ans_schema = props if "properties" in props else defs[props["$ref"].split("/")[-1]]
        out = {}
        for qid, s in ans_schema["properties"].items():
            neg = "miss" in doc or "cut" in doc
            if s.get("type") == "number":
                out[qid] = 0.8 if neg else 0.2
            else:
                ref = defs[s["$ref"].split("/")[-1]] if "$ref" in s else s
                keys = list(ref["properties"])
                n = len(keys); p = {k: 1.0/n for k in keys}
                out[qid] = p
        return ProviderResult(json.dumps({"answers": out}), 0, 0)
    def translate_error(self, e): return TypeSafeError(str(e))

q = {"guidance_cut": Noul(instructions="Company cut guidance."),
     "tone": Choice(instructions="Tone", criteria={"bull":None,"bear":None,"neutral":None}),
     "impact": Score(instructions="Impact", criteria=["low","mid","high"])}
c = SystemOneAdapterClient(structured_outputs=True, llm_answer_mode="probabilities")
r = c.system_one("ACME cut guidance after Q3 miss", q, model=RuleProvider())
print(r.model_dump_json(indent=1)[:900])
print(r.usage)
