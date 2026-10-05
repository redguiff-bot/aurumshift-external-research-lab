"""laneBJKL — OpenTelemetry Python SDK smoke : 1 span (étape du chemin critique) + 1 compteur + 1 histogramme
vers les exporteurs console. Mesure : import, overhead par span (sans export réseau)."""
import json, time, io, contextlib
t0 = time.perf_counter()
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader, InMemoryMetricReader
from opentelemetry.sdk.resources import Resource
import opentelemetry.sdk.version as v
t_import = time.perf_counter() - t0
res = Resource.create({"service.name": "aurumshift-lab-smoke"})
buf = io.StringIO()
tp = TracerProvider(resource=res)
tp.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter(out=buf)))
mem = InMemorySpanExporter(); tp.add_span_processor(SimpleSpanProcessor(mem))
trace.set_tracer_provider(tp)
reader = InMemoryMetricReader()
mp = MeterProvider(resource=res, metric_readers=[reader]); metrics.set_meter_provider(mp)
tracer = trace.get_tracer("lab.critical_path"); meter = metrics.get_meter("lab.critical_path")
c = meter.create_counter("decision.count"); h = meter.create_histogram("pit.snapshot.lag_ms", unit="ms")
with tracer.start_as_current_span("decision_v1.evaluate", attributes={"decision_input.sha256": "ab" * 32, "arm": "B_quorum1_shadow"}) as sp:
    with tracer.start_as_current_span("pit.snapshot"):
        h.record(42.0, {"venue": "okx"})
    c.add(1, {"arm": "B_quorum1_shadow", "outcome": "SUPPRESSED_BY_QUORUM"})
spans = mem.get_finished_spans()
md = reader.get_metrics_data()
names = [m.name for rm in md.resource_metrics for sm in rm.scope_metrics for m in sm.metrics]
# overhead : 10 000 spans avec un exporteur no-op (mémoire désactivée)
tp2 = TracerProvider(); t2 = tp2.get_tracer("bench")
t = time.perf_counter()
for i in range(10_000):
    with t2.start_as_current_span("s"): pass
us_nop = (time.perf_counter() - t) / 10_000 * 1e6
tp3 = TracerProvider(); mem3 = InMemorySpanExporter(); tp3.add_span_processor(BatchSpanProcessor(mem3)); t3 = tp3.get_tracer("bench")
t = time.perf_counter()
for i in range(10_000):
    with t3.start_as_current_span("s", attributes={"k": i}): pass
us_batch = (time.perf_counter() - t) / 10_000 * 1e6; tp3.shutdown()
print(json.dumps({"otel_sdk": v.__version__, "t_import_s": round(t_import, 3), "spans_exported": len(spans),
                  "parent_child_ok": spans[0].parent.span_id == spans[1].context.span_id,
                  "console_export_bytes": len(buf.getvalue()), "metrics_seen": names,
                  "us_per_span_no_processor": round(us_nop, 2), "us_per_span_batch_inmemory": round(us_batch, 2)}, indent=1))
