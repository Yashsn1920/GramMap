import shutil

import pytest
import yaml

from pipelines.config import DEFAULT_DIR, ConfigError, load_config, load_file


@pytest.fixture
def cfg_dir(tmp_path):
    """A writable copy of the real config directory."""
    d = tmp_path / "config"
    shutil.copytree(DEFAULT_DIR, d)
    return d


def edit(d, name, change):
    path = d / f"{name}.yaml"
    data = yaml.safe_load(path.read_text())
    change(data)
    path.write_text(yaml.safe_dump(data))


def test_real_config_loads():
    cfg = load_config()
    assert set(cfg.categories) >= {"SCH", "HLT", "WTR", "WEL", "ROD", "AWC"}
    assert cfg.categories["SCH"].match.meters == 150
    assert cfg.categories["PND"].match.method == "overlap"
    assert cfg.pipeline.conflation.match_threshold == 0.75
    assert sum(n.weight for n in cfg.norms) == 100
    assert cfg.speeds.walk.default == 4.5
    assert cfg.sources["osm"].weight == 0.70
    assert "nhfr" not in cfg.enabled_sources()


def test_hash_is_stable_and_tracks_changes(cfg_dir):
    assert load_config(cfg_dir).hash == load_config().hash
    edit(cfg_dir, "speeds", lambda d: d["walk"].update(default=5.0))
    assert load_config(cfg_dir).hash != load_config().hash


def test_bad_value_names_file_and_field(cfg_dir):
    edit(cfg_dir, "categories", lambda d: d["categories"]["SCH"]["match"].update(meters=-5))
    with pytest.raises(ConfigError) as exc:
        load_config(cfg_dir)
    msg = str(exc.value)
    assert "categories.yaml" in msg
    assert "categories.SCH.match.meters" in msg


def test_unknown_key_rejected(cfg_dir):
    edit(cfg_dir, "speeds", lambda d: d["walk"].update(defualt=4))
    with pytest.raises(ConfigError, match=r"walk\.defualt: Extra inputs are not permitted"):
        load_file("speeds", cfg_dir)


def test_missing_meters_for_distance_match(cfg_dir):
    edit(cfg_dir, "categories", lambda d: d["categories"]["WEL"]["match"].pop("meters"))
    with pytest.raises(ConfigError, match="'meters' is required"):
        load_file("categories", cfg_dir)


def test_weights_must_sum_to_one(cfg_dir):
    edit(
        cfg_dir,
        "pipeline",
        lambda d: d["conflation"]["weights_named"].update(name=0.9),
    )
    with pytest.raises(ConfigError, match="weights_named must sum to 1"):
        load_file("pipeline", cfg_dir)


def test_thresholds_ordered(cfg_dir):
    edit(cfg_dir, "pipeline", lambda d: d["conflation"].update(uncertain_threshold=0.8))
    with pytest.raises(ConfigError, match="uncertain_threshold must be below"):
        load_file("pipeline", cfg_dir)


def test_unknown_norm_rule_type(cfg_dir):
    edit(cfg_dir, "norms", lambda d: d["norms"][0]["rule"].update(type="nearby"))
    with pytest.raises(ConfigError, match=r"norms\.0\.rule"):
        load_file("norms", cfg_dir)


def test_cross_file_references(cfg_dir):
    edit(cfg_dir, "field_priority", lambda d: d["fields"]["name"].insert(0, "osmm"))
    edit(cfg_dir, "norms", lambda d: d["norms"][0].update(category="XYZ"))
    with pytest.raises(ConfigError) as exc:
        load_config(cfg_dir)
    msg = str(exc.value)
    assert "unknown source 'osmm'" in msg
    assert "unknown category 'XYZ'" in msg


def test_invalid_yaml(cfg_dir):
    (cfg_dir / "speeds.yaml").write_text("walk: [unclosed\n")
    with pytest.raises(ConfigError, match="speeds.yaml: invalid YAML"):
        load_file("speeds", cfg_dir)


def test_missing_file(cfg_dir):
    (cfg_dir / "norms.yaml").unlink()
    with pytest.raises(ConfigError, match="norms.yaml: file not found"):
        load_config(cfg_dir)
