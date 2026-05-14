# Contributing

Thanks for your interest in improving the official Python client for
[twtapi.io](https://twtapi.io).

## Reporting issues

- **Bug reports**: open an issue with a minimal reproduction snippet,
  the SDK version (`python -c "import twtapi; print(twtapi.__version__)"`),
  and the Python version.
- **Feature requests** should describe a real use case. If the missing
  capability isn't already documented at <https://twtapi.io/docs>, raise
  it there first — this SDK only wraps the public API.

## Development

```bash
git clone https://github.com/twtapi/twtapi-python
cd twtapi-python
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
```

Run the checks before opening a PR:

```bash
ruff check src tests
mypy src
pytest
```

## Adding endpoints

This SDK is a thin, deterministic wrapper around the HTTP API. Every
method maps 1:1 to one endpoint documented at <https://twtapi.io/docs>.

When the public API gains a new endpoint:
1. Add the method to the relevant `src/twtapi/resources/<area>.py` file.
2. Mirror it in the async resource class in the same file.
3. If the endpoint paginates, add a `*_iter` companion.
4. Add an entry to the README method table.
5. Add a `respx`-mocked unit test in `tests/`.
6. Bump the version in `pyproject.toml` and add a `CHANGELOG.md` entry.

## Style

- Format with `ruff format` (line length 100).
- All code is type-annotated; `mypy --strict` must pass.
- Public symbols documented with short docstrings — link back to the
  HTTP endpoint by path.
- Never log full request or response bodies. Mask cookie / API-key
  values.

## License

By contributing, you agree your contributions are licensed under the MIT
license that covers the project.
