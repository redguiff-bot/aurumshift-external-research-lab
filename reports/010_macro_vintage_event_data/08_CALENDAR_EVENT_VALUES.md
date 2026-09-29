# 08 — Calendars and event values

Two separate classes (as required):

## Schedule-only calendars (no actual/previous/forecast)
| Calendar | Machine-readable | Time-of-day | Event id | Values |
|---|---|---|---|---|
| BLS | ICS, 313 events | 08:30/10:00 ET | ICS UID (per event) | none |
| BEA | ICS, 119 events | UTC datetimes | none used | none; estimate stage (Advance/Second/Third) in title |
| EIA WPSR | HTML | times in text | – | none (the "forecast" keyword hit is site navigation, verified for EIA) |
| FRED release calendar | HTML | times in text | – | none |
| Census | HTML | many times | – | none |
| ECB, Eurostat, Fed G.17 | HTML | no times detected | – | none (ECB "forecast" hit = navigation menu, verified) |

Scheduled timestamps in these calendars agree with actual ALFRED vintage dates for the tested series (05). They contain no forecast; **no official source examined publishes consensus forecasts** (INFERENCE: official statistical agencies do not).

## Release-value feeds
* ALFRED / RTDSM / OECD revisions provide *values by vintage* → "actual" and "previous as known at T" can be derived (previous = same-observation value in the prior vintage; revision = difference).
* Forecast/consensus: only the **unofficial** TipRanks tool was executed (comparator, `results/tipranks_calendar_comparator.json`): fields `actual`, `estimate`, `prev`, `time`, `impact`, `unit`; no event id, no provider attribution, no revision info, one duplicated event (API crude stock at 20:30 and 21:00). Its `time` values (e.g. Retail Sales 2026-09-16T12:30:00) lack a timezone marker (12:30 = 08:30 ET only by inference).

Conclusion: official calendars are schedule-only; official values are PIT only via ALFRED-class vintage stores; forecasts are not available from any official source tested.
