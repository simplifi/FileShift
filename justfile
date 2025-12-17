# FileShift Development Tasks

# Default task - show available commands
default:
    @just --list

# Install project with uv
install:
    uv pip install -e ".[dev]"

# Run all tests
test:
    uv run pytest -v

# Run tests with coverage
test-cov:
    uv run pytest --cov --cov-report=html --cov-report=term

# Run specific test file
test-file FILE:
    uv run pytest -v {{FILE}}

# Run tests and watch for changes
test-watch:
    uv run pytest-watch

# Format code with black and isort
format:
    uv run black .
    uv run isort .
    uv run ruff --fix .

# Check code formatting
check:
    uv run black --check .
    uv run isort --check-only .
    uv run ruff check .
    uv run mypy src

# Run type checking
typecheck:
    uv run mypy src

# Clean build artifacts
clean:
    rm -rf build dist *.egg-info
    rm -rf .coverage htmlcov .pytest_cache
    rm -rf .mypy_cache .ruff_cache
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

# Build standalone app
build:
    uv run pyinstaller json_to_csv_multifile_pyqt.py \
        --name "FileShift" \
        --windowed \
        --onefile \
        --icon resources/icon.ico \
        --add-data "src:src"

# Run the GUI app
run:
    uv run python json_to_csv_multifile_pyqt.py

# Run the CLI
run-cli *ARGS:
    uv run python -m src.cli {{ARGS}}

# Generate sample data
generate-samples:
    uv run python scripts/generate_sample_data.py

# Run pre-commit hooks
pre-commit:
    uv run pre-commit run --all-files

# Set up pre-commit hooks
pre-commit-install:
    uv run pre-commit install

# Create a new release
release VERSION:
    git tag -a v{{VERSION}} -m "Release version {{VERSION}}"
    git push origin v{{VERSION}}

# Run benchmarks
benchmark:
    uv run pytest -v tests/benchmarks --benchmark-only

# Profile the application
profile FILE:
    uv run python -m cProfile -o profile.stats json_to_csv_multifile_pyqt.py {{FILE}}
    uv run python -m pstats profile.stats

# Update dependencies
update-deps:
    uv pip compile pyproject.toml -o requirements.txt --upgrade

# Create virtual environment with uv
venv:
    uv venv
    uv pip install -e ".[dev]"

# Serve documentation
docs-serve:
    uv run mkdocs serve

# Build documentation
docs-build:
    uv run mkdocs build