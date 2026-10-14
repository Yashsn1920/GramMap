const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, LevelFormat, PageBreak, TableOfContents,
  Header, Footer, PageNumber, BorderStyle,
} = require("docx");

const W = 9026; // A4 content width (DXA) with 1" margins
const ACCENT = "1F5C4A";
const LIGHT = "E3EFEA";
const CODEBG = "F2F2F2";

// ---------- helpers ----------
function runs(text, opts = {}) {
  // supports **bold** segments
  const parts = String(text).split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return parts.map((s) =>
    s.startsWith("**")
      ? new TextRun({ text: s.slice(2, -2), bold: true, ...opts })
      : new TextRun({ text: s, ...opts })
  );
}
const P = (t, o = {}) => new Paragraph({ children: runs(t), spacing: { after: 120 }, ...o });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)], pageBreakBefore: true });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });
const B = (t, level = 0) => new Paragraph({ numbering: { reference: "bullets", level }, children: runs(t), spacing: { after: 60 } });
const BL = (arr, level = 0) => arr.map((t) => (Array.isArray(t) ? BL(t, level + 1) : B(t, level))).flat();
const CODE = (lines) =>
  lines.split("\n").map((l, i, a) =>
    new Paragraph({
      shading: { type: ShadingType.CLEAR, color: "auto", fill: CODEBG },
      spacing: { after: i === a.length - 1 ? 160 : 0, line: 240 },
      children: [new TextRun({ text: l.length ? l : " ", font: "Consolas", size: 16 })],
    })
  );
const NOTE = (t) =>
  new Paragraph({
    shading: { type: ShadingType.CLEAR, color: "auto", fill: LIGHT },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color: ACCENT, space: 6 } },
    spacing: { before: 80, after: 160 },
    children: runs(t),
  });

const cellBorder = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };
function T(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const scale = W / total;
  const ws = widths.map((w) => Math.floor(w * scale));
  ws[ws.length - 1] += W - ws.reduce((a, b) => a + b, 0);
  const mk = (txt, i, head) =>
    new TableCell({
      borders,
      width: { size: ws[i], type: WidthType.DXA },
      shading: head ? { type: ShadingType.CLEAR, color: "auto", fill: ACCENT } : undefined,
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: String(txt).split("\n").map((line) =>
        new Paragraph({ children: runs(line, head ? { bold: true, color: "FFFFFF", size: 19 } : { size: 19 }) })
      ),
    });
  return new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: ws,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => mk(h, i, true)) }),
      ...rows.map((r) => new TableRow({ children: r.map((c, i) => mk(c, i, false)) })),
    ],
  });
}
const SP = () => new Paragraph({ children: [], spacing: { after: 80 } });

// Implementation step block
function STEP(s) {
  return [
    H3(`${s.id}  ${s.title}`),
    T(["Field", "Detail"], [
      ["Goal", s.goal],
      ["Depends on", s.dep],
      ["Target week", s.week],
    ], [1800, 7226]),
    P("**Tasks**", { spacing: { before: 120, after: 60 } }),
    ...BL(s.tasks),
    P("**Deliverables**", { spacing: { before: 120, after: 60 } }),
    ...BL(s.out),
    P("**Done when (acceptance criteria)**", { spacing: { before: 120, after: 60 } }),
    ...BL(s.done),
  ];
}

// Progress tracker state: update when a step is finished.
const PROGRESS = {
  "S0.1": ["Done", "14 Oct 2026. Pilot: Bengaluru North. See docs/source_audit.md"],
  "S0.2": ["Done", "14 Oct 2026. PR #1; CI green"],
  "S0.3": ["Done", "14 Oct 2026. PR #2; 18 tests"],
};

// ---------- content ----------
const C = [];

// Title page
C.push(
  new Paragraph({ spacing: { before: 2400 }, children: [] }),
  new Paragraph({ alignment: AlignmentType.LEFT, children: [new TextRun({ text: "GramMap", size: 72, bold: true, color: ACCENT })] }),
  new Paragraph({ children: [new TextRun({ text: "Village Asset Mapping System", size: 40, color: "404040" })], spacing: { after: 240 } }),
  new Paragraph({ children: [new TextRun({ text: "Product Requirements Document and Implementation Guide", size: 28, color: "595959" })], spacing: { after: 600 } }),
  P("A GIS-enabled application that documents community assets (schools, health facilities, water sources, roads and other public infrastructure) for real villages and towns, using only publicly available online data. No field surveys and no LLM services are required."),
  SP(),
  T(["Item", "Value"], [
    ["Document version", "1.2"],
    ["Date", "14 October 2026"],
    ["Status", "Baseline. Changes are tracked in the Change Log (Section 19)."],
    ["Project type", "College project, software only"],
    ["Team", "[Member A], [Member B], [Member C], [Member D]"],
    ["Pilot district", "Bengaluru North (formerly Bengaluru Rural), Karnataka. Chosen in S0.1; see docs/source_audit.md."],
  ], [2600, 6426]),
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Contents")] }),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  P("(In Word, right-click the table above and choose Update Field to refresh page numbers.)", {}),
);

// 1. How to use
C.push(
  H1("1. How to Use This Document"),
  P("This document is both the **specification** (what we are building and why) and the **working guide** (exactly how we build it, step by step). It is the single source of truth for the project. When code and this document disagree, either the code is fixed or this document is updated through the Change Log."),
  H2("1.1 Working protocol"),
  P("We work through the implementation steps in Section 15 in order. Every step follows the same loop:"),
  ...BL([
    "**Read** the step: goal, dependencies, tasks, deliverables and acceptance criteria.",
    "**Branch**: create a git branch named after the step, for example feature/S2.2-osm-connector.",
    "**Build** the tasks. Keep changes inside the step's scope; note anything else as a new item for later.",
    "**Test**: write the tests listed, run them, and check every acceptance criterion.",
    "**Review and merge**: open a pull request that references the step ID; another team member reviews.",
    "**Update the tracker** (Section 16): mark the step Done, record the date and any deviations.",
    "**Move on** to the next step only after the current one meets its acceptance criteria.",
  ]),
  H2("1.2 Conventions used here"),
  ...BL([
    "**FR-x.y**: functional requirement. **NFR-x**: non-functional requirement.",
    "**Sx.y**: implementation step (for example S4.2 is Phase 4, Step 2).",
    "**MVP**: the minimum viable product, the cut line if time runs short (Section 15.1).",
    "Numeric thresholds in this document are starting values. They live in configuration files and may be tuned; tuning is recorded in the Change Log.",
  ]),
);

// 2. Overview
C.push(
  H1("2. Product Overview"),
  H2("2.1 Problem statement"),
  P("Information about public assets in Indian villages, such as schools, health centres, water tanks, hand pumps, anganwadis and roads, is scattered across many separate sources: OpenStreetMap, national school and health registries, rural road databases, Census tables and satellite-derived datasets. No single source is complete; the sources overlap, contradict each other, use different names for the same place, and often lack coordinates. Planners, students and citizens therefore have no simple way to see what a village has, where it is, and what it is missing."),
  H2("2.2 Product vision"),
  NOTE("**Type any real village or town, and within about a minute see a single, de-duplicated map of its community assets, with a confidence score for each asset, a list of what is missing, and an analysis of who lacks access to essential services.**"),
  H2("2.3 Goals"),
  ...BL([
    "**G1 Integrate**: automatically collect asset data for real villages from at least 8 public online sources.",
    "**G2 Conflate**: merge records of the same physical asset into one record with traceable provenance (which source supplied which field).",
    "**G3 Qualify**: give each asset a confidence score and a location-precision level, so users know how much to trust it.",
    "**G4 Reveal gaps**: detect missing or unmapped assets by comparing sources against each other and against official amenity lists.",
    "**G5 Analyze**: compute road-network access to facilities, compare villages against government norms, and recommend sites for new facilities.",
    "**G6 Present**: an interactive web map, village profile pages and downloadable reports and data.",
  ]),
  H2("2.4 Non-goals"),
  ...BL([
    "No field surveys, surveyor apps or physical data collection.",
    "No simulated or synthetic villages; the system works only on real places.",
    "No paid or LLM APIs. All processing is deterministic GIS and classical machine learning.",
    "No guarantee about asset **condition** (for example whether a hand pump works). Condition is rarely available online; the system shows proxies and says so.",
    "Not a replacement for official government records.",
  ]),
  H2("2.5 Constraints"),
  ...BL([
    "Strictly software based, built only from free, publicly accessible data.",
    "Must run on a student laptop (8 to 16 GB RAM) using Docker; deployment to a low-cost server is optional.",
    "Must respect each data source's licence and terms of use (Section 18).",
    "Timeline: about 14 weeks with a team of four.",
  ]),
);

// 3. Users
C.push(
  H1("3. Users and User Stories"),
  H2("3.1 Personas"),
  T(["Persona", "Who", "Main need"], [
    ["Planner", "Block or district development officer, NGO planner", "See which villages lack services and where to place new facilities"],
    ["Researcher or student", "Studies rural development", "Download clean, sourced asset data and statistics"],
    ["Citizen", "Resident or panchayat member", "Look up what facilities exist near a village and report a wrong location"],
    ["Admin", "Our team, operating the system", "Run and monitor data pipelines, review flagged records"],
  ], [1800, 3200, 4026]),
  H2("3.2 User stories"),
  T(["ID", "As a...", "I want to...", "So that..."], [
    ["US-1", "Any user", "search a village by name and open it on the map", "I can see its assets quickly"],
    ["US-2", "Any user", "toggle asset categories and filter by confidence", "I see only what matters to me"],
    ["US-3", "Any user", "click an asset and see which sources reported it", "I can judge whether to trust it"],
    ["US-4", "Planner", "see villages that fail service norms on a colour-coded map", "I can prioritise investment"],
    ["US-5", "Planner", "see which hamlets are more than X km by road from a health facility", "I can identify under-served people"],
    ["US-6", "Planner", "get the best location for one new facility", "I can justify a placement decision"],
    ["US-7", "Planner", "see assets the Census lists but no map shows", "I know where data is missing"],
    ["US-8", "Researcher", "export assets as GeoJSON, KML, Shapefile or CSV", "I can analyze them in QGIS or Python"],
    ["US-9", "Any user", "download a village profile PDF", "I can share or print a summary"],
    ["US-10", "Any user", "map a village outside the pilot district on demand", "the system is useful anywhere"],
    ["US-11", "Citizen", "flag an asset location as wrong", "the data improves over time"],
    ["US-12", "Admin", "review low-confidence matches and flags", "errors are corrected before they spread"],
  ], [900, 1500, 3500, 3126]),
);

