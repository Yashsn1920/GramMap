import ast
import pathlib

PIPELINES = pathlib.Path(__file__).resolve().parent.parent


def test_no_django_imports():
    """Pipelines must stay pure; database access belongs in flows via the backend."""
    for path in PIPELINES.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            assert not any(n.split(".")[0] == "django" for n in names), path
