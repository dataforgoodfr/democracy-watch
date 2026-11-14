"""Tests du découpage en alinéas et de l'itération des articles."""

from democracy_watch.articles import Alinea, Article, iter_articles, split_alineas


class _FakeCursor:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows
        self.executed: list[tuple[str, tuple]] = []

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, query: str, params: tuple) -> None:
        self.executed.append((query, params))

    def __iter__(self):
        return iter(self._rows)


class _FakeConnection:
    def __init__(self, rows: list[dict]) -> None:
        self.cursor_obj = _FakeCursor(rows)

    def cursor(self) -> _FakeCursor:
        return self.cursor_obj


def test_split_alineas_canutes_glued_numbers_ignores_article_refs_and_years():
    content = (
        "1L'Assemblée nationale adopte l'article L. 253-7 applicable au 1er mars 2026. "
        "2Vu l'article 3 du code général des collectivités territoriales. "
        "3« Les dispositions du 2° entrent en vigueur en 2027. »"
    )

    assert split_alineas(content) == (
        Alinea(1, "L'Assemblée nationale adopte l'article L. 253-7 applicable au 1er mars 2026."),
        Alinea(2, "Vu l'article 3 du code général des collectivités territoriales."),
        Alinea(3, "« Les dispositions du 2° entrent en vigueur en 2027. »"),
    )


def test_split_alineas_html_source():
    html = (
        "<p>1 L'article L. 253-7 s'applique à compter de 2026.</p>"
        "<p>2 Le rapport est remis au Parlement avant le 1er mars 2027.</p>"
    )

    assert split_alineas(html) == (
        Alinea(1, "L'article L. 253-7 s'applique à compter de 2026."),
        Alinea(2, "Le rapport est remis au Parlement avant le 1er mars 2027."),
    )


def test_split_alineas_single_paragraph_without_numbers():
    content = "L'article L. 253-7 est prorogé jusqu'au 31 décembre 2026."

    assert split_alineas(content) == (
        Alinea(1, "L'article L. 253-7 est prorogé jusqu'au 31 décembre 2026."),
    )


def test_split_alineas_empty_returns_empty_tuple():
    assert split_alineas("") == ()
    assert split_alineas("   ") == ()


def test_iter_articles_streams_articles_with_dossier_metadata():
    rows = [
        {
            "id": "art-12",
            "texte_ref": "PIONANR5L17B0420",
            "numero": "12",
            "libelle": "Article 12",
            "ordre": 12,
            "contenu": "1Premier alinéa L. 253-7. 2Deuxième alinéa 2026.",
            "dossier_id": "dos-1",
            "source_url": "https://www.assemblee-nationale.fr/dyn/17/textes/l17b0420",
            "dossier_titre": "Proposition de loi visant à protéger la biodiversité",
            "dossier_procedure_code": "PPL",
            "dossier_procedure_libelle": "Proposition de loi",
            "dossier_etat": "En commission",
            "dossier_commission": "Commission du développement durable",
        }
    ]
    conn = _FakeConnection(rows)

    articles = list(iter_articles(conn))

    assert len(articles) == 1
    article = articles[0]
    assert isinstance(article, Article)
    assert article.uid == "art-12"
    assert article.number == "12"
    assert article.title == "Article 12"
    assert article.alineas == (
        Alinea(1, "Premier alinéa L. 253-7."),
        Alinea(2, "Deuxième alinéa 2026."),
    )
    assert article.dossier_title == "Proposition de loi visant à protéger la biodiversité"
    assert article.dossier_type == "PPL"
    assert article.dossier_commission == "Commission du développement durable"
    assert article.dossier_stage == "En commission"
    assert conn.cursor_obj.executed[0][1] == (17, 17)
