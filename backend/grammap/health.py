from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response

REQUIRED_EXTENSIONS = ("postgis", "pgrouting", "pg_trgm")


@api_view(["GET"])
def health(request):
    """Report OK when the database is reachable and the required extensions are installed."""
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT extname, extversion FROM pg_extension")
            extensions = dict(cur.fetchall())
    except Exception as exc:  # database down or misconfigured
        return Response({"status": "error", "database": str(exc)}, status=503)

    missing = [e for e in REQUIRED_EXTENSIONS if e not in extensions]
    body = {
        "status": "error" if missing else "ok",
        "database": "ok",
        "extensions": {e: extensions.get(e) for e in REQUIRED_EXTENSIONS},
    }
    return Response(body, status=503 if missing else 200)
