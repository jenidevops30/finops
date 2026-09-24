# Phase 1 Validation

## Commands

    pip install -e '.[dev]'
    pytest --cov=finops_platform --cov-report=term-missing
    ruff check .
    bandit -r src
    streamlit run streamlit_app.py

## Definition of done

1. Foundation modules exist and are modular.
2. Domain models validate core normalized data.
3. Configuration is environment driven.
4. Logging is centralized.
5. AWS access is isolated behind a read-only client boundary.
6. Tests cover configuration, model validation, and boundary validation.
7. CI runs quality, test, and Bandit checks.
8. No new AWS mutation operation is introduced by Phase 1.
