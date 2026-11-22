import pytest

from engine.domain.refusal import Reason, Refusal
from engine.reading.dispositif import dispositif_lines


@pytest.mark.parametrize(
    ("markup", "expected"),
    [
        ("<p>un</p><p>deux</p>", ("un", "deux")),
        ("<p class='x'>un</p>\n<P>deux</P>", ("un", "deux")),
        ("<p>un</p><p> </p><p></p>", ("un",)),
        ("<p>a <b>b</b> c</p>", ("a b c",)),
        ("<p>&lt;b&gt; &amp; l&rsquo;a</p>", ("<b> & l’a".replace("’", "'"),)),
        ("<p>&laquo;&nbsp;a&nbsp;&raquo;</p>", ("«a»",)),
        ("<p>x y</p>", ("x y",)),
        ("<p>a<br>b</p><p>c<BR/>d</p><p>e<br />f</p>", ("a b", "c d", "e f")),
        ("<p>a</p>\n  <p>b</p>\n", ("a", "b")),
        ("", ()),
        ("<p></p>", ()),
    ],
)
def test_dispositif_lines(markup, expected):
    assert dispositif_lines(markup) == expected


@pytest.mark.parametrize(
    "markup",
    [
        "texte brut",
        "<p>un</p> texte <p>deux</p>",
        "<p>un</p><table><tr><td>x</td></tr></table>",
        "<ul><li>x</li></ul><p>un</p>",
        "<div><p>un</p></div>",
    ],
)
def test_dispositif_lines_refuses_content_outside_paragraphs(markup):
    with pytest.raises(Refusal) as error:
        dispositif_lines(markup)
    assert error.value.reason is Reason.OUT_OF_SCOPE
