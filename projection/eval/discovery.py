"""Découverte des métriques et des prédicteurs : les sous-classes concrètes d'une classe de base."""

import inspect


def instances[T](base: type[T], package: str) -> list[T]:
    """Une instance de chaque sous-classe concrète de base définie dans package, dans l'ordre où
    elles sont importées. Une sous-classe définie ailleurs (dans un test, par exemple) n'est pas
    prise."""
    found: list[T] = []
    todo: list[type[T]] = [base]
    while todo:
        cls = todo.pop(0)
        todo += cls.__subclasses__()
        if not inspect.isabstract(cls) and cls.__module__.startswith(f"{package}."):
            found.append(cls())
    return found
