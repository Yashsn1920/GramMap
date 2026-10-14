import pytest
from django.apps import apps
from django.contrib.gis.db.models import GeometryField
from django.core.management import call_command
from django.db import connection

GRAMMAP_APPS = ["accounts", "geo", "sources", "assets", "analytics"]


@pytest.mark.django_db
def test_no_missing_migrations():
    call_command("makemigrations", "--check", "--dry-run", verbosity=0)


@pytest.mark.django_db
def test_every_geometry_column_has_gist_index():
    with connection.cursor() as cur:
        cur.execute("SELECT tablename, indexdef FROM pg_indexes WHERE schemaname = 'public'")
        indexes = cur.fetchall()
    missing = []
    for label in GRAMMAP_APPS:
        for model in apps.get_app_config(label).get_models():
            table = model._meta.db_table
            for field in model._meta.get_fields():
                if isinstance(field, GeometryField):
                    if not any(
                        t == table and "USING gist" in d and f"({field.column})" in d
                        for t, d in indexes
                    ):
                        missing.append(f"{table}.{field.column}")
    assert not missing


@pytest.mark.django_db
def test_village_name_trigram_index():
    with connection.cursor() as cur:
        cur.execute("SELECT indexdef FROM pg_indexes WHERE indexname = 'village_norm_name_trgm'")
        (indexdef,) = cur.fetchone()
    assert "gin" in indexdef and "gin_trgm_ops" in indexdef


@pytest.mark.django_db
def test_village_round_trip():
    from django.contrib.gis.geos import MultiPolygon, Polygon

    from apps.geo.models import Block, District, State, Village

    state = State.objects.create(code="29", name="Karnataka")
    district = District.objects.create(code="583", state=state, name="Bengaluru North")
    block = Block.objects.create(code="5541", district=district, name="Doddaballapura")
    square = Polygon(((77.5, 13.3), (77.51, 13.3), (77.51, 13.31), (77.5, 13.31), (77.5, 13.3)))
    Village.objects.create(
        lgd_code="613541",
        block=block,
        name="Kodigehalli",
        norm_name="kodigehalli",
        name_variants=["kodigehalli", "kodigehally"],
        boundary=MultiPolygon(square, srid=4326),
    )
    v = Village.objects.get(boundary__intersects=square.centroid)
    assert v.name_variants == ["kodigehalli", "kodigehally"]