// 4. Solution overview
C.push(
  H1("4. Solution Overview"),
  P("The system is a **data integration pipeline** feeding a **GIS web application**. For a given area, it fetches records from many online sources, converts them into one common format, links them to official village codes, merges duplicates into single assets, fills gaps using cross-checks and satellite-derived datasets, runs spatial analyses, and serves the results through an API and an interactive map."),
  H2("4.1 Architecture"),
  ...CODE(
`  +----------------------- SOURCE CONNECTORS (one per source) ------------------------+
  | OSM | Overture | LGD | Boundaries | Census | UDISE+ | Health | PMGSY | Buildings | ... |
  +-------------------------------------------+---------------------------------------+
                                              v
  BRONZE  raw records exactly as fetched (source, fetch time, raw JSON)   -> lineage
                                              v
  SILVER  normalized records: common categories, WGS84 geometry, clean names,
          linked to an LGD village code, location precision assigned
                                              v
  GOLD    conflated assets: one record per real asset, attribute provenance,
          confidence score, links back to every source record
                                              v
     +--------------+---------------+-------------------+------------------+
     | Gap-filling  | Analytics     | REST API +        | Scheduled        |
     | engine       | engine        | vector tiles      | refresh (Celery) |
     +--------------+---------------+---------+---------+------------------+
                                              v
             Web dashboard  |  Village profile PDF  |  Data exports`),
  H2("4.2 Operating modes"),
  T(["Mode", "Description", "Used for"], [
    ["Pilot district (batch)", "The full pipeline runs over every village in one chosen district and results are stored.", "District dashboards, gap maps, optimizer, evaluation"],
    ["On demand", "A user searches a village outside the pilot; the pipeline runs for that village's area only, in the background, and the page updates when done.", "Using the system anywhere; live demo"],
  ], [2200, 4400, 2426]),
  H2("4.3 Data layers"),
  T(["Layer", "Contents", "Rule"], [
    ["Bronze", "Raw source payloads", "Never edited. Re-fetching creates a new version. Enables re-processing without re-downloading."],
    ["Silver", "Normalized source records", "One row per source record. Same schema for all sources."],
    ["Gold", "Conflated assets", "One row per real-world asset. Rebuilt deterministically from silver."],
  ], [1400, 2800, 4826]),
  NOTE("**Design principle: rebuildable.** Gold can always be regenerated from silver, and silver from bronze. Pipeline code is deterministic for a given input and configuration. Every pipeline run is recorded with a run ID, timestamps and counts."),
);

// 5. Data sources
C.push(
  H1("5. Data Sources"),
  P("Each source below is confirmed or rejected during the **source audit (S0.1)**. Government portals change often; access methods and licences must be checked against the live site, and this table updated. The system must work if any single government source is unavailable."),
  H2("5.1 Global open sources"),
  T(["Source", "Provides", "Access method", "Licence (verify)", "Priority"], [
    ["OpenStreetMap", "POIs (schools, hospitals, water towers, wells), roads, water bodies, place names", "Overpass API for small areas; Geofabrik India/state extract for bulk", "ODbL", "Must"],
    ["Overture Maps", "Places (POIs), buildings, transportation, admin divisions", "GeoParquet on cloud storage, read by bounding box with DuckDB", "Mixed by theme (CDLA / ODbL)", "Must"],
    ["Google Open Buildings", "Building footprints with confidence", "Downloadable tiles (CSV/GeoParquet) or Earth Engine", "CC BY 4.0 / ODbL", "Must"],
    ["Microsoft Building Footprints", "Building footprints", "Downloadable by region", "ODbL", "Should"],
    ["Microsoft Road Detections", "ML-detected road lines", "Downloadable by region", "ODbL", "Should"],
    ["WorldPop / Meta population maps", "Population per grid cell (about 100 m / 30 m)", "GeoTIFF download", "CC BY 4.0", "Must"],
    ["JRC Global Surface Water", "Water occurrence and seasonality, 1984 onwards", "Earth Engine or tile download", "Free, attribution", "Should"],
    ["Sentinel-2", "10 m multispectral imagery (water index)", "Earth Engine or Microsoft Planetary Computer", "Copernicus free and open", "Could"],
    ["Copernicus DEM GLO-30", "Elevation (30 m)", "Download / Earth Engine", "Free, attribution", "Should"],
    ["ESA WorldCover", "Land cover (10 m)", "Download / Earth Engine", "CC BY 4.0", "Could"],
    ["Wikidata", "Named institutions with coordinates", "SPARQL endpoint", "CC0", "Could"],
  ], [1700, 2400, 2300, 1500, 1126]),
  H2("5.2 Indian government sources"),
  P("Status after the S0.1 source audit (14 Oct 2026) is shown in brackets. Details are in docs/source_audit.md."),
  T(["Source", "Provides", "Access method", "Licence (verify)", "Priority"], [
    ["**KGIS, Karnataka (KSRSAC)** [Usable]", "Official village and Gram Panchayat boundaries carrying LGD, Census 2011 and GP codes; schools with UDISE codes; GP water supply points; GP buildings; polio immunisation sites; government buildings; bridges", "ArcGIS REST query services at kgis.ksrsac.in (paged, up to 1,000 records per request)", "Government portal; attribute KSRSAC; confirm terms before public release", "Must"],
    ["LGD (Local Government Directory) [Optional]", "Official codes and hierarchy: state, district, sub-district, block, village", "Download pages need a captcha (one-time manual download). KGIS already provides LGD codes.", "GODL-India / site terms", "Could"],
    ["Village boundaries outside Karnataka (SHRUG, Bhuvan, DataMeet)", "Village polygons with Census 2011 codes", "Download (SHRUG shapefiles) or WMS/WFS. DataMeet Karnataka layer has ±500 m error, so KGIS is used instead.", "Check each", "Should"],
    ["Census 2011 Village Directory and PCA", "Amenities present in each village; population", "Census of India / data.gov.in / SHRUG tables", "GODL-India", "Must"],
    ["Mission Antyodaya [Blocked]", "Village infrastructure survey (2020)", "Portal does not resolve; try data.gov.in / AIKosh copies in S2.6", "Site terms", "Could"],
    ["UDISE+ / School GIS (NIC) [Partial]", "School directory, codes, enrolment, teachers, facilities", "geoportal.nic.in REST service (connection refused from our network); public school-count API", "Site terms", "Should"],
    ["National Health Facility Registry; National Hospital Directory (data.gov.in) [Blocked]", "Health facilities, type, location", "NHFR needs login; data.gov.in needs a free API key (retry in S2.5)", "GODL-India / site terms", "Could"],
    ["**PMGSY GeoSadak** [Usable]", "Rural habitations with population; geotagged rural facilities (education, medical, admin, agro); rural roads", "DataMeet GitHub mirror github.com/datameet/pmgsy-geosadak (2022 snapshot); official portal unreachable", "GODL-India", "Must"],
    ["Jal Jeevan Mission dashboard", "Village tap-water coverage", "Dashboard reports", "Site terms", "Could"],
    ["data.gov.in (other)", "Post offices, bank branches, anganwadis (varies by state)", "data.gov.in API (free key)", "GODL-India", "Could"],
  ], [1900, 2400, 2100, 1500, 1126]),
  NOTE("**Fallback rule:** if a government source has no coordinates, we still ingest it and place assets using the geocoding fallback (Section 7.4). If it cannot be accessed at all, we document this and continue; the 'value added by each source' evaluation (Section 13) shows the impact."),
);

