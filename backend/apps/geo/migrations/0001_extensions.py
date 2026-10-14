from django.contrib.postgres.operations import CreateExtension, TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    """Database extensions every later migration relies on (PostGIS itself is created by GeoDjango)."""

    operations = [
        CreateExtension("postgis"),
        CreateExtension("pgrouting"),
        TrigramExtension(),
    ]
