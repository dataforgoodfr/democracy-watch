---

name: dinum-python
description: Apply DINUM, beta.gouv.fr and La Suite numérique Python engineering standards when creating, modifying or reviewing Python code.
---

# 🐍 DINUM & La Suite Python Engineering Standards

This skill defines the engineering standards applicable across backend Python services, Django/DRF applications, Celery workers, and data connectors.

> **Cross-cutting DINUM Principle :**
> Do not optimize for satisfying a checklist while degrading the product. DINUM/La Suite rules are intended to produce understandable, accessible, secure, and maintainable software. Repository context and user needs matter.

---

## 🎯 Activation Scope

Activate this skill whenever work touches:

- Python source files (`.py`)
- Django & Django REST Framework applications
- FastAPI or other Python APIs
- Python background workers & Celery tasks
- CLI scripts & Python tooling
- Python test suites (`pytest`, `unittest`, `responses`)
- Dependency and build configurations (`pyproject.toml`, `requirements.txt`, `pytest.ini`, `ruff.toml`)

---

## 🧭 Precedence Order

When recommendations conflict, apply this strict precedence:

1. **Explicit user instruction**
2. **Repository `AGENTS.md` / `AGENT.md` instructions**
3. **Existing repository configuration and CI (`pyproject.toml`, `ruff.toml`, `.flake8`, `setup.cfg`, `pytest.ini`)**
4. **Existing architectural/project conventions**
5. **DINUM / beta.gouv / La Suite recommendations**
6. **Generic Python / PEP 8 ecosystem best practices**

---

## 📋 Required Behaviour & Engineering Checklist

### 1. Inspect repository rules first

Before modifying Python:

- Inspect `pyproject.toml`, `ruff.toml`, `.flake8`, `setup.cfg`, `pytest.ini`, and CI workflows.
- Repository configuration always wins (e.g. Ruff with 88 characters wins over the historical handbook 99-character suggestion).
- Do not change project-wide formatting rules as part of an unrelated task.

### 2. Style, automated linting & imports

- Obey the project's configured formatter and linter (Ruff, Flake8, Black, isort).
- Do not manually fight the formatter or disable lint checks globally.
- Group imports into 6 distinct logical sections:
  1. `__future__` imports
  2. Standard library
  3. Frameworks (Django, DRF, FastAPI)
  4. Third-party packages
  5. Application / internal first-party modules
  6. Local / relative imports
- Avoid wildcard imports (`from module import *`).
- Do not leave commented-out code or debug `print()` statements.

### 3. Documentation & intent

- Public modules, classes, and functions must explain their purpose.
- Follow existing repository docstring conventions.
- Docstrings should explain intent and invariants, not merely paraphrase function names.

### 4. Functions & architecture

Prefer:

- Small cohesive functions with explicit inputs and outputs.
- Early returns when simplifying control flow.
- Clear domain boundaries and dependency injection for testability.
- Pure functions for domain calculations.

Avoid:

- Large multipurpose functions.
- Hidden global mutable state.
- Boolean-parameter explosions.
- Duplicated business logic or premature abstraction.
- Catching exceptions only to ignore them (`except Exception: pass`).

### 5. Type hints

- Annotate public interfaces, parameters, and return types.
- Model `None` explicitly (`Optional[T]` / `T | None`).
- Avoid unnecessary `Any`.
- Do not add type assertions solely to hide design flaws.

### 6. Errors & exception handling

- Errors must be explicit, actionable, and properly scoped.
- Never silently swallow unexpected exceptions.
- Do not expose internal traceback details or sensitive data in HTTP responses.
- Use stable machine-readable error schemas and correct HTTP status codes at API boundaries.

### 7. Django & database practices

- Prevent $N+1$ queries using `select_related()` and `prefetch_related()`.
- Wrap multi-table mutations inside atomic transactions (`transaction.atomic`).
- Avoid expensive operations inside loops over querysets.
- Maintain migration safety and backward compatibility; never rewrite existing migrations without a deliberate reason.
- Enforce authorization strictly server-side (never trust the client).

### 8. Defensive security

Follow La Suite security principles:

- Never version secrets or hardcode passwords/tokens.
- Mandatory anti-SSRF validation on outgoing HTTP requests (block private IP ranges: `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254`).
- Circuit Breaker and strict timeouts (3.5s max) on external API dependencies.
- Never deserialize untrusted data with unsafe mechanisms (e.g. raw `pickle`).

### 9. Automated testing

beta.gouv standards require automated testing:

- Update existing tests and add regression tests for bug fixes.
- Test critical business rules and failure paths.
- Mock external network calls with `responses` or `unittest.mock`.
- Ensure test filenames clearly indicate the module/behaviour under test.
- Run `cd server && uv run pytest` before declaring task complete (all Python lives in `server/`).

### 10. Technical documentation

Update technical documentation when a change introduces:

- New dependencies
- New environment variables
- New background workers / Celery tasks
- New API endpoints (update OpenAPI/Swagger specs)
- Architecture modifications

### 11. Final Verification Checklist

Before declaring a Python task complete:

1. Review the diff.
2. Remove debugging statements.
3. Run the configured formatter / check mode.
4. Run configured linter (e.g. Ruff / Flake8).
5. Run type checker when applicable.
6. Run relevant test suites (`cd server && uv run pytest`).
7. Verify database migrations if applicable.
8. Report any command that could not be run.

---

## 🔗 Official Sources & References

- [La Suite numérique — Developer Handbook](https://suitenumerique.gitbook.io/handbook)
- [La Suite — Python Best Practices](https://github.com/suitenumerique/dev-handbook/blob/main/python.md)
- [La Suite — Security Rules](https://github.com/suitenumerique/dev-handbook/blob/main/security.md)
- [La Suite — Code Reviews](https://github.com/suitenumerique/dev-handbook/blob/main/code-reviews.md)
- [beta.gouv — Official Quality Standards](https://standards.beta.gouv.fr/standards)
- [beta.gouv — Uniform Source Code Standard](https://github.com/betagouv/standards/blob/main/qualit%C3%A9-logicielle/le-code-source-est-uniforme.md)
- [beta.gouv — Unit & E2E Testing Standard](https://github.com/betagouv/standards/blob/main/qualit%C3%A9-logicielle/le-code-est-instrumente-par-des-tests-unitaires-et-des-tests-e2e.md)
- [beta.gouv — Technical Documentation Standard](https://github.com/betagouv/standards/blob/main/qualit%C3%A9-logicielle/les-aspects-techniques-du-produit-sont-documentes.md)
- [La Suite Docs Backend Configuration](https://github.com/suitenumerique/docs/blob/main/src/backend/pyproject.toml)