// 6. Functional requirements
C.push(
  H1("6. Functional Requirements"),
  H2("6.1 Village resolution (FR-1)"),
  T(["ID", "Requirement", "Priority"], [
    ["FR-1.1", "Search villages and towns by name with fuzzy matching and transliteration variants; show state, district and block to tell same-named places apart.", "Must"],
    ["FR-1.2", "Resolve a selection to an LGD code, a boundary polygon and an analysis bounding box (boundary buffered by 5 km).", "Must"],
    ["FR-1.3", "If no boundary exists, use a fallback area: a buffer around the settlement's building cluster, flagged as approximate.", "Should"],
    ["FR-1.4", "Allow selecting a village by clicking the map.", "Should"],
  ], [900, 7100, 1026]),
  H2("6.2 Data ingestion (FR-2)"),
  T(["ID", "Requirement", "Priority"], [
    ["FR-2.1", "Each source has a connector that can fetch by bounding box or by administrative code.", "Must"],
    ["FR-2.2", "Raw responses are stored in bronze with source name, fetch time, query parameters and a content hash.", "Must"],
    ["FR-2.3", "Connectors cache responses, respect rate limits and retry with back-off.", "Must"],
    ["FR-2.4", "Re-running a connector with unchanged upstream data creates no duplicate records (idempotent).", "Must"],
    ["FR-2.5", "Each run records counts fetched, normalized, rejected, and any errors.", "Must"],
  ], [900, 7100, 1026]),
  H2("6.3 Normalization (FR-3)"),
  T(["ID", "Requirement", "Priority"], [
    ["FR-3.1", "Map every source's types and tags to the common category taxonomy (Section 7.2).", "Must"],
    ["FR-3.2", "Convert all geometry to WGS84 (EPSG:4326) and validate it.", "Must"],
    ["FR-3.3", "Normalize names: lower-case, remove punctuation, expand abbreviations, transliterate to a common Latin form, remove generic words.", "Must"],
    ["FR-3.4", "Link each record to an LGD village code using a point-in-polygon test, or the source's own code when supplied.", "Must"],
    ["FR-3.5", "Assign a location precision: exact, matched or approximate.", "Must"],
  ], [900, 7100, 1026]),
  H2("6.4 Conflation (FR-4)"),
  T(["ID", "Requirement", "Priority"], [
    ["FR-4.1", "Generate candidate pairs of the same category within a category-specific distance.", "Must"],
    ["FR-4.2", "Score candidates on distance, name similarity and shared identifiers.", "Must"],
    ["FR-4.3", "Merge matched records into one gold asset; keep links to every source record.", "Must"],
    ["FR-4.4", "Choose each attribute from the most authoritative source for that field and store its provenance.", "Must"],
    ["FR-4.5", "Compute a confidence score (0 to 1) for each asset.", "Must"],
    ["FR-4.6", "Send uncertain pairs to a review queue; admins can confirm or reject a match.", "Should"],
    ["FR-4.7", "Train a match classifier on hand-labelled pairs to replace the fixed threshold.", "Should"],
  ], [900, 7100, 1026]),
  H2("6.5 Gap-filling and quality (FR-5)"),
  T(["ID", "Requirement", "Priority"], [
    ["FR-5.1", "Compare Census / Mission Antyodaya amenities with found assets: flag Missing and Unlisted assets.", "Must"],
    ["FR-5.2", "Detect settlements (hamlets) from building footprints and estimate their population.", "Must"],
    ["FR-5.3", "Flag ML-detected roads absent from OSM as likely unmapped roads.", "Should"],
    ["FR-5.4", "Compute water-body permanence and multi-year trend for ponds and tanks.", "Could"],
    ["FR-5.5", "Flag quality issues: asset outside its village, in a water body, impossible attribute values, stale data.", "Must"],
    ["FR-5.6", "Compute a data completeness score per village.", "Must"],
  ], [900, 7100, 1026]),
  H2("6.6 Analytics (FR-6)"),
  T(["ID", "Requirement", "Priority"], [
    ["FR-6.1", "Build a road network graph from OSM with travel speeds per road class.", "Must"],
    ["FR-6.2", "Compute road distance and travel time from every settlement to the nearest facility of each category.", "Must"],
    ["FR-6.3", "Draw isochrones (areas reachable within N minutes or km) around a chosen facility.", "Must"],
    ["FR-6.4", "Evaluate villages against a configurable norms table; compute a gap score (0 to 100).", "Must"],
    ["FR-6.5", "Recommend the best p sites for new facilities (maximal coverage optimization).", "Should"],
    ["FR-6.6", "What-if: add a hypothetical facility or block a road segment and recompute access.", "Should"],
    ["FR-6.7", "Risk overlay: flag assets in flood-prone or low-lying areas.", "Could"],
  ], [900, 7100, 1026]),
  H2("6.7 Presentation and output (FR-7)"),
  T(["ID", "Requirement", "Priority"], [
    ["FR-7.1", "Interactive map with category layers, clustering, legend, satellite toggle and search.", "Must"],
    ["FR-7.2", "Asset detail panel showing attributes, confidence, precision and per-field provenance.", "Must"],
    ["FR-7.3", "Village page with asset summary, gaps, access statistics and completeness.", "Must"],
    ["FR-7.4", "District view with choropleth maps (gap score, completeness, access).", "Must"],
    ["FR-7.5", "Exports: GeoJSON, KML, Shapefile (zipped), CSV.", "Must"],
    ["FR-7.6", "One-click village profile PDF.", "Should"],
    ["FR-7.7", "On-demand mapping with a progress indicator.", "Should"],
    ["FR-7.8", "Citizens can flag a wrong location; flags enter the review queue.", "Could"],
    ["FR-7.9", "Attribution for every data source displayed on the map and in exports.", "Must"],
  ], [900, 7100, 1026]),
  H2("6.8 Administration (FR-8)"),
  T(["ID", "Requirement", "Priority"], [
    ["FR-8.1", "Roles: Admin, Reviewer, Viewer (anonymous viewing allowed).", "Must"],
    ["FR-8.2", "Admin page to trigger pipeline runs and view run history and errors.", "Should"],
    ["FR-8.3", "Scheduled refresh of sources (weekly for OSM, monthly for others).", "Should"],
    ["FR-8.4", "Audit log of manual edits and review decisions.", "Should"],
  ], [900, 7100, 1026]),
);

