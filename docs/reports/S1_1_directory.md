# S1.1 Administrative directory load

- **Run:** PipelineRun 3, finished 2026-10-14 17:09 UTC
- **Source:** KGIS (KSRSAC) Admin_Dynamic and Village_Dynamic layers (attributes only)
- **Config hash:** `4027522ebf13`

## Totals (Karnataka)

| Level | Rows |
|---|---|
| states | 1 |
| districts | 31 |
| blocks | 240 |
| villages | 30,038 |

## Pilot district: Bengaluru (Rural) (LGD 526)

- Villages: **1,139**
- With a Census 2011 code: **1,137** (99.8%)

| Taluk (block) | Villages |
|---|---|
| Devanahalli | 227 |
| Doddaballapura | 304 |
| Hoskote | 298 |
| Nelamangala | 310 |

Pilot villages affected by each data issue:

| Issue | Villages |
|---|---|
| census_code_differs_from_lgd_code | 148 |
| census_code_shared | 172 |
| same_code_different_name_or_taluk | 1 |
| village_without_census_code | 2 |

## Data issues (whole state)

| Issue | Count | Examples |
|---|---|---|
| census_code_differs_from_lgd_code | 4,043 | 607872 Tenkabylu: census 607870; 607873 Suttha: census 607876; 607875 H.Honnekoppa: census 607876; 607890 Amache: census 607917; 607907 Purappamane: census 607908 |
| census_code_shared | 4,495 | 607870: 607870 Manashetty; 607870: 607872 Tenkabylu; 607876: 607873 Suttha; 607876: 607875 H.Honnekoppa; 607876: 607876 Ganganakoppa |
| extra_polygons_merged | 2,229 |  |
| same_code_different_name_or_taluk | 219 | 599324: Asangihala / Ilarhalli; 602248: Aravatagi / Aravatagi (Neeralagi); 602259: Banadura / Holthikoti; 602259: Banadura / Ragikalapur; 602406: Anchatageri / Budnala |
| village_without_census_code | 82 | 939527 Kalasi; 607860 Harohitthage; 938589 Adugalale; 938590 Hagaturu; 938591 Hosakote |
| village_without_lgd_code | 117 | KGIS 8253 Katarki_Submerged; KGIS 21639 Kakanahalli; KGIS 21837 Yadani; KGIS 22981 Mallenahalli; KGIS 22982 Manchenahalli |
| village_without_taluk | 57 | 599419 Anemadu; 622678 Channapalli; 622675 Gattaryagadahalli; 622680 Goovalahalli; 622679 Goovalahalli Majare Rampura |
