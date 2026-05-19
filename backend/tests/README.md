# Backend Tests

## Setup

```bash
cd backend
pip install -r requirements.txt
```

## Run all tests with coverage

```bash
pytest
```

This will:
- Run all tests in the `tests/` directory
- Report per-module coverage in the terminal
- Generate an HTML report at `htmlcov/index.html`
- Fail if overall coverage drops below **75%**

## Run a specific file

```bash
pytest tests/test_guardian.py -v
pytest tests/test_markdown.py -v
pytest tests/test_security.py -v
pytest tests/test_schemas.py -v
```

## Run only fast (no-DB) tests

```bash
pytest tests/test_guardian.py tests/test_markdown.py tests/test_schemas.py tests/test_security.py -v
```

## Test structure

| File | What it covers |
|---|---|
| `test_guardian.py` | All `Guardian` permission methods + `ensure_*` helpers |
| `test_markdown.py` | `render`, `_process_mentions`, `_process_quotes`, `extract_excerpt`, `count_words` |
| `test_schemas.py` | Pydantic validation, camelCase aliases, `UserOut.from_orm` |
| `test_security.py` | `create_dev_jwt`, `validate_dev_token`, `_is_dev_token` |
| `test_routes_auth.py` | `GET /api/auth/me`, `POST /api/auth/dev-login` |
| `test_routes_categories.py` | `GET /api/categories`, `POST /api/categories` |
| `test_routes_posts.py` | `POST /api/posts`, `POST /api/posts/{id}/like`, `.../bookmark` |
| `test_routes_bookmarks.py` | `GET /api/bookmarks` |
| `test_routes_users.py` | `GET /api/u/{username}`, `PUT /api/u/{username}` |