// 7. Detailed solution approach
C.push(
  H1("7. Detailed Solution Approach"),
  P("This section specifies **how** each part works. Implementation steps in Section 15 refer back here."),

  H2("7.1 Village resolver"),
  ...BL([
    "**Master list (Karnataka):** load village polygons from KGIS; each already carries its LGD village code, Census 2011 code and LGD Gram Panchayat code, so no separate code join is needed. Villages split into several polygons are merged by village code. (Other states: load the LGD village table, join Census codes, then attach boundary polygons by Census code.)",
    "**Search index:** for every village store the name, the normalized name and transliteration variants (from the indic-transliteration library). Use PostgreSQL trigram similarity (pg_trgm) for fast fuzzy search, and re-rank the top 50 results with rapidfuzz.",
    "**Disambiguation:** results always display 'Village, Block, District, State'.",
    "**Analysis area:** boundary buffered by 5 km (configurable), so nearby facilities just outside the village are included in access analysis.",
    "**No boundary:** take Open Buildings footprints within 2 km of the LGD or OSM place point, cluster them (Section 7.6) and use the convex hull of the main cluster, buffered by 300 m. Flag the village boundary_precision = approximate.",
  ]),

  H2("7.2 Category taxonomy"),
  P("All sources map to this fixed list (stored in config/categories.yaml). Matching distance is used by conflation (Section 7.5)."),
  T(["Code", "Category", "Example source mappings", "Geometry", "Match distance"], [
    ["SCH", "School", "OSM amenity=school; Overture education; UDISE+", "Point", "150 m"],
    ["COL", "College", "OSM amenity=college/university", "Point", "200 m"],
    ["HLT", "Health facility (with subtype: SC, PHC, CHC, hospital, clinic)", "OSM amenity=hospital/clinic/doctors, healthcare=*; NHFR", "Point", "150 m"],
    ["AWC", "Anganwadi centre", "data.gov.in lists; OSM name contains 'anganwadi'", "Point", "100 m"],
    ["WTR", "Water tank / tower", "OSM man_made=water_tower / storage_tank (content=water)", "Point", "50 m"],
    ["WEL", "Well / hand pump / tap", "OSM man_made=water_well, amenity=drinking_water", "Point", "30 m"],
    ["PND", "Pond / tank (water body)", "OSM natural=water, water=pond/reservoir; JRC", "Polygon", "Overlap"],
    ["ROD", "Road", "OSM highway=*; PMGSY; MS road detections", "Line", "Buffer 15 m"],
    ["GOV", "Panchayat / government office", "OSM office=government, amenity=townhall", "Point", "150 m"],
    ["PST", "Post office", "OSM amenity=post_office; India Post list", "Point", "150 m"],
    ["BNK", "Bank / ATM", "OSM amenity=bank/atm; Overture", "Point", "100 m"],
    ["MKT", "Market", "OSM amenity=marketplace", "Point", "200 m"],
    ["REL", "Place of worship", "OSM amenity=place_of_worship", "Point", "75 m"],
    ["OTH", "Other community asset", "Community halls, libraries, police", "Point", "100 m"],
  ], [800, 2200, 3500, 1100, 1426]),

  H2("7.3 Name normalization"),
  P("Applied to every record name before matching. Implemented as a pure function with unit tests for many real examples."),
  ...BL([
    "Lower-case; strip punctuation and extra spaces; convert Devanagari and other Indic scripts to Latin (ITRANS-style) form.",
    "Expand common abbreviations: govt to government, gps/g.p.s. to government primary school, phc to primary health centre, chc, sc, hs, ups, mps, zp, etc. (dictionary in config/abbreviations.yaml).",
    "Normalize spelling variants of common words: vidyalaya/vidhyalay, prathamik/prathmik, rajkiya.",
    "Remove generic tokens for the comparison key (school, government, primary, the, of, village names) while keeping the full normalized name for display.",
    "Output: display_name, norm_name (full) and key_tokens (distinctive words).",
  ]),

  H2("7.4 Geocoding fallback for records without coordinates"),
  P("Many government lists give a village name or code but no coordinates. Processing order:"),
  ...BL([
    "**1. Link to village:** use the source's village code (LGD or Census). If only a name is given, fuzzy-match within the stated block or district.",
    "**2. Find a named match nearby:** search OSM and Overture POIs of the same category inside the village area. If one has a name similarity of 80 or more, take its coordinates and set precision = matched.",
    "**3. Settlement centroid:** otherwise place the record at the centroid of the village's largest building cluster (not the polygon centre, which may be farmland) and set precision = approximate.",
    "Records placed by step 3 are shown with a dashed marker and are excluded from distance-sensitive analysis unless the user includes them.",
  ]),

  H2("7.5 Conflation engine"),
  H3("Candidate generation"),
  P("For each category, find pairs of silver records from **different sources** within the category's match distance using PostGIS ST_DWithin on geography. Records with a shared official identifier (for example a UDISE code present in both) are always candidates regardless of distance."),
  H3("Pair scoring"),
  ...CODE(
`dist_score  = max(0, 1 - distance_m / match_distance[category])
name_score  = token_set_ratio(key_tokens_a, key_tokens_b) / 100     # rapidfuzz
attr_score  = 1 if subtypes agree, 0.5 if unknown, 0 if they conflict

if shared_official_id:          score = 1.0
elif both names present:        score = 0.45*dist_score + 0.45*name_score + 0.10*attr_score
else (one or both unnamed):     score = 0.85*dist_score + 0.15*attr_score

score >= 0.75          -> match
0.50 <= score < 0.75   -> uncertain (classifier from S4.3 decides; else review queue)
score < 0.50           -> no match`),
  H3("Clustering and merging"),
  ...BL([
    "Matched pairs form a graph; each connected component (union-find) becomes one gold asset.",
    "**Guard:** if a component contains two records from the same source that are more than the match distance apart, split it at the weakest link. This prevents chains of matches from merging two separate schools.",
    "**Geometry:** taken from the most precise and most authoritative source available. Order for points: government source with exact coordinates, then OSM, then Overture, then matched, then approximate.",
    "**Attributes:** each field has a source priority list in config/field_priority.yaml (for example enrolment: UDISE+; facility type: NHFR; name: government source, then OSM). The chosen source and its date are stored in attribute_provenance.",
  ]),
  H3("Confidence score"),
  ...CODE(
`source_weight:  govt registry with coords 0.80 | OSM 0.70 | Overture 0.60
                govt registry, geocoded 0.40 | single ML-derived layer 0.50
recency(age):   < 2 years 1.0 | 2-5 years 0.8 | > 5 years 0.6

support    = 1 - PRODUCT over sources s of (1 - source_weight[s] * recency[s])
precision  = exact 1.0 | matched 0.9 | approximate 0.6
confidence = round(support * precision, 2)

Display:  >= 0.80 High   |   0.50 - 0.79 Medium   |   < 0.50 Low`),

  H2("7.6 Settlements and population"),
  ...BL([
    "Take building footprints (Open Buildings; keep those with model confidence of 0.70 or more) inside the analysis area, add Microsoft footprints that do not overlap them.",
    "Project centroids to the local UTM zone and run DBSCAN (eps = 50 m, min_samples = 5). Each cluster is a settlement (hamlet); its polygon is the concave hull of its buildings.",
    "**Population:** sum WorldPop (or Meta) population inside the village, then distribute it to settlements in proportion to their total building footprint area. Store population_est and building_count.",
    "Settlement centroids are snapped to the nearest road network node for routing.",
  ]),

  H2("7.7 Expected-versus-found gap detection"),
  ...BL([
    "Load amenity indicators for each village from the Census Village Directory and, where available, Mission Antyodaya (for example: primary school yes/no and count, PHC, sub-centre, drinking water source types, paved road access).",
    "For each indicator, compare with gold assets of the matching category inside the village.",
    "**Missing:** listed as present but no asset found. **Unlisted:** asset found but not listed (possibly new since the Census). **Count mismatch:** both exist but counts differ.",
    "Store each as a GapFlag with its evidence (source and value) so the user can see why it was raised.",
  ]),

  H2("7.8 Unmapped road detection"),
  ...BL([
    "Buffer OSM roads by 15 m. For every Microsoft road-detection line, measure the share of its length outside that buffer.",
    "If more than 70% lies outside and the outside part is longer than 100 m, flag it as a likely unmapped road (shown as a dashed orange line).",
    "Optionally export flagged roads as a MapRoulette challenge so OSM volunteers can verify and add them (contributing back without field work).",
  ]),

  H2("7.9 Water body analysis (optional module)"),
  ...BL([
    "Ponds and tanks come from OSM water polygons plus polygons extracted from JRC occurrence greater than 25%.",
    "From JRC (yearly history) compute, per polygon: permanence (share of months with water) and a multi-year trend of water area (linear regression slope).",
    "Optionally confirm recent years with a Sentinel-2 NDWI composite for the dry season.",
    "Label: Permanent, Seasonal, or Drying (statistically negative trend). This acts as a condition proxy for water assets.",
  ]),

  H2("7.10 Road network and accessibility"),
  ...BL([
    "Download the drivable and walkable OSM network for the district with osmnx; load edges into PostGIS (table road_edge with source and target node IDs, length and cost columns) for use with pgRouting.",
    "**Speeds (configurable):** walking 4.5 km/h on all roads and paths; driving: primary 50, secondary 40, tertiary 30, residential/unclassified 25, track 15 km/h.",
    "**Nearest facility per settlement:** run pgr_drivingDistance from all facility nodes of a category at once (equal-cost mode), which gives, for every node, the nearest facility and its cost. Settlements read their snapped node's value.",
    "**Isochrones:** for a chosen facility, take nodes within N minutes and build a concave hull, drawn as bands (for example 15 / 30 / 60 minutes).",
    "**What-if:** add a temporary facility node or set a blocked edge's cost to infinity, rerun for the affected area, and show before-versus-after.",
    "Results stored in settlement_access (settlement, category, mode, distance_m, time_min, nearest_asset).",
  ]),

  H2("7.11 Norms and gap score"),
  P("Norms live in config/norms.yaml so they can be changed without code. Starting values below come from widely cited Indian guidelines (RTE norms for schools, IPHS for health). They must be checked against current official documents during S7.3 and cited in the report."),
  T(["Norm", "Rule (starting value)", "Weight"], [
    ["Primary school access", "Every settlement within 1 km by road of a primary school", "15"],
    ["Upper primary access", "Within 3 km", "10"],
    ["Secondary school access", "Within 5 km", "10"],
    ["Sub-centre", "One per 5,000 people (plains) / 3,000 (hilly or tribal)", "10"],
    ["PHC", "One per 30,000 (plains) / 20,000 (hilly or tribal); within 10 km", "15"],
    ["CHC", "One per 120,000 (plains) / 80,000 (hilly or tribal)", "5"],
    ["Drinking water", "At least one mapped drinking water source per settlement", "15"],
    ["All-weather road", "Village connected by a paved road (OSM surface or PMGSY)", "10"],
    ["Anganwadi", "At least one per village (finer norms by population optional)", "10"],
  ], [2400, 5226, 1400]),
  ...CODE(
`For each norm n and village v:
   met(n, v) = share of population (or settlements) satisfying the rule, 0..1
gap_score(v) = 100 * SUM_n weight_n * (1 - met(n, v)) / SUM_n weight_n
0 = all norms met, 100 = none met.  Shown as a district choropleth.`),

  H2("7.12 Facility location optimizer"),
  P("Maximal Coverage Location Problem (MCLP), solved with PuLP and the bundled CBC solver."),
  ...CODE(
`Inputs:  demand points i (settlements) with population w_i
         candidate sites j (settlement centroids and road junctions in the area)
         coverage threshold S (for example 5 km by road), number of new facilities p
         existing facilities (their coverage counts as already satisfied)
N_i    = candidate sites within S of demand point i (from network distances)

maximize    SUM_i  w_i * y_i
subject to  y_i <= SUM_{j in N_i} x_j      for every uncovered demand point i
            SUM_j  x_j  = p
            x_j, y_i in {0, 1}

Output:  chosen sites, population newly covered, coverage before vs after.
Baseline for evaluation: random placement and greedy placement.`),

  H2("7.13 Completeness score"),
  ...CODE(
`completeness(v) = 100 * ( 0.4 * share of expected categories found
                        + 0.3 * share of assets with exact or matched precision
                        + 0.2 * min(1, mean sources per asset / 2)
                        + 0.1 * share of assets confirmed in the last 2 years )`),

  H2("7.14 On-demand pipeline"),
  ...BL([
    "User selects a village outside the pilot; the API creates a PipelineRun and queues a Celery job, returning the run ID.",
    "The job runs, for the analysis area only: resolver, all fast connectors (OSM Overpass, Overture via DuckDB, buildings, population, local government data already ingested in bulk), normalization, conflation, settlements, expected-vs-found, access for the area.",
    "Slow optional modules (water trend, road gaps) run afterwards and update the page when ready.",
    "The front end polls the run status every 2 seconds and shows a step-by-step progress list.",
    "Target: core results in under 90 seconds for a typical village.",
  ]),
);

// 8. NFRs
C.push(
  H1("8. Non-Functional Requirements"),
  T(["ID", "Area", "Requirement"], [
    ["NFR-1", "Performance", "District map (up to about 1,500 villages) loads in under 3 s; API p95 latency under 500 ms for map and detail queries; on-demand core pipeline under 90 s per village."],
    ["NFR-2", "Reproducibility", "Same inputs and configuration give the same gold output. Every run stores run ID, config hash, source versions and counts."],
    ["NFR-3", "Resilience", "Failure of one connector never stops the pipeline; the run completes with a warning and the missing source is shown in the UI."],
    ["NFR-4", "Portability", "Whole system starts with 'docker compose up' on Linux, macOS or Windows (WSL2), 8 to 16 GB RAM."],
    ["NFR-5", "Data integrity", "All stored geometry is valid and in EPSG:4326; metric calculations use geography type or the local UTM zone."],
    ["NFR-6", "Transparency", "Every gold asset and every flag can be traced back to its source records."],
    ["NFR-7", "Legal", "Source attribution shown on map and in exports; licences respected (Section 18)."],
    ["NFR-8", "Security", "Admin and reviewer endpoints require authentication (JWT); public endpoints are read-only; secrets kept in .env, never committed; rate limiting on public API."],
    ["NFR-9", "Usability", "Usable on a phone browser (responsive layout); clear legend; plain-language labels for confidence and precision."],
    ["NFR-10", "Quality", "Pipeline modules have unit tests (target coverage 70% or more); CI runs lint and tests on every pull request."],
  ], [1000, 1700, 6326]),
);

// 9. Data model
C.push(
  H1("9. Data Model"),
  P("PostgreSQL 16 with PostGIS, pgRouting and pg_trgm. All geometry columns use SRID 4326 and have GiST indexes. Django models mirror these tables."),
  ...CODE(
`-- Administrative backbone
state(code PK, name)
district(code PK, state_code FK, name, boundary MULTIPOLYGON)
block(code PK, district_code FK, name)
village(lgd_code PK, census_code, gp_lgd_code, block_code FK, name, norm_name,
        name_variants TEXT[], boundary MULTIPOLYGON, boundary_precision,
        population_census, population_est, completeness_score, gap_score,
        is_pilot BOOL, last_processed_at)

-- Lineage
pipeline_run(id PK, kind[batch|on_demand], scope JSONB, status, config_hash,
             started_at, finished_at, stats JSONB, errors JSONB)
bronze_record(id PK, source, query JSONB, fetched_at, content_hash, payload JSONB,
              run_id FK)
source_record(id PK, source, source_id, bronze_id FK, category, subtype,
              name, norm_name, key_tokens TEXT[], official_ids JSONB,
              attributes JSONB, geom GEOMETRY, location_precision,
              village_lgd FK, source_date, is_active BOOL)          -- silver

-- Gold
asset(id PK, category, subtype, name, geom GEOMETRY, village_lgd FK,
      attributes JSONB, attribute_provenance JSONB, confidence NUMERIC,
      location_precision, source_count INT, first_seen, last_confirmed,
      review_status[auto|confirmed|rejected])
asset_source_link(asset_id FK, source_record_id FK, match_score NUMERIC)
match_review(id PK, record_a FK, record_b FK, score, decision, decided_by, decided_at)

-- Derived
settlement(id PK, village_lgd FK, geom POLYGON, centroid POINT,
           building_count, population_est, road_node_id)
road_edge(id PK, source BIGINT, target BIGINT, geom LINESTRING, highway,
          surface, length_m, cost_walk_s, cost_drive_s, is_blocked BOOL)
settlement_access(settlement_id FK, category, mode, distance_m, time_min,
                  nearest_asset_id FK)
expected_amenity(village_lgd FK, category, source, expected_count, source_year)
gap_flag(id PK, village_lgd FK, kind, category, geom GEOMETRY NULL,
         evidence JSONB, status[open|resolved|dismissed], created_at)
water_body(id PK, geom MULTIPOLYGON, permanence NUMERIC, trend_slope NUMERIC, label)

-- Users and feedback
user(id PK, email, role[admin|reviewer|viewer])
correction_flag(id PK, asset_id FK, suggested_geom POINT, note, status, created_at)
audit_log(id PK, user_id, action, object_type, object_id, diff JSONB, at)`),
);

