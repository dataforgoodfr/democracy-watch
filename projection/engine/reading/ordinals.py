"""Mots-nombres du français juridique : ordinaux (« troisième », « dernier ») et cardinaux."""

ORDINALS = {
    **{
        word: rank
        for rank, word in enumerate(
            "premier deuxième troisième quatrième cinquième sixième septième huitième neuvième "
            "dixième onzième douzième treizième quatorzième quinzième seizième dix-septième "
            "dix-huitième dix-neuvième vingtième".split(),
            1,
        )
    },
    "première": 1,
    "second": 2,
    "seconde": 2,
    "dernier": -1,
    "dernière": -1,
    "avant-dernier": -2,
    "avant-dernière": -2,
}
CARDINALS = {
    word: number
    for number, word in enumerate(
        "deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize "
        "dix-sept dix-huit dix-neuf vingt".split(),
        2,
    )
}
