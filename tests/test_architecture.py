"""Guards for layered architecture: presentation → service → repository → data."""

import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "app"
API_ROOT = APP_ROOT / "api"
MIDDLEWARE_ROOT = APP_ROOT / "middleware"
REPOS_ROOT = APP_ROOT / "repositories"


def _python_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return [path for path in directory.rglob("*.py") if path.name != "__init__.py"]


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
    return modules


class TestLayeredArchitecture:
    def test_api_routes_do_not_import_repositories(self):
        violations = []
        for path in _python_files(API_ROOT):
            for module in _imported_modules(path):
                if module.startswith("app.repositories"):
                    violations.append(f"{path.relative_to(APP_ROOT.parent)} imports {module}")
        assert not violations, "API routes must call services, not repositories:\n" + "\n".join(violations)

    def test_middleware_does_not_import_repositories(self):
        violations = []
        for path in _python_files(MIDDLEWARE_ROOT):
            for module in _imported_modules(path):
                if module.startswith("app.repositories"):
                    violations.append(f"{path.relative_to(APP_ROOT.parent)} imports {module}")
        assert not violations, "Middleware must call services, not repositories:\n" + "\n".join(violations)

    def test_repositories_do_not_raise_http_exceptions(self):
        violations = []
        for path in _python_files(REPOS_ROOT):
            source = path.read_text(encoding="utf-8")
            imported_http = any(
                module == "fastapi" or module.startswith("fastapi.") for module in _imported_modules(path)
            )
            mentions_http_exception = "HTTPException" in source
            if imported_http or mentions_http_exception:
                violations.append(str(path.relative_to(APP_ROOT.parent)))
        assert not violations, "Repositories must not raise HTTPException:\n" + "\n".join(violations)