// 10. API
C.push(
  H1("10. API Specification"),
  P("REST API under /api/v1, documented automatically with OpenAPI (drf-spectacular) at /api/docs. Responses are JSON; spatial responses are GeoJSON. Vector tiles are served separately by Martin at /tiles."),
  T(["Method and path", "Purpose"], [
    ["GET /villages/search?q=&district=", "Fuzzy village search"],
    ["GET /villages/{lgd}", "Village profile: boundary, stats, scores"],
    ["GET /villages/{lgd}/assets?category=&min_conf=", "Assets in a village (GeoJSON)"],
    ["GET /villages/{lgd}/gaps", "Gap flags with evidence"],
    ["GET /villages/{lgd}/access", "Settlement access table"],
    ["GET /villages/{lgd}/report.pdf", "Village profile PDF"],
    ["POST /villages/{lgd}/process", "Start on-demand pipeline; returns run ID"],
    ["GET /runs/{id}", "Pipeline run status and progress"],
    ["GET /assets/{id}", "Asset detail with provenance and linked source records"],
    ["GET /districts/{code}/summary", "District statistics and choropleth values"],
    ["GET /analysis/isochrone?asset=&mode=&minutes=", "Isochrone polygons"],
    ["POST /analysis/optimize", "Body: district or village, category, p, threshold. Returns sites and coverage."],
    ["POST /analysis/whatif", "Body: added facilities and/or blocked edges. Returns access change."],
    ["GET /export?scope=&format=geojson|kml|shp|csv", "Data export with attribution file"],
    ["POST /assets/{id}/flags", "Citizen correction flag"],
    ["GET/POST /review/matches", "Reviewer queue for uncertain matches (auth)"],
    ["POST /admin/runs", "Start batch run for a district (auth)"],
    ["POST /auth/token", "Obtain JWT"],
  ], [4200, 4826]),
);

// 11. Frontend
C.push(
  H1("11. User Interface"),
  T(["Screen", "Contents"], [
    ["Home / district map", "Search bar; district choropleth with a switcher (gap score, completeness, health access, school access); click a village to open it."],
    ["Village page", "Map with boundary, settlements and asset layers; side panel with summary cards (asset counts, gap score, completeness, population); tabs for Assets, Gaps, Access and Sources; buttons for PDF and export."],
    ["Asset drawer", "Name, category and subtype, confidence badge, precision label, attributes table with a source and date for each field, list of source records, 'Report wrong location' action."],
    ["Analysis tools", "Isochrone tool (pick a facility, mode, minutes); what-if mode (add facility, block road); optimizer form and result map with before-after coverage."],
    ["Data quality", "Lists of missing assets, unmapped roads and low-confidence assets, with filters and links to the map."],
    ["On-demand progress", "Step-by-step progress list while a new village is processed."],
    ["Review queue (auth)", "Side-by-side comparison of two records on a mini map with Match / Not a match buttons."],
    ["Admin (auth)", "Pipeline runs, statuses, error logs, trigger buttons."],
    ["About / sources", "Methodology summary and full attribution list."],
  ], [2200, 6826]),
  H2("11.1 Map styling rules"),
  ...BL([
    "One icon and colour per category, used consistently in map, legend, charts and PDF.",
    "Marker style shows precision: solid outline = exact, thin outline = matched, dashed outline = approximate.",
    "Marker opacity shows confidence: High 100%, Medium 75%, Low 50%.",
    "Flags (missing assets, unmapped roads) are drawn in a distinct warning colour.",
    "Colour scales for choropleths are colour-blind safe and work in light and dark themes.",
  ]),
);

// 12. Tech stack and repo
C.push(
  H1("12. Technology Stack and Repository"),
  T(["Concern", "Choice", "Reason"], [
    ["Language (pipelines, backend)", "Python 3.12", "Best GIS and data ecosystem"],
    ["GIS libraries", "GeoPandas, Shapely 2, pyproj, rasterio, osmnx, DuckDB (spatial extension)", "Vector, raster, OSM networks, fast GeoParquet queries"],
    ["Matching and ML", "rapidfuzz, indic-transliteration, scikit-learn", "Fuzzy names, transliteration, match classifier and DBSCAN"],
    ["Optimization", "PuLP with CBC", "Free integer programming solver"],
    ["Satellite (optional)", "Google Earth Engine Python API, or Planetary Computer with stackstac", "Free for non-commercial / academic use"],
    ["Database", "PostgreSQL 16 + PostGIS + pgRouting + pg_trgm", "Spatial queries, routing, fuzzy search"],
    ["Backend", "Django 5 + GeoDjango + Django REST Framework + drf-spectacular + SimpleJWT", "Spatial ORM, built-in admin, auto API docs"],
    ["Jobs", "Celery + Redis + Celery Beat", "Background pipelines and schedules"],
    ["Vector tiles", "Martin", "Fast tiles straight from PostGIS"],
    ["Frontend", "React + TypeScript + Vite, MapLibre GL JS, deck.gl, Recharts, Tailwind CSS, TanStack Query", "Modern map UI and data fetching"],
    ["PDF", "WeasyPrint (HTML to PDF), static map images rendered with matplotlib/contextily", "Simple templated reports"],
    ["Quality", "pytest, ruff, black, mypy (pipelines), ESLint, Prettier, Vitest", "Consistent code and tests"],
    ["DevOps", "Docker Compose, GitHub Actions", "One-command setup, CI"],
  ], [2000, 4000, 3026]),
  H2("12.1 Repository layout"),
  ...CODE(
`grammap/
  docker-compose.yml          .env.example          README.md
  config/
    categories.yaml           # taxonomy + source tag mappings + match distances
    sources.yaml              # endpoints, rate limits, weights, enabled flags
    field_priority.yaml       # which source wins for each attribute
    abbreviations.yaml        # name normalization dictionary
    norms.yaml                # service norms and weights
    speeds.yaml               # road speeds per class and mode
    pipeline.yaml             # numeric thresholds for resolver, conflation, confidence, ...
  pipelines/                  # pure Python package, no Django imports
    connectors/  base.py  osm.py  overture.py  lgd.py  boundaries.py  census.py
                 udise.py  health.py  pmgsy.py  buildings.py  population.py ...
    normalize/   categories.py  names.py  geocode.py  village_link.py
    conflate/    candidates.py  scoring.py  cluster.py  merge.py  confidence.py
    gapfill/     settlements.py  expected.py  roads.py  water.py  quality.py
    analytics/   network.py  access.py  isochrone.py  norms.py  optimize.py
                 completeness.py
    flows/       batch_district.py  on_demand_village.py
    tests/
  backend/
    grammap/                  # Django settings, urls, celery
    apps/ geo/  sources/  assets/  analytics/  reports/  accounts/  review/
  frontend/
    src/  components/  pages/  map/  api/  hooks/  styles/
  data/                       # local cache and downloads (git-ignored)
  notebooks/                  # exploration only, never imported by code
  docs/                       # this PRD, decisions log, evaluation results`),
  H2("12.2 Engineering conventions"),
  ...BL([
    "**Branches:** main is always runnable. Work happens on feature/S<step>-<short-name>. Merge by pull request with one reviewer.",
    "**Commits:** start with the step ID, for example 'S4.2: add pair scoring with weights from config'.",
    "**Configuration over code:** thresholds, weights, mappings and norms live in config/*.yaml, never hard-coded.",
    "**Pipelines are pure:** functions take GeoDataFrames or plain data and return results; database reads and writes happen only in flows. This keeps them testable.",
    "**Coordinates:** store in EPSG:4326; compute distances with geography or by projecting to the district's UTM zone (India spans zones 42N to 47N).",
    "**Every new module ships with tests** using small fixture files (a few dozen records) stored in pipelines/tests/fixtures.",
    "**Decisions log:** any choice that changes this document gets a dated entry in docs/decisions.md and the Change Log.",
  ]),
);

// 13. Testing & evaluation
C.push(
  H1("13. Testing and Evaluation"),
  H2("13.1 Testing levels"),
  T(["Level", "What", "Tool"], [
    ["Unit", "Name normalization, scoring, confidence, norms, optimizer on toy inputs", "pytest"],
    ["Connector", "Each connector against recorded responses (no live network in CI)", "pytest + saved fixtures"],
    ["Integration", "Full flow on a small fixture village: bronze to gold to analytics", "pytest + PostGIS in Docker"],
    ["API", "Endpoints, permissions, GeoJSON validity", "DRF test client"],
    ["Frontend", "Key components and pages", "Vitest, manual checklist"],
    ["Performance", "API latency and on-demand pipeline time", "Locust, timing logs"],
  ], [1600, 5000, 2426]),
  H2("13.2 Evaluation without field work"),
  P("Ground truth comes from **desk-based labelling**: team members compare records and satellite imagery on screen. No travel is needed."),
  T(["Question", "Method", "Metric"], [
    ["How accurate is conflation?", "Label about 300 random candidate pairs as match / no match (stratified by score)", "Precision, recall, F1 (rule-based vs classifier)"],
    ["How accurate are locations?", "For 100 random assets, check the marker against imagery and visible labels", "Share within 50 m; median error by precision class"],
    ["How complete is the map?", "Compare found assets with Census / Mission Antyodaya amenity lists", "Coverage % per category"],
    ["What does each source add?", "Re-run gold with sources added one at a time", "Coverage gain per source (chart)"],
    ["Are flagged roads real?", "Check 100 flagged unmapped roads against imagery", "Precision"],
    ["Does the optimizer help?", "Compare with random and greedy placement", "Extra population covered"],
    ["Is it fast enough?", "Time 20 on-demand runs; load-test API", "Median and p95 times"],
  ], [2400, 4000, 2626]),
  H2("13.3 Labelling tool"),
  P("A small internal page (part of the review queue) shows two records side by side on a satellite mini-map with their attributes, and stores Match / Not a match / Unsure. The same labels train the classifier in S4.3 and are used for evaluation; a held-out 30% is never used for training."),
);

