-- clickhouse-local (single binary, no server): ASOF JOIN semantics. NOTE: ClickHouse ASOF requires >=1 equality column (sym).
CREATE TABLE q (sym String, ts DateTime64(6,'UTC'), bid Float64) ENGINE=Memory;
CREATE TABLE t (sym String, ts DateTime64(6,'UTC'), px Float64) ENGINE=Memory;
INSERT INTO q VALUES ('X','2024-01-01 00:00:00.000000', 100.0), ('X','2024-01-01 00:00:01.000000', 101.0), ('X','2024-01-01 00:00:02.000000', 102.0);
INSERT INTO t VALUES ('X','2024-01-01 00:00:01.000000', 1), ('X','2024-01-01 00:00:01.500000', 2), ('X','2024-01-01 00:00:00.500000', 3), ('X','2023-12-31 23:59:59.000000', 4);
SELECT 'inclusive(>=)' k, t.ts, q.bid FROM t ASOF LEFT JOIN q ON t.sym = q.sym AND t.ts >= q.ts ORDER BY t.ts FORMAT TSV;
SELECT 'strict(>)' k, t.ts, q.bid FROM t ASOF LEFT JOIN q ON t.sym = q.sym AND t.ts > q.ts ORDER BY t.ts FORMAT TSV;
