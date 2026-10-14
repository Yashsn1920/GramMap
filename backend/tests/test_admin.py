import pytest
from django.contrib import admin
from django.urls import reverse

GRAMMAP_APPS = {"accounts", "geo", "sources", "assets", "analytics"}


@pytest.mark.django_db
def test_every_model_registered_and_pages_load(admin_client):
    from django.apps import apps

    for label in GRAMMAP_APPS:
        for model in apps.get_app_config(label).get_models():
            if model._meta.auto_created:
                continue
            assert admin.site.is_registered(model), model
            opts = model._meta
            for view in ("changelist", "add"):
                url = reverse(f"admin:{opts.app_label}_{opts.model_name}_{view}")
                assert admin_client.get(url).status_code == 200, url