// 14. Risks
C.push(
  H1("14. Risks and Mitigations"),
  T(["Risk", "Impact", "Mitigation"], [
    ["Government portal blocks bulk access or changes format", "Fewer sources", "Source audit first (S0.1); cache downloads; system works without any single source; document the gap"],
    ["OSM is sparse in the pilot district", "Low coverage", "Choose a pilot district with reasonable OSM coverage during S0.1; lean on Overture and government lists; road-gap module shows the problem"],
    ["Village name spellings do not match across sources", "Poor linking", "Join by codes wherever possible; transliteration plus fuzzy matching; review queue"],
    ["Government coordinates are wrong (for example 0,0 or district centre)", "Bad locations", "Quality checks: outside village, duplicated coordinates across many records, distance from settlement; downgrade precision"],
    ["LGD-to-Census-to-boundary codes do not join cleanly", "Missing boundaries", "Resolved for Karnataka: KGIS polygons carry LGD and Census codes. Elsewhere: fallback boundary from building clusters (Section 7.1); track join rate as a metric"],
    ["Slow bulk downloads from OSM mirrors on the home network (about 5 KB/s)", "Cannot fetch OSM extracts at home", "Use Overpass per area with retries and mirror switching; download the Karnataka extract once on a faster network"],
    ["Earth Engine account approval is slow", "Water module delayed", "Water module is optional; alternative: Planetary Computer or direct JRC tile download"],
    ["Large datasets exceed laptop memory", "Slow or failed runs", "Process by district or tile; use DuckDB to filter GeoParquet by bounding box; never load national files whole"],
    ["Schedule overrun", "Unfinished features", "Strict MVP cut line (Section 15.1); optional modules last"],
    ["Licence misuse (for example Google Maps data)", "Legal and academic risk", "Only sources in Section 5; display-only basemaps; attribution everywhere"],
  ], [3000, 1700, 4326]),
);

