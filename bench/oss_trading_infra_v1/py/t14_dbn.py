"""T14 — Databento DBN (open, zero-copy market-data format; databento-dbn Rust/py): offline roundtrip of MBO records, both ts_event and ts_recv preserved?
No network / API key used (the paid databento client is NOT evaluated)."""
import json, io, warnings; warnings.filterwarnings("ignore")
import databento_dbn as d, databento as db
res = {"databento_version": db.__version__}
try:
    m = d.MBOMsg(publisher_id=1, instrument_id=42, ts_event=1_700_000_000_000_000_000, order_id=7, price=100_500_000_000, size=3, action=d.Action.ADD, side=d.Side.BID,
                 ts_recv=1_700_000_000_000_500_000, flags=0, channel_id=0, ts_in_delta=250, sequence=1)
    res["ctor_ok"] = True; res["fields"] = [a for a in dir(m) if not a.startswith("_") and a not in ("pretty_price",)][:30]
    buf = io.BytesIO(); enc = d.Transcoder if hasattr(d, "Transcoder") else None
    res["has_Transcoder"] = enc is not None; res["has_DBNDecoder"] = hasattr(d, "DBNDecoder"); res["has_DBNEncoder"] = hasattr(d, "DBNEncoder")
    if hasattr(d, "DBNEncoder"):
        e = d.DBNEncoder(buf, d.Schema.MBO if hasattr(d, "Schema") else None) if False else None
    md = d.Metadata(dataset="XNAS.ITCH", schema=d.Schema.MBO, start=1_700_000_000_000_000_000, stop=1_700_000_001_000_000_000, limit=None, stype_in=d.SType.RAW_SYMBOL, stype_out=d.SType.INSTRUMENT_ID, symbols=["X"], partial=[], not_found=[], mappings=[]) if hasattr(d, "Metadata") else None
    res["metadata_ctor"] = md is not None
    if md is not None:
        b = bytes(md.encode()) if hasattr(md, "encode") else None
        if b is not None:
            dec = d.DBNDecoder(); dec.write(b); dec.write(bytes(m)); recs = dec.decode()
            res["roundtrip_records"] = len(recs); res["roundtrip_types"] = [type(r).__name__ for r in recs]
            r = [x for x in recs if type(x).__name__ == "MBOMsg"]
            if r: res["roundtrip_ts_event"] = r[0].ts_event; res["roundtrip_ts_recv"] = r[0].ts_recv; res["roundtrip_price"] = r[0].price; res["ts_recv_preserved_separately"] = r[0].ts_recv != r[0].ts_event
except Exception as ex:
    res["error"] = f"{type(ex).__name__}: {str(ex)[:300]}"
print(json.dumps(res, default=str))
