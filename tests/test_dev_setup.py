import json
import os
import pty
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from secrets import token_urlsafe
from unittest.mock import Mock

import pytest

from backend.api.app import main
from backend.api.app.schemas import Page
from backend.api.scripts.export_openapi import build_document

ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = {
    "/api/v0/amendements",
    "/api/v0/dossiers",
    "/api/v0/textes",
    "/api/v0/articles",
    "/api/v0/parlementaires",
    "/api/v0/groupes_politiques",
    "/api/v0/declarations_hatvp",
}


def test_docker_build_excludes_local_credentials():
    patterns = set((ROOT / ".dockerignore").read_text().splitlines())
    assert {".env", ".env.*", ".git/", ".venv/", "build/"}.issubset(patterns)


def test_microcks_examples_do_not_access_database_or_export_secrets(monkeypatch):
    password = token_urlsafe(32)
    monkeypatch.setenv("API_PASSWORD", password)
    monkeypatch.setenv("DATABASE_URL", "postgresql://example.invalid/test")
    engine = Mock(side_effect=AssertionError("Aucun accès DB autorisé"))
    monkeypatch.setattr(main, "create_async_engine", engine)
    document = build_document()
    assert document["openapi"].startswith("3.1.")
    assert password not in json.dumps(document)
    assert "example.invalid" not in json.dumps(document)
    engine.assert_not_called()
    examples = {}
    for path, methods in document["paths"].items():
        operation = methods["get"]
        content = (
            operation.get("responses", {})
            .get("200", {})
            .get("content", {})
            .get("application/json", {})
        )
        if "examples" in content:
            examples[path] = content["examples"]["default"]["value"]
        if path in COLLECTIONS:
            assert operation["security"] == [{"HTTPBearer": []}]
            for parameter in operation["parameters"]:
                if parameter["name"] in ("limit", "offset"):
                    assert (
                        parameter["examples"]["default"]["value"]
                        == examples[path][parameter["name"]]
                    )
    assert set(examples) == COLLECTIONS | {"/health"}
    assert examples.pop("/health") == {"status": "ok"}
    for example in examples.values():
        page = Page[object].model_validate(example)
        assert page.items == [] and not page.has_more
        assert page.limit == 20 and page.offset == 0


