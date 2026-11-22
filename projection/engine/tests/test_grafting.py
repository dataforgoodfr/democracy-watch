"""Origine des mots du texte projeté : arbre après patch, puis `project` et `consolidate`."""

from engine import usecases
from engine.domain.documents import Amendment, Article, Text
from engine.domain.grafting import graft
from engine.domain.patch import Splice
from engine.domain.tree import Origin, article_of

LINES = (
    "Le fait de vendre est puni de 4 000 euros.",
    "Le présent article entre en vigueur demain.",
)


def tree():
    return article_of("T0", Article("3", LINES))


def by_text(paragraph):
    return {word.text: word for word in paragraph.words}


def test_untouched_nodes_are_shared_with_the_base():
    base = tree()
    after = graft(
        base,
        (
            Splice.on_chars(
                "3",
                0,
                3,
                7,
                "but",
            ),
        ),
        "T0",
    )
    assert after.paragraphs[1] is base.paragraphs[1]
    assert after.paragraphs[0] is not base.paragraphs[0]


def test_substituted_words_carry_the_amendment_and_others_keep_their_id():
    base = tree()
    old = LINES[0]
    start = old.index("puni")
    patch = (
        Splice.on_chars(
            "3",
            0,
            start,
            start + 4,
            "sanctionné",
        ),
    )
    patch = tuple(Splice(s.article, s.span, s.new, s.line, "CE5") for s in patch)
    after = graft(base, patch, "T0")
    paragraph = after.paragraphs[0]
    assert paragraph.text == "Le fait de vendre est sanctionné de 4 000 euros."
    words = by_text(paragraph)
    assert words["sanctionné"].origin == Origin("T0", "CE5")
    assert words["sanctionné"].id == "T0/3/a1/CE5.m1"
    assert words["vendre"] == by_text(base.paragraphs[0])["vendre"]
    assert words["euros"].origin == Origin("T0")


def test_a_word_cut_in_its_middle_is_written_whole_by_the_amendment():
    base = tree()
    start = LINES[0].index("000")
    patch = (Splice("3", (start, start + 1), "5", 0, "CE5"),)
    paragraph = graft(base, patch, "T0").paragraphs[0]
    assert paragraph.text == "Le fait de vendre est puni de 4 500 euros."
    assert by_text(paragraph)["500"].origin == Origin("T0", "CE5")
    assert by_text(paragraph)["4"].origin == Origin("T0")


def test_two_amendments_on_disjoint_words_keep_their_own_origin():
    base = tree()
    a = LINES[0].index("vendre")
    b = LINES[0].index("euros")
    patch = (
        Splice("3", (a, a + 6), "céder", 0, "CE1"),
        Splice("3", (b, b + 5), "francs", 0, "CE2"),
    )
    words = by_text(graft(base, patch, "T0").paragraphs[0])
    assert words["céder"].origin.amendment == "CE1"
    assert words["francs"].origin.amendment == "CE2"
    assert words["puni"].origin.amendment is None


def test_written_identifiers_do_not_repeat_in_a_paragraph():
    base = tree()
    patch = (
        Splice("3", (0, 0), "Ici ", 0, "CE1"),
        Splice("3", (3, 7), "but", 0, "CE1"),
    )
    ids = [w.id for w in graft(base, patch, "T0").paragraphs[0].words]
    assert len(ids) == len(set(ids))


def test_inserted_and_rewritten_paragraphs_are_written_by_the_amendment():
    base = tree()
    patch = (Splice.on_lines("3", 1, 1, ("Un alinéa.", "Un autre.")),)
    patch = tuple(Splice(s.article, s.span, s.new, s.line, "CE7") for s in patch)
    after = graft(base, patch, "T0")
    assert [p.id for p in after.paragraphs] == ["T0/3/a1", "CE7/a1", "CE7/a2", "T0/3/a2"]
    assert after.paragraphs[1].words[0].origin == Origin("T0", "CE7")
    assert after.paragraphs[0] is base.paragraphs[0]


def test_deleting_the_article_leaves_no_paragraph():
    after = graft(tree(), (Splice("3", None, (), None, "CE1"),), "T0")
    assert after.paragraphs == ()


def test_rewriting_the_article_replaces_every_paragraph():
    after = graft(tree(), (Splice("3", None, ("Nouveau.",), None, "CE1"),), "T0")
    assert after.lines == ("Nouveau.",)
    assert after.paragraphs[0].id == "CE1/a1"


def amendment(number, *paragraphs):
    return Amendment(
        number, "ART. 3", "".join(f"<p>{p}</p>" for p in paragraphs), id=f"UID-{number}"
    )


def test_project_and_consolidate_trace_each_word_to_its_amendment():
    text = Text("T0", (Article("3", LINES),))
    one = amendment(
        "CE1", "À l'alinéa 1, substituer au mot :", "« vendre »", "le mot :", "« céder »."
    )
    two = amendment(
        "CE2", "À l'alinéa 2, substituer au mot :", "« demain »", "le mot :", "« lundi »."
    )
    projection = usecases.project(text, one)
    assert projection.result is not None
    assert (
        "".join(w.text for w in projection.result.paragraphs[0].words) == projection.result.lines[0]
    )
    consolidation = usecases.consolidate(text, [one, two])
    (article,) = consolidation.articles
    origins = {word.text: word.origin.amendment for p in article.paragraphs for word in p.words}
    assert origins["céder"] == "UID-CE1"
    assert origins["lundi"] == "UID-CE2"
    assert origins["fait"] is None
    assert tuple(p.text for p in article.paragraphs) == article.lines


def test_a_pure_deletion_does_not_steal_the_neighbouring_word_from_its_writer():
    """A supprime « de » et l'espace, B change « la » en « le » : « le » est à B, pas à A."""
    base = article_of("T0", Article("3", ("de la loi",)))
    patch = (
        Splice("3", (0, 3), "", 0, "CE1"),
        Splice("3", (4, 5), "e", 0, "CE2"),
    )
    paragraph = graft(base, patch, "T0").paragraphs[0]
    assert paragraph.text == "le loi"
    assert by_text(paragraph)["le"].origin == Origin("T0", "CE2")
