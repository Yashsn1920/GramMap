"""Load and validate config/*.yaml (PRD Section 12.2: configuration over code).

    from pipelines.config import load_config
    cfg = load_config()                 # every file, cross-checked
    cfg.categories["SCH"].match.meters  # 150

Any problem raises ConfigError naming the file and the field path.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

DEFAULT_DIR = Path(__file__).resolve().parent.parent / "config"

Fraction = Annotated[float, Field(ge=0, le=1)]
Positive = Annotated[float, Field(gt=0)]


class ConfigError(ValueError):
    pass


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# ---------- categories.yaml ----------


class MatchRule(Strict):
    method: Literal["distance", "overlap", "buffer"]
    meters: Positive | None = None

    @model_validator(mode="after")
    def meters_needed(self):
        if self.method in ("distance", "buffer") and self.meters is None:
            raise ValueError(f"'meters' is required for method '{self.method}'")
        return self


class Category(Strict):
    label: str
    geometry: Literal["point", "line", "polygon"]
    match: MatchRule
    subtypes: list[str] = []
    sources: dict[str, list[str]] = {}


class CategoriesFile(Strict):
    categories: dict[Annotated[str, Field(pattern=r"^[A-Z]{3}$")], Category]


# ---------- sources.yaml ----------


class Source(Strict):
    label: str
    kind: Literal["government", "osm", "overture", "ml", "other"]
    access: Literal["overpass", "duckdb", "arcgis_rest", "download", "api"]
    url: str
    mirrors: list[str] = []
    page_size: Annotated[int, Field(gt=0)] | None = None
    rate_limit: Positive | None = None
    weight: Fraction
    geocoded_weight: Fraction | None = None
    licence: str
    attribution: str
    enabled: bool = True


class SourcesFile(Strict):
    sources: dict[str, Source]


# ---------- field_priority.yaml ----------


class GeometryPriority(Strict):
    kind_order: list[Literal["government", "osm", "overture", "ml", "other"]]
    precision_order: list[Literal["exact", "matched", "approximate"]]


class FieldPriorityFile(Strict):
    geometry: GeometryPriority
    fields: dict[str, list[str]]


# ---------- abbreviations.yaml ----------


class AbbreviationsFile(Strict):
    abbreviations: dict[str, str]
    spelling_variants: dict[str, str] = {}
    generic_tokens: list[str] = []

    @model_validator(mode="after")
    def lower_case(self):
        for name in ("abbreviations", "spelling_variants"):
            bad = [k for k in getattr(self, name) if k != k.lower()]
            if bad:
                raise ValueError(f"{name} keys must be lower-case: {bad}")
        return self


# ---------- norms.yaml ----------


class AccessRule(Strict):
    type: Literal["access"]
    max_km: Positive


class PerPopulation(Strict):
    plains: Annotated[int, Field(gt=0)]
    hilly: Annotated[int, Field(gt=0)]


class PopulationRule(Strict):
    type: Literal["population"]
    per: PerPopulation
    max_km: Positive | None = None


class PresenceRule(Strict):
    type: Literal["presence"]
    per: Literal["settlement", "village"]


class PavedRoadRule(Strict):
    type: Literal["paved_road"]


class Norm(Strict):
    id: str
    label: str
    category: str
    also_categories: list[str] = []
    subtype: str | None = None
    rule: Annotated[
        AccessRule | PopulationRule | PresenceRule | PavedRoadRule, Field(discriminator="type")
    ]
    weight: Positive


class NormsFile(Strict):
    norms: list[Norm]

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [n.id for n in self.norms]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"duplicate norm ids: {dupes}")
        return self


# ---------- speeds.yaml ----------


class WalkSpeeds(Strict):
    default: Positive


class DriveSpeeds(Strict):
    default: Positive
    highway: dict[str, Positive] = {}


class SpeedsFile(Strict):
    walk: WalkSpeeds
    drive: DriveSpeeds


# ---------- pipeline.yaml ----------


class Resolver(Strict):
    analysis_buffer_km: Positive
    no_boundary_search_km: Positive
    no_boundary_hull_buffer_m: Positive
    search_candidates: Annotated[int, Field(gt=0)]


class Geocoding(Strict):
    name_match_min: Annotated[float, Field(ge=0, le=100)]


def _check_sum(weights: dict[str, float], what: str):
    total = sum(weights.values())
    if abs(total - 1) > 1e-6:
        raise ValueError(f"{what} must sum to 1, got {total:g}")


class Conflation(Strict):
    weights_named: dict[Literal["distance", "name", "attribute"], Fraction]
    weights_unnamed: dict[Literal["distance", "attribute"], Fraction]
    attribute_scores: dict[Literal["agree", "unknown", "conflict"], Fraction]
    match_threshold: Fraction
    uncertain_threshold: Fraction

    @model_validator(mode="after")
    def consistent(self):
        _check_sum(self.weights_named, "weights_named")
        _check_sum(self.weights_unnamed, "weights_unnamed")
        if self.uncertain_threshold >= self.match_threshold:
            raise ValueError("uncertain_threshold must be below match_threshold")
        return self


class RecencyBand(Strict):
    max_years: Positive | None
    factor: Fraction


class Display(Strict):
    high: Fraction
    medium: Fraction


class Confidence(Strict):
    recency: list[RecencyBand]
    precision: dict[Literal["exact", "matched", "approximate"], Fraction]
    display: Display

    @model_validator(mode="after")
    def consistent(self):
        if not self.recency or self.recency[-1].max_years is not None:
            raise ValueError("the last recency band must have max_years: null")
        if self.display.medium >= self.display.high:
            raise ValueError("display.medium must be below display.high")
        return self


class Settlements(Strict):
    min_building_confidence: Fraction
    dbscan_eps_m: Positive
    dbscan_min_samples: Annotated[int, Field(gt=0)]


class RoadGaps(Strict):
    osm_buffer_m: Positive
    min_outside_share: Fraction
    min_outside_length_m: Positive


class Water(Strict):
    jrc_min_occurrence: Annotated[float, Field(ge=0, le=100)]


class Completeness(Strict):
    weights: dict[
        Literal["categories_found", "precise_share", "sources_per_asset", "recently_confirmed"],
        Fraction,
    ]
    sources_per_asset_target: Positive
    recent_years: Positive

    @model_validator(mode="after")
    def consistent(self):
        _check_sum(self.weights, "completeness.weights")
        return self


class OnDemand(Strict):
    poll_interval_s: Positive
    target_seconds: Positive


class PipelineFile(Strict):
    resolver: Resolver
    geocoding: Geocoding
    conflation: Conflation
    confidence: Confidence
    settlements: Settlements
    road_gaps: RoadGaps
    water: Water
    completeness: Completeness
    on_demand: OnDemand


# ---------- loading ----------

FILES: dict[str, type[Strict]] = {
    "categories": CategoriesFile,
    "sources": SourcesFile,
    "field_priority": FieldPriorityFile,
    "abbreviations": AbbreviationsFile,
    "norms": NormsFile,
    "speeds": SpeedsFile,
    "pipeline": PipelineFile,
}


class Config(Strict):
    categories: dict[str, Category]
    sources: dict[str, Source]
    field_priority: FieldPriorityFile
    abbreviations: AbbreviationsFile
    norms: list[Norm]
    speeds: SpeedsFile
    pipeline: PipelineFile
    hash: str

    def enabled_sources(self) -> dict[str, Source]:
        return {k: s for k, s in self.sources.items() if s.enabled}


def config_dir() -> Path:
    return Path(os.environ.get("GRAMMAP_CONFIG_DIR", DEFAULT_DIR))


def _format(err: ValidationError) -> str:
    lines = []
    for e in err.errors():
        where = ".".join(str(p) for p in e["loc"]) or "(top level)"
        lines.append(f"  {where}: {e['msg']}")
    return "\n".join(lines)


def load_file(name: str, directory: Path | None = None) -> Strict:
    """Load and validate one config file, e.g. load_file('norms')."""
    if name not in FILES:
        raise ConfigError(f"unknown config file '{name}'; expected one of {sorted(FILES)}")
    path = (directory or config_dir()) / f"{name}.yaml"
    try:
        raw = yaml.safe_load(path.read_text())
    except FileNotFoundError:
        raise ConfigError(f"{path}: file not found") from None
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path}: invalid YAML\n  {exc}") from None
    try:
        return FILES[name].model_validate(raw if raw is not None else {})
    except ValidationError as exc:
        raise ConfigError(f"{path}: {exc.error_count()} problem(s)\n{_format(exc)}") from None


def _cross_check(parts: dict, directory: Path):
    sources = set(parts["sources"].sources)
    categories = parts["categories"].categories
    problems = []
    for code, cat in categories.items():
        for src in cat.sources:
            if src not in sources:
                problems.append(f"categories.yaml: {code}.sources: unknown source '{src}'")
    for field, order in parts["field_priority"].fields.items():
        for src in order:
            if src != "*" and src not in sources:
                problems.append(f"field_priority.yaml: fields.{field}: unknown source '{src}'")
    for norm in parts["norms"].norms:
        for code in [norm.category, *norm.also_categories]:
            if code not in categories:
                problems.append(f"norms.yaml: {norm.id}.category: unknown category '{code}'")
        cat = categories.get(norm.category)
        if norm.subtype and cat and norm.subtype not in cat.subtypes:
            problems.append(
                f"norms.yaml: {norm.id}.subtype: '{norm.subtype}' is not a subtype of "
                f"{norm.category}"
            )
    if problems:
        raise ConfigError(f"{directory}: inconsistent config files\n  " + "\n  ".join(problems))


def load_config(directory: Path | str | None = None) -> Config:
    """Load every config file, cross-check references between them and return one object."""
    directory = Path(directory) if directory else config_dir()
    parts = {name: load_file(name, directory) for name in FILES}
    _cross_check(parts, directory)
    data = {
        "categories": parts["categories"].categories,
        "sources": parts["sources"].sources,
        "field_priority": parts["field_priority"],
        "abbreviations": parts["abbreviations"],
        "norms": parts["norms"].norms,
        "speeds": parts["speeds"],
        "pipeline": parts["pipeline"],
    }
    cfg = Config(**data, hash="")
    canonical = json.dumps(cfg.model_dump(exclude={"hash"}), sort_keys=True)
    return cfg.model_copy(update={"hash": hashlib.sha256(canonical.encode()).hexdigest()})
