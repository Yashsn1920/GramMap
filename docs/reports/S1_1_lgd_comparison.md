# S1.1 LGD comparison, district 526

- LGD file: `/app/data/raw/lgd/villages_526.xlsx`
- Before reconciling: **Mismatch** (see below)

| Measure | Count |
|---|---|
| Villages in LGD | 1,171 |
| Villages in our directory (KGIS) | 1,139 |
| In both | 1,136 |
| In LGD but not ours | 35 |
| Ours but not in LGD | 3 |
| Census codes filled from LGD | 0 |
| Census code coverage after | 97.4% |

**In LGD but not ours (first 10):** 625032 Sevanagara; 625041 Shivalinga Pura; 625646 Jadigenahalli; 625761 Chikkahalli; 625929 Rangenahalli; 625949 Hosahalli; 910080 Mopurahalli (D); 910087 Hanagalapura (D); 910091 Ancharahalli (D); 910094 Kudihalli (D)

**Ours but not in LGD (first 10):** 625869 Rangenahalli; 625872 Chikkanahalli; 625893 Hosahalli

## After reconciling with LGD (--apply)

- Pilot villages: **1,171**, LGD villages: **1,171**, result: **Match**
- Added from LGD (no boundary yet): 32
- Moved into this district (KGIS had them elsewhere): 3
- In KGIS for this district but not in LGD, marked is_pilot = false: 3

**Added:** 910262 Chikkahosahalli (D); 910246 Chikkamurali; 948554 Dinne Soluru; 910230 Dinnur; 910253 Haliyur (D); 926008 Jyothipuraa; 948555 Koira Hosur; 910258 Nagenahalli; 948556 P Ranganathpura; 948558 Seekayanahalli; 948559 Singawara; 910264 Yarrappanahalli (D); 910091 Ancharahalli (D); 910208 Bandayyanapalya; 910207 Birayyanapalya; 910219 Boirasandra (Palya); 910087 Hanagalapura (D); 910094 Kudihalli (D); 910080 Mopurahalli (D); 910223 Palapaladinne (D); 910098 Ramayyana Palya; 625032 Sevanagara; 625041 Shivalinga Pura; 910221 Subramanya Ghati (D); 910224 Tiruvanahalli (D); 924477 Chikkakorati; 910284 Ganjaralahalli (D); 910273 Hallevooru (D); 625646 Jadigenahalli; 910292 Venkatapur (B); 910484 Gollarahattii; 924490 Hattugunte Palya

**Moved:** 625761 Chikkahalli (from block 5605); 625949 Hosahalli (from block 5605); 625929 Rangenahalli (from block 5605)

**Not in LGD:** 625872 Chikkanahalli; 625893 Hosahalli; 625869 Rangenahalli
