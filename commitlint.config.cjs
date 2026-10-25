// Conventional Commits : `type(scope): sujet`, le scope est la partie du dépôt touchée.
module.exports = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "scope-enum": [
      2,
      "always",
      [
        "api",
        "brand",
        "state",
        "theme",
        "ui",
        "data",
        "screens",
        "web",
        "docs",
        "server",
        "e2e",
        "ci",
        "deps",
        "repo",
      ],
    ],
  },
};