// 15. Implementation plan
const steps = [
  // Phase 0
  { phase: "Phase 0: Foundations (Weeks 1 to 2)" },
  { id: "S0.1", title: "Source audit and pilot district selection", week: "1", dep: "None",
    goal: "Know exactly which sources work, how to access them, and pick a pilot district.",
    tasks: [
      "Shortlist 2 or 3 candidate districts (ideally one the team knows, with moderate OSM coverage).",
      "For each source in Section 5: find the access URL or API, test a real download for one candidate district, note format, fields, coordinate availability, licence, update date, and any blockers.",
      "Count OSM schools, health facilities and roads per candidate district (Overpass) to compare coverage.",
      "Choose the pilot district; record the decision and reasons.",
    ],
    out: ["docs/source_audit.md: one row per source (status: usable / partial / blocked)", "Pilot district fixed in this document's title page", "Updated Section 5 tables"],
    done: ["Every Must source tested with a real sample", "Pilot district agreed by all members", "Sample files saved in data/samples/"] },
  { id: "S0.2", title: "Repository, Docker and CI setup", week: "1", dep: "None (parallel with S0.1)",
    goal: "One command starts the whole development stack.",
    tasks: [
      "Create the repository with the layout in Section 12.1.",
      "docker-compose.yml with services: db (PostGIS + pgRouting image), redis, backend (Django), worker (Celery), tiles (Martin), frontend (Vite dev server).",
      "Enable extensions: postgis, pgrouting, pg_trgm.",
      "Django skeleton with GeoDjango, DRF, health-check endpoint. React + Vite + MapLibre skeleton showing an OSM basemap.",
      "GitHub Actions: ruff, black --check, pytest, ESLint, frontend build.",
      ".env.example, README with setup steps.",
    ],
    out: ["Running stack", "CI pipeline green on main"],
    done: ["Fresh clone plus 'docker compose up' shows a map at localhost and /api/health returns OK", "CI runs on every pull request"] },
  { id: "S0.3", title: "Database schema and configuration files", week: "2", dep: "S0.2",
    goal: "All core tables and config files exist.",
    tasks: [
      "Create Django models and migrations for the data model in Section 9 (geo, sources, assets, analytics, accounts apps).",
      "Add GiST indexes on geometry, trigram index on village norm_name.",
      "Create config/*.yaml files with the starting values from Section 7, and a loader with validation (pydantic).",
      "Register models in Django admin for inspection.",
    ],
    out: ["Migrations", "Config files and loader with tests"],
    done: ["Migrations apply on an empty database", "Config loader rejects an invalid file with a clear error"] },

  { phase: "Phase 1: Administrative backbone (Weeks 2 to 3)" },
  { id: "S1.1", title: "LGD directory ingestion", week: "2", dep: "S0.3",
    goal: "Every state, district, block and village with official codes is in the database.",
    tasks: [
      "Connector to load LGD downloads (all-India or pilot state).",
      "Normalize names; store transliteration variants.",
      "Load LGD-to-Census 2011 code mapping.",
    ],
    out: ["Populated state, district, block and village tables"],
    done: ["Village count for pilot district matches LGD", "At least 95% of pilot villages have a Census code (or the shortfall is documented)"] },
  { id: "S1.2", title: "Village boundaries", week: "2 to 3", dep: "S1.1",
    goal: "Pilot villages have polygons.",
    tasks: [
      "Load boundary dataset for the pilot state; repair invalid geometry (make_valid).",
      "Join to villages by Census code; report the join rate.",
      "Load district boundary; mark pilot villages is_pilot = true.",
    ],
    out: ["Boundaries in village table", "Join-rate report"],
    done: ["Boundary join rate recorded (target 90% or more)", "Boundaries draw correctly on the map"] },
  { id: "S1.3", title: "Village search and resolver", week: "3", dep: "S1.2",
    goal: "Users can find any village and the system knows its analysis area.",
    tasks: [
      "Implement search: pg_trgm candidates, rapidfuzz re-rank, variant matching.",
      "Implement resolver returning LGD code, boundary, buffered analysis area.",
      "API: GET /villages/search and GET /villages/{lgd}.",
      "Front end: search bar with results list; selecting a result zooms to the boundary.",
    ],
    out: ["Search and resolver with tests", "Working search UI"],
    done: ["Test list of 30 village names with spelling variants: the correct village is in the top 3 for at least 27"] },

  { phase: "Phase 2: Source connectors (Weeks 3 to 5)" },
  { id: "S2.1", title: "Connector framework", week: "3", dep: "S0.3",
    goal: "A shared base so every connector behaves the same way.",
    tasks: [
      "BaseConnector with fetch(area), normalize(raw) and a run() that writes bronze then silver.",
      "Caching on disk keyed by query hash; rate limiting; retries with exponential back-off.",
      "Content hashing for idempotency; PipelineRun records with stats and errors.",
      "Management command: python manage.py ingest <source> --district <code>.",
    ],
    out: ["pipelines/connectors/base.py with tests"],
    done: ["A dummy connector run twice produces no duplicates", "A failing fetch is logged and does not crash the run"] },
  { id: "S2.2", title: "OpenStreetMap connector", week: "3 to 4", dep: "S2.1",
    goal: "All relevant OSM features for the pilot district are in silver.",
    tasks: [
      "Bulk mode: read Geofabrik extract with osmium/pyosmium or DuckDB; on-demand mode: Overpass query built from the categories.yaml tag list.",
      "Convert ways and relations (for example a school drawn as a polygon) to a representative point, keeping the polygon in attributes.",
      "Map tags to categories; extract name, name:hi, operator, and useful tags (isced:level, healthcare, surface).",
    ],
    out: ["OSM connector, fixture-based tests"],
    done: ["Counts per category for the pilot district match a manual Overpass check within 2%"] },
  { id: "S2.3", title: "Overture Maps connector", week: "4", dep: "S2.1",
    goal: "Overture places (and later buildings/roads) for any bounding box.",
    tasks: [
      "DuckDB query on the current Overture release, filtered by bounding box and category list.",
      "Map Overture categories to the taxonomy; keep the confidence value and its source list.",
      "Pin the Overture release version in sources.yaml.",
    ],
    out: ["Overture connector with tests"],
    done: ["Pilot district places loaded; release version recorded in each record"] },
  { id: "S2.4", title: "Schools connector (UDISE+ / School GIS)", week: "4", dep: "S2.1, S0.1 findings",
    goal: "Official school list with codes and attributes.",
    tasks: [
      "Implement the access method chosen in S0.1 (download, API or polite scraper).",
      "Map school category and management type; store the UDISE code as an official ID.",
      "Keep coordinates if published; otherwise leave geometry empty for the geocoder (S3.3).",
    ],
    out: ["Schools connector"],
    done: ["Pilot district school count is close to the official count published by the portal (difference explained)"] },
  { id: "S2.5", title: "Health facilities connector", week: "4 to 5", dep: "S2.1",
    goal: "Official health facility list with type and location.",
    tasks: [
      "Ingest NHFR and/or the National Hospital Directory per S0.1.",
      "Map facility type to subtypes (SC, PHC, CHC, district hospital, private clinic).",
    ],
    out: ["Health connector"],
    done: ["Facilities for the pilot district loaded with subtype; unknown types listed in run stats"] },
  { id: "S2.6", title: "Census amenities and Mission Antyodaya", week: "5", dep: "S1.1",
    goal: "Expected amenities per village.",
    tasks: [
      "Load Village Directory amenity columns and PCA population for the pilot state.",
      "Load Mission Antyodaya indicators if available.",
      "Translate indicators into expected_amenity rows per category.",
    ],
    out: ["expected_amenity table populated"],
    done: ["At least 90% of pilot villages have expected amenities"] },
  { id: "S2.7", title: "Buildings and population connectors", week: "5", dep: "S2.1",
    goal: "Building footprints and population grids for the pilot district.",
    tasks: [
      "Open Buildings (and Microsoft) footprints clipped to the district; filter by confidence.",
      "WorldPop or Meta population raster clipped to the district.",
      "Store footprints in a buildings table (not in silver assets).",
    ],
    out: ["Buildings table, population raster in data/"],
    done: ["Footprints display correctly over imagery for 3 sample villages"] },
  { id: "S2.8", title: "Roads connectors (OSM network, PMGSY, Microsoft roads)", week: "5", dep: "S2.2",
    goal: "Road data needed for routing and road-gap detection.",
    tasks: [
      "OSM drivable and walkable network via osmnx; save nodes and edges.",
      "PMGSY roads per S0.1 (as attributes to join onto OSM roads where they overlap).",
      "Microsoft road detections for the district.",
    ],
    out: ["Road datasets stored"],
    done: ["Road network loads into road_edge with valid source/target IDs"] },

  { phase: "Phase 3: Normalization (Weeks 5 to 6)" },
  { id: "S3.1", title: "Category mapping and village linking", week: "5", dep: "Phase 2",
    goal: "Every silver record has a category and a village code.",
    tasks: [
      "Category mapper driven by categories.yaml; unmapped values listed in run stats.",
      "Village linking by official code, else by point-in-polygon.",
      "Location precision assigned.",
    ],
    out: ["normalize/categories.py, village_link.py"],
    done: ["Less than 2% of silver records lack a category; unmapped tags reviewed"] },
  { id: "S3.2", title: "Name normalization", week: "6", dep: "S3.1",
    goal: "Clean, comparable names (Section 7.3).",
    tasks: [
      "Implement normalization, abbreviations dictionary, generic-token removal.",
      "Unit tests with at least 50 real name pairs from the pilot data.",
    ],
    out: ["normalize/names.py with tests"],
    done: ["All test pairs produce the expected key tokens"] },
  { id: "S3.3", title: "Geocoding fallback", week: "6", dep: "S3.2, S2.7",
    goal: "Records without coordinates get a best-available location.",
    tasks: [
      "Implement the three-stage process in Section 7.4.",
      "Temporary settlement centroid: largest building cluster per village (full settlements come in S6.1; a simple version is enough here).",
    ],
    out: ["normalize/geocode.py"],
    done: ["Every government record has a geometry and precision; share in each precision class reported"] },

  { phase: "Phase 4: Conflation (Weeks 6 to 8)" },
  { id: "S4.1", title: "Candidate generation", week: "6", dep: "Phase 3",
    goal: "All plausible same-asset pairs.",
    tasks: [
      "PostGIS ST_DWithin self-join per category across sources; plus pairs sharing official IDs.",
      "Store candidates with distance.",
    ],
    out: ["conflate/candidates.py"],
    done: ["Runs on the full pilot district in under 2 minutes"] },
  { id: "S4.2", title: "Pair scoring and clustering", week: "7", dep: "S4.1",
    goal: "Decide matches and form asset clusters (Section 7.5).",
    tasks: [
      "Scoring with weights from config.",
      "Union-find clustering with the same-source split guard.",
      "Uncertain pairs written to match_review.",
    ],
    out: ["conflate/scoring.py, cluster.py"],
    done: ["Unit tests cover: exact duplicate, nearby different schools, unnamed water tanks, chained matches"] },
  { id: "S4.3", title: "Labelling tool and match classifier", week: "7 to 8", dep: "S4.2",
    goal: "Ground-truth labels and a learned matcher.",
    tasks: [
      "Build the review/labelling page (Section 13.3).",
      "Label about 300 stratified pairs (split among the team).",
      "Train logistic regression or gradient boosting on features: distance, name scores, attribute agreement, source pair; 70/30 split.",
      "Compare with the rule-based threshold; keep the better one, switchable in config.",
    ],
    out: ["Labels in database and exported CSV", "Trained model file and evaluation notebook"],
    done: ["F1 for both methods reported on the held-out set"] },
  { id: "S4.4", title: "Merge, provenance and confidence", week: "8", dep: "S4.2",
    goal: "Gold asset table.",
    tasks: [
      "Geometry and attribute selection using field_priority.yaml; store attribute_provenance.",
      "Confidence calculation (Section 7.5).",
      "Rebuild gold for the district deterministically; asset_source_link populated.",
    ],
    out: ["conflate/merge.py, confidence.py", "Gold assets for pilot district"],
    done: ["Running the rebuild twice gives identical results", "Every gold asset links to at least one source record"] },

  { phase: "Phase 5: API and map interface (Weeks 8 to 9)" },
  { id: "S5.1", title: "Core REST API and vector tiles", week: "8", dep: "S4.4",
    goal: "The front end can read everything it needs.",
    tasks: [
      "Endpoints for villages, assets, asset detail, district summary (Section 10).",
      "Martin tile sources for assets, villages, settlements and roads.",
      "OpenAPI docs; pagination; filters.",
    ],
    out: ["API with tests and docs"],
    done: ["All listed endpoints pass API tests; tiles render in MapLibre"] },
  { id: "S5.2", title: "Map, layers and asset drawer", week: "8 to 9", dep: "S5.1",
    goal: "The main map experience.",
    tasks: [
      "Category layers with icons, clustering, legend, satellite toggle (display only).",
      "Styling rules from Section 11.1 (precision outline, confidence opacity).",
      "Asset drawer with provenance table.",
      "Filters: category, confidence, precision, source.",
    ],
    out: ["Map UI"],
    done: ["User stories US-1, US-2 and US-3 work end to end"] },
  { id: "S5.3", title: "Village page and district view", week: "9", dep: "S5.2",
    goal: "Summary views.",
    tasks: [
      "Village page layout with summary cards and tabs.",
      "District overview with placeholder choropleth (filled in Phase 7).",
      "Responsive layout check on a phone screen.",
    ],
    out: ["Village and district pages"],
    done: ["Pages load within NFR-1 limits on the pilot district"] },

  { phase: "Phase 6: Gap-filling and data quality (Weeks 9 to 10)" },
  { id: "S6.1", title: "Settlements and population", week: "9", dep: "S2.7",
    goal: "Hamlets with population estimates (Section 7.6).",
    tasks: ["DBSCAN clustering, concave hulls, population allocation, snapping to road nodes.", "Settlement layer on map."],
    out: ["gapfill/settlements.py", "settlement table"],
    done: ["Visual check on 10 villages: clusters match visible hamlets on imagery", "Sum of settlement populations equals the village total"] },
  { id: "S6.2", title: "Expected-versus-found flags", week: "9", dep: "S2.6, S4.4",
    goal: "Missing, unlisted and count-mismatch flags (Section 7.7).",
    tasks: ["Comparison logic, gap_flag rows with evidence.", "Gaps tab on village page; data quality page."],
    out: ["gapfill/expected.py"],
    done: ["User story US-7 works; each flag shows its evidence"] },
  { id: "S6.3", title: "Unmapped road detection", week: "10", dep: "S2.8",
    goal: "Likely unmapped roads (Section 7.8).",
    tasks: ["Buffer comparison logic; flagged roads layer; optional MapRoulette export."],
    out: ["gapfill/roads.py"],
    done: ["Flagged roads displayed; sample of 30 visually checked and precision noted"] },
  { id: "S6.4", title: "Quality checks and completeness score", week: "10", dep: "S4.4",
    goal: "Quality flags and per-village completeness (Sections 7.13, FR-5.5).",
    tasks: [
      "Checks: outside village, in water body, duplicate coordinates across many records, impossible values, stale data.",
      "Completeness formula; store on village.",
    ],
    out: ["gapfill/quality.py, analytics/completeness.py"],
    done: ["Completeness visible on village page and as a district choropleth"] },
  { id: "S6.5", title: "Water body analysis (optional)", week: "10 or later", dep: "S0.1 Earth Engine access",
    goal: "Permanent / seasonal / drying labels (Section 7.9).",
    tasks: ["JRC-based permanence and trend; optional Sentinel-2 NDWI check.", "Water layer with labels."],
    out: ["gapfill/water.py"],
    done: ["Labels computed for pilot district ponds; 10 spot-checked against imagery history"] },

  { phase: "Phase 7: Analytics (Weeks 10 to 12)" },
  { id: "S7.1", title: "Routing graph", week: "10", dep: "S2.8",
    goal: "Routable network in pgRouting.",
    tasks: ["Load edges with walk and drive costs from speeds.yaml.", "Snap assets and settlements to nearest nodes.", "Check connectivity; report disconnected parts."],
    out: ["analytics/network.py"],
    done: ["Shortest path between two known places matches a manual check within 10%"] },
  { id: "S7.2", title: "Access computation and isochrones", week: "11", dep: "S7.1, S6.1",
    goal: "Nearest-facility table and isochrone tool (Section 7.10).",
    tasks: ["Multi-source driving distance per category and mode; settlement_access table.", "Isochrone endpoint and UI tool.", "Access tab on village page."],
    out: ["analytics/access.py, isochrone.py", "Isochrone UI"],
    done: ["User story US-5 works; district access computed in under 5 minutes"] },
  { id: "S7.3", title: "Norms and gap score", week: "11", dep: "S7.2",
    goal: "Village gap score and choropleth (Section 7.11).",
    tasks: ["Verify norms against official documents and cite them.", "Implement scoring; store on village.", "District choropleth switcher."],
    out: ["analytics/norms.py"],
    done: ["User story US-4 works; norm values cited in docs"] },
  { id: "S7.4", title: "Facility location optimizer", week: "12", dep: "S7.2",
    goal: "Recommend new facility sites (Section 7.12).",
    tasks: ["Build coverage sets from network distances.", "PuLP model; random and greedy baselines.", "Optimizer UI with before-after coverage."],
    out: ["analytics/optimize.py", "Optimizer page"],
    done: ["User story US-6 works; optimizer beats both baselines on the pilot district"] },
  { id: "S7.5", title: "What-if scenarios and risk overlay", week: "12", dep: "S7.2",
    goal: "Interactive scenario analysis.",
    tasks: ["Add facility / block road, recompute for affected area.", "Optional flood-risk overlay from DEM and surface water."],
    out: ["What-if endpoint and UI"],
    done: ["Blocking a bridge shows which settlements lose access within 10 seconds"] },

  { phase: "Phase 8: Delivery (Weeks 12 to 14)" },
  { id: "S8.1", title: "On-demand pipeline", week: "12", dep: "Phases 1 to 7",
    goal: "Any village can be processed live (Section 7.14).",
    tasks: ["Celery flow for a single village area.", "Run status endpoint and progress UI.", "Caching so repeated requests are instant."],
    out: ["flows/on_demand_village.py", "Progress UI"],
    done: ["User story US-10 works; median core run under 90 s across 10 test villages in other districts"] },
  { id: "S8.2", title: "Exports and village PDF", week: "13", dep: "S5.3",
    goal: "Downloadable data and reports.",
    tasks: ["GeoJSON, KML, zipped Shapefile, CSV exports with an attribution file.", "PDF template: map, asset table, gaps, access, sources."],
    out: ["Export endpoint, PDF report"],
    done: ["User stories US-8 and US-9 work; exports open correctly in QGIS"] },
  { id: "S8.3", title: "Accounts, review queue, corrections and scheduling", week: "13", dep: "S4.3",
    goal: "Admin features and data upkeep.",
    tasks: ["JWT auth and roles.", "Review queue polish; citizen correction flags.", "Celery Beat refresh schedule; audit log."],
    out: ["Admin and review features"],
    done: ["User stories US-11 and US-12 work; protected endpoints reject anonymous users"] },
  { id: "S8.4", title: "Evaluation", week: "13", dep: "S4.3, S6.x, S7.x",
    goal: "All metrics in Section 13.2.",
    tasks: ["Run each evaluation; produce tables and charts.", "Performance tests."],
    out: ["docs/evaluation.md with results, charts, notebooks"],
    done: ["Every metric in Section 13.2 has a value"] },
  { id: "S8.5", title: "Deployment, documentation and demo", week: "14", dep: "All",
    goal: "Finished, presentable project.",
    tasks: ["Optional deployment to a small cloud server.", "README, user guide, API docs.", "Final report chapters; demo script rehearsal (Section 17).", "Tag release v1.0."],
    out: ["Final report, slides, recorded demo video as backup"],
    done: ["A teammate who did not build a feature can run the demo from the README alone"] },
];

