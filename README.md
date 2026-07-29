# ezgit-sync

![PyPI version](https://img.shields.io/pypi/v/ezgit-sync.svg)

This package is a basic git automator for deep learning and machine learning tasks.

* [GitHub](https://github.com/hasanaliozkan-dev/ezgit-sync/) | [PyPI](https://pypi.org/project/ezgit-sync/) | [Documentation](https://hasanaliozkan-dev.github.io/ezgit-sync/)
* Created by [Hasan Ali Özkan](https://hasanaliozkan-dev.github.io/) | GitHub [@hasanaliozkan-dev](https://github.com/hasanaliozkan-dev) | PyPI [@hasanaliozkan](https://pypi.org/user/hasanaliozkan/)
* MIT License

## Features

* TODO

## Documentation

Documentation is built with [Zensical](https://zensical.org/) and deployed to GitHub Pages.

* **Live site:** https://hasanaliozkan-dev.github.io/ezgit-sync/
* **Preview locally:** `just docs-serve` (serves at http://localhost:8000)
* **Build:** `just docs-build`

API documentation is auto-generated from docstrings using [mkdocstrings](https://mkdocstrings.github.io/).

Docs deploy automatically on push to `main` via GitHub Actions. To enable this, go to your repo's Settings > Pages and set the source to **GitHub Actions**.

## Development

To set up for local development:

```sh
# Clone your fork
git clone git@github.com:your_username/ezgit-sync.git
cd ezgit-sync

# Install dependencies
uv sync

# Create a branch for development
git checkout -b feature/new-awesome-feature
```

This installs the CLI globally but with live updates - any changes you make to the source code are immediately available when you run `autogit`.

Run tests:

```bash
uv run pytest
```

Run quality checks (format, lint, type check, test):

```bash
just qa
```

## Author

auto_git was created in 2026 by Hasan Ali Özkan.

Built with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
