import json
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.app.articles.schemas import Article
from backend.api.scripts import export_microcks_samples as export

ARTICLE = {
    "uid": "A1",
    "text_reference": "T1",
    "number": "1",
    "label": "Article premier",
    "content": "Texte",
    "position": 1,
    "chamber": "assemblee",
    "legislative_term": 17,
    "dossier_uid": "D1",
    "source_url": None,
}


def operations(path):
    return json.loads(path.read_text().split("operations: ", 1)[1])


async def test_collection_pages_and_default_page(monkeypatch):
    rows = [Article.model_validate({**ARTICLE, "uid": f"A{index}"}) for index in range(130)]
    calls = []

    async def list_items(session, *, dossier_uid, limit, offset):
        calls.append((dossier_uid, limit, offset))
        return rows[offset : offset + limit]

    samples, everything = await export.collection(
        AsyncMock(spec=AsyncSession), "/api/v0/articles", "D1", list_items, {"dossier_uid": "D1"}
    )
    assert calls == [("D1", 101, 0), ("D1", 101, 100)]
    assert everything == rows
    assert [(item["name"], item["parameters"]) for item in samples] == [
        ("D1-offset-0", {"dossier_uid": "D1", "limit": 100, "offset": 0}),
        ("D1-offset-100", {"dossier_uid": "D1", "limit": 100, "offset": 100}),
        ("D1", {"dossier_uid": "D1"}),
    ]
    first, second, default = (item["response"] for item in samples)
    assert (len(first["items"]), first["has_more"]) == (100, True)
    assert (len(second["items"]), second["has_more"]) == (30, False)
    assert (len(default["items"]), default["limit"], default["has_more"]) == (20, 20, True)


def test_write_examples_chunks_and_escapes(tmp_path, monkeypatch):
    monkeypatch.setattr(export, "MAX_FILE_CHARS", 300)
    (tmp_path / "examples-99.yaml").write_text("ancien")
    samples = [
        export.sample("/api/v0/articles/{uid}", f"A{index}", {"uid": f"A{index}"}, ARTICLE)
        for index in range(3)
    ]
    samples[0]["response"] = {**ARTICLE, "content": "a\x8db c é"}
    export.write_examples(samples, tmp_path)
    files = sorted(tmp_path.glob("examples-*.yaml"))
    assert [file.name for file in files] == [f"examples-0{index}.yaml" for index in range(3)]
    text = files[0].read_text()
    assert text.startswith("apiVersion: mocks.microcks.io/v1alpha1\nkind: APIExamples\n")
    assert '"name": "democracy_watch_API", "version": "0.1.0"' in text
    assert "\x8d" not in text and " " not in text and "é" in text
    example = operations(files[0])["GET /api/v0/articles/{uid}"]["A0"]
    assert example["request"] == {"parameters": {"uid": "A0"}}
    assert example["response"]["status"] == "200"
    assert example["response"]["body"]["content"] == "a\x8db c é"