C.push(
  H1("15. Implementation Plan"),
  P("The work is divided into 9 phases and 39 steps. Each step is small enough to finish in a few days and has clear acceptance criteria. Steps are done in order unless marked as parallel; a step starts only when its dependencies are Done."),
  H2("15.1 MVP cut line"),
  NOTE("**MVP (must be finished):** Phases 0 to 5, plus S6.1, S6.2, S6.4, S7.1, S7.2, S7.3, S8.2 and S8.4. Everything else (S4.3 classifier, S6.3, S6.5, S7.4, S7.5, S8.1, S8.3) is valuable but is dropped first if the schedule slips. The MVP alone delivers a complete, defensible project."),
  H2("15.2 Phase summary"),
  T(["Phase", "Name", "Weeks", "Outcome"], [
    ["0", "Foundations", "1 to 2", "Sources confirmed, stack running, schema ready"],
    ["1", "Administrative backbone", "2 to 3", "Villages, codes, boundaries, search"],
    ["2", "Source connectors", "3 to 5", "All sources ingested to bronze and silver"],
    ["3", "Normalization", "5 to 6", "Clean, linked, located records"],
    ["4", "Conflation", "6 to 8", "Gold assets with provenance and confidence"],
    ["5", "API and map", "8 to 9", "Usable map application"],
    ["6", "Gap-filling and quality", "9 to 10", "Settlements, gaps, completeness"],
    ["7", "Analytics", "10 to 12", "Access, norms, optimizer, what-if"],
    ["8", "Delivery", "12 to 14", "On-demand, reports, admin, evaluation, final demo"],
  ], [900, 2600, 1300, 4226]),
);
for (const s of steps) {
  if (s.phase) C.push(H2(s.phase));
  else C.push(...STEP(s));
}

// 16. Tracker
C.push(
  H1("16. Progress Tracker"),
  P("Update this table at the end of every step. Status values: Not started, In progress, Blocked, Done, Dropped."),
  T(["Step", "Title", "Week", "Owner", "Status", "Done on / notes"],
    steps.filter((s) => s.id).map((s) => [s.id, s.title, s.week, "", (PROGRESS[s.id] || ["Not started", ""])[0], (PROGRESS[s.id] || ["", ""])[1]]),
    [700, 3600, 900, 1100, 1300, 1426]),
  H2("16.1 Suggested ownership"),
  T(["Member", "Area", "Main steps"], [
    ["A", "Connectors and pipelines", "S0.1, S1.1, S2.1 to S2.8, S8.1"],
    ["B", "Normalization, conflation, database", "S0.3, S1.2, S3.x, S4.x, S6.2, S6.4"],
    ["C", "Frontend and API", "S0.2, S1.3 (UI), S5.x, S8.2, S8.3"],
    ["D", "Spatial analytics and evaluation", "S6.1, S6.3, S6.5, S7.x, S8.4"],
  ], [1200, 3300, 4526]),
);

// 17. Demo
C.push(
  H1("17. Final Demo Script (about 8 minutes)"),
  ...BL([
    "**Problem (30 s):** asset data is scattered; show three sources disagreeing about one village.",
    "**District view (1 min):** gap-score choropleth; switch to completeness and health access.",
    "**Village drill-down (1.5 min):** assets coloured by category; open one school and show provenance from three sources and its confidence.",
    "**Gaps (1 min):** 'The Census lists a PHC here but no source locates it'; unmapped roads layer.",
    "**Access (1 min):** isochrones from the nearest PHC; list of hamlets beyond 5 km.",
    "**Optimizer and what-if (1.5 min):** best site for one new PHC with coverage gain; block a bridge and show lost access.",
    "**On demand (1 min):** a village named by the audience is mapped live.",
    "**Output and results (30 s):** download the PDF; show the evaluation chart of coverage added by each source.",
  ]),
);

// 18. Licensing
C.push(
  H1("18. Licensing and Attribution"),
  T(["Data", "Obligation"], [
    ["OpenStreetMap (ODbL)", "Credit '© OpenStreetMap contributors' on map and exports. A database derived from OSM and shared publicly must also be under ODbL."],
    ["Overture Maps", "Follow the licence of each theme (some ODbL, some CDLA-Permissive); credit Overture."],
    ["Google Open Buildings / Microsoft footprints and roads", "Credit the provider; follow CC BY 4.0 / ODbL terms."],
    ["WorldPop, Meta, ESA WorldCover, JRC, Copernicus", "Credit as required by each (mostly CC BY 4.0 or attribution)."],
    ["Indian government open data", "Follow GODL-India where it applies (attribution); for portals with their own terms, respect them and avoid heavy scraping."],
    ["Satellite basemaps (Esri, Google, Bing)", "Display only, if used at all. Never extract data from them or train models on them."],
  ], [3000, 6026]),
  P("The About page and every export include a generated attribution file listing all sources used for that output."),
);

// 19. Glossary & change log
C.push(
  H1("19. Glossary and Change Log"),
  H2("19.1 Glossary"),
  T(["Term", "Meaning"], [
    ["Asset", "A physical community facility: school, health centre, water source, road, etc."],
    ["Bronze / Silver / Gold", "Raw, normalized and merged data layers"],
    ["Conflation", "Merging records from different sources that describe the same real object"],
    ["Confidence", "0 to 1 score of how likely an asset is real and correctly placed"],
    ["Location precision", "Exact (source coordinates), matched (borrowed from a named match), approximate (settlement centroid)"],
    ["Settlement / hamlet", "A cluster of buildings within a village"],
    ["Isochrone", "Area reachable within a given travel time"],
    ["MCLP", "Maximal Coverage Location Problem: choose p sites covering the most demand"],
    ["LGD", "Local Government Directory: official codes for administrative units"],
    ["PHC / CHC / SC", "Primary Health Centre / Community Health Centre / Sub-Centre"],
    ["UDISE+", "Unified District Information System for Education Plus (school data)"],
    ["PMGSY", "Pradhan Mantri Gram Sadak Yojana (rural roads programme)"],
    ["GODL", "Government Open Data License - India"],
    ["ODbL", "Open Database License, used by OpenStreetMap"],
    ["DBSCAN", "Density-based clustering algorithm used to find settlements"],
    ["NDWI", "Normalized Difference Water Index, from satellite imagery"],
  ], [2400, 6626]),
  H2("19.2 Change log"),
  T(["Version", "Date", "Change", "By"], [
    ["1.0", "14 Oct 2026", "Initial baseline", "Team"],
    ["1.1", "14 Oct 2026", "S0.1 source audit: KGIS added as a Must source; PMGSY via DataMeet mirror; NHFR, Mission Antyodaya, Census site marked blocked; LGD optional; pilot district fixed as Bengaluru North; two risks updated", "Team"],
    ["1.2", "14 Oct 2026", "S0.2 and S0.3 done. Data model: village.gp_lgd_code added (KGIS provides GP codes); water_body.geom is MULTIPOLYGON; bronze_record unique on (source, content_hash). Repository layout: config/pipeline.yaml added for the numeric thresholds of Section 7. See docs/decisions.md", "Team"],
    ["", "", "", ""],
  ], [1100, 1600, 4926, 1400]),
);

// ---------- document ----------
const doc = new Document({
  creator: "GramMap Team",
  title: "GramMap PRD",
  styles: {
    default: { document: { run: { font: "Calibri", size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 34, bold: true, color: ACCENT }, paragraph: { spacing: { before: 240, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 27, bold: true, color: "2E2E2E" }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, color: ACCENT }, paragraph: { spacing: { before: 240, after: 100 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [{
      reference: "bullets",
      levels: [
        { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1080, hanging: 270 } } } },
      ],
    }],
  },
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "GramMap PRD v1.1", size: 16, color: "808080" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: ["Page ", PageNumber.CURRENT, " of ", PageNumber.TOTAL_PAGES], size: 16, color: "808080" })] })] }) },
    children: C,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(process.argv[2], buf);
  console.log("written", process.argv[2], buf.length);
});
