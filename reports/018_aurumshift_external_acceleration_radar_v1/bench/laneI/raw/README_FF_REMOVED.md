Les réponses brutes ForexFactory (`s*_ff_json.json`, `s*_ff_xml.xml`) ont été retirées du dépôt : les CGU de
redistribution de ForexFactory n'ont pas pu être lues (403), on ne republie donc pas leur contenu. Les fichiers
`*.meta.json` (horodatage de réception, statut HTTP, Last-Modified, sha256 du brut) sont conservés comme preuve.
Pour reproduire : `fetch_calendars.py <tag> ff_json ff_xml` (≤ 1 requête/heure).