def test_export_is_json_on_stdout():
    result = subprocess.run(
        [
            "uv",
            "--no-cache",
            "run",
            "--no-sync",
            "--offline",
            "python",
            "-m",
            "backend.api.scripts.export_openapi",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    document = json.loads(result.stdout)
    assert "/api/v0/dossiers" in document["paths"]


@pytest.mark.skipif(shutil.which("make") is None, reason="GNU Make indisponible")
@pytest.mark.parametrize("compose", ["docker-compose", "docker compose"])
@pytest.mark.parametrize("directory", [ROOT, ROOT / "backend" / "api"])
def test_make_docker_workflow_is_explicit_and_non_destructive(compose, directory):
    result = subprocess.run(
        [
            "make",
            "--dry-run",
            "-f",
            str(ROOT / "Makefile"),
            f"COMPOSE={compose}",
            "docker-up",
            "microcks-import",
            "docker-down",
        ],
        cwd=directory,
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    output = result.stdout
    prefix = f'{compose} --env-file "{ROOT}/.env" -f "{ROOT}/backend/api/docker-compose.yml"'
    assert f"{prefix} up --build -d --wait api microcks" in output
    assert f'uv --directory "{ROOT}" run python -m backend.api.scripts.export_openapi' in output
    assert f'> "{ROOT}/build/openapi.json"' in output
    assert f"file=@{ROOT}/build/openapi.json;type=application/json" in output
    assert "http://127.0.0.1:8081/api/artifact/upload?mainArtifact=true" in output
    assert f"{prefix} down" in output
    assert "down -v" not in output
    assert "pre-commit" not in output


@pytest.mark.skipif(shutil.which("docker-compose") is None, reason="Compose indisponible")
def test_compose_build_sources_resolve_from_compose_directory(tmp_path):
    env_file = tmp_path / "empty.env"
    env_file.write_text("")
    result = subprocess.run(
        [
            "docker-compose",
            "--env-file",
            str(env_file),
            "-f",
            str(ROOT / "backend/api/docker-compose.yml"),
            "config",
            "--no-interpolate",
            "--format",
            "json",
        ],
        cwd=ROOT / "backend" / "api",
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    build = json.loads(result.stdout)["services"]["api"]["build"]
    context = Path(build["context"])
    assert context == ROOT
    dockerfile = context / build["dockerfile"]
    assert dockerfile.is_file()
    for line in dockerfile.read_text().splitlines():
        if line.startswith("COPY ") and "--from=" not in line:
            for source in shlex.split(line)[1:-1]:
                assert (context / source).exists(), f"Source Docker absente : {source}"


CHECK_PORTS = ROOT / "backend" / "api" / "scripts" / "check_ports.sh"
OFFER_STOP = ROOT / "backend" / "api" / "scripts" / "offer_stop.sh"
LISTENER = (
    "import socket, sys, time\n"
    "s = socket.socket()\n"
    "s.bind(('127.0.0.1', 0))\n"
    "s.listen()\n"
    "print(s.getsockname()[1], flush=True)\n"
    "time.sleep(30)\n"
)


@pytest.fixture
def listener():
    """Processus jetable qui écoute sur un port libre choisi par le système."""
    process = subprocess.Popen([sys.executable, "-c", LISTENER], stdout=subprocess.PIPE, text=True)
    assert process.stdout is not None
    port = int(process.stdout.readline())
    yield process, port
    process.kill()
    process.wait()


def run_script(script, *args, answer=None):
    """Lance le script sans Docker, avec un pseudo-terminal si une réponse est fournie."""
    env = {**os.environ, "DOCKER": "absent-docker"}
    if answer is None:
        return subprocess.run(
            [script, *args],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            env=env,
            timeout=15,
        )
    master, slave = pty.openpty()
    try:
        os.write(master, answer.encode() + b"\n")
        return subprocess.run(
            [script, *args], stdin=slave, capture_output=True, text=True, env=env, timeout=15
        )
    finally:
        os.close(master)
        os.close(slave)


needs_lsof = pytest.mark.skipif(shutil.which("lsof") is None, reason="lsof indisponible")


@needs_lsof
def test_check_ports_accepts_free_port(listener):
    process, port = listener
    process.kill()
    process.wait()
    assert run_script(CHECK_PORTS, str(port)).returncode == 0


@needs_lsof
@pytest.mark.parametrize("answer", [None, "n", ""])
def test_check_ports_keeps_process_without_consent(listener, answer):
    process, port = listener
    result = run_script(CHECK_PORTS, str(port), answer=answer)
    assert result.returncode == 1
    assert f"Port {port} occupé par" in result.stdout
    assert "abandon" in result.stderr
    assert process.poll() is None


@needs_lsof
@pytest.mark.parametrize("answer", ["o", "oui", "y"])
def test_check_ports_stops_process_with_consent(listener, answer):
    process, port = listener
    result = run_script(CHECK_PORTS, str(port), answer=answer)
    assert result.returncode == 0
    assert process.wait(timeout=5) is not None


@pytest.mark.skipif(shutil.which("make") is None, reason="GNU Make indisponible")
@pytest.mark.parametrize(
    ("target", "arguments"),
    [
        ("dev", "8000"),
        ("docker-up", "--ignore-project api 8000 8081"),
        ("microcks-up", "--ignore-project api 8081"),
    ],
)
def test_make_targets_check_ports_first(target, arguments):
    result = subprocess.run(
        ["make", "--dry-run", "-f", str(ROOT / "Makefile"), target],
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    first, *_ = result.stdout.splitlines()
    assert first == f'"{CHECK_PORTS}" {arguments}'


@pytest.mark.parametrize(("answer", "stopped"), [(None, False), ("n", False), ("o", True)])
def test_offer_stop_runs_stop_command_only_with_consent(tmp_path, answer, stopped):
    marker = tmp_path / "stopped"
    result = run_script(OFFER_STOP, "touch", str(marker), answer=answer)
    assert result.returncode == 0
    assert marker.exists() is stopped


@pytest.mark.parametrize("answer", [None, "n"])
def test_offer_stop_keeps_server_attached_without_consent(answer):
    result = run_script(OFFER_STOP, "--run", sys.executable, "-c", "print('fini')", answer=answer)
    assert result.returncode == 0
    assert "fini" in result.stdout


def test_offer_stop_kills_server_with_consent():
    # Un serveur survivant garderait la sortie ouverte : subprocess.run dépasserait le délai.
    result = run_script(OFFER_STOP, "--run", sys.executable, "-c", LISTENER, answer="o")
    assert result.returncode == 0


@pytest.mark.skipif(shutil.which("make") is None, reason="GNU Make indisponible")
@pytest.mark.parametrize(
    ("target", "arguments", "suffix"),
    [
        ("dev", "--run uv", "--reload"),
        ("docker-up", "docker-compose", " stop api microcks"),
        ("microcks-up", "docker-compose", " stop microcks"),
    ],
)
def test_make_server_targets_offer_stop(target, arguments, suffix):
    result = subprocess.run(
        ["make", "--dry-run", "-f", str(ROOT / "Makefile"), target],
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    *_, last = result.stdout.splitlines()
    assert last.startswith(f'"{OFFER_STOP}" {arguments}')
    assert last.endswith(suffix)
