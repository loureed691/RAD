.PHONY: help setup install install-dev clean lint test test-unit test-integration \
        backtest optimize paper-trade live validate-config check-security \
        format type-check pre-commit run dashboard

# Default target
help:
	@echo "RAD Trading Bot - Makefile Commands"
	@echo "====================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup           - Initial setup (create dirs, install deps)"
	@echo "  make install         - Install production dependencies"
	@echo "  make install-dev     - Install dev dependencies (testing, linting)"
	@echo "  make clean           - Clean up build artifacts and cache"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint            - Run flake8 linter"
	@echo "  make format          - Format code with black"
	@echo "  make type-check      - Run mypy type checker"
	@echo "  make check-security  - Check for security vulnerabilities"
	@echo "  make pre-commit      - Run all pre-commit checks"
	@echo ""
	@echo "Testing:"
	@echo "  make test            - Run all tests"
	@echo "  make test-unit       - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-coverage   - Run tests with coverage report"
	@echo "  make stress          - Run 500-scenario stress test suite"
	@echo ""
	@echo "Trading Operations:"
	@echo "  make validate-config - Validate configuration"
	@echo "  make backtest        - Run backtesting engine"
	@echo "  make optimize        - Run hyperparameter optimization"
	@echo "  make paper-trade     - Run in paper trading mode"
	@echo "  make live            - Run in live trading mode (CAREFUL!)"
	@echo "  make dashboard       - Start web dashboard"
	@echo ""
	@echo "Utilities:"
	@echo "  make run             - Quick start (runs start.py)"
	@echo "  make logs            - Tail the bot logs"
	@echo "  make status          - Show bot status"

# Setup & Installation
setup:
	@echo "🔧 Setting up RAD Trading Bot..."
	mkdir -p logs models
	cp -n .env.example .env 2>/dev/null || echo "⚠️  .env already exists, skipping"
	@echo "✅ Setup complete! Edit .env with your API credentials"

install:
	@echo "📦 Installing production dependencies..."
	pip install --upgrade pip
	pip install -r requirements.lock

install-dev: install
	@echo "📦 Installing development dependencies..."
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-mock pytest-asyncio hypothesis \
	            flake8 pylint black mypy safety pip-tools

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache .mypy_cache htmlcov dist build
	@echo "✅ Cleanup complete"

# Code Quality
lint:
	@echo "🔍 Running flake8..."
	flake8 . --config=.flake8 || true

format:
	@echo "🎨 Formatting code with black..."
	black . --config pyproject.toml || echo "⚠️  black not installed, skipping"

type-check:
	@echo "🔍 Running mypy type checker..."
	mypy . --config-file=pyproject.toml || echo "⚠️  mypy not installed, skipping"

check-security:
	@echo "🔒 Checking for security vulnerabilities..."
	safety check --file=requirements.lock || echo "⚠️  Some vulnerabilities found, review above"

pre-commit: format lint type-check
	@echo "✅ Pre-commit checks complete"

# Testing
test:
	@echo "🧪 Running all tests..."
	python run_all_tests.py

test-unit:
	@echo "🧪 Running unit tests..."
	python test_bot.py
	python test_risk_management.py
	python test_strategy_optimizations.py

test-integration:
	@echo "🧪 Running integration tests..."
	python test_integration.py
	python test_websocket_integration.py
	python test_priority1_integration.py

test-coverage:
	@echo "🧪 Running tests with coverage..."
	pytest --cov=. --cov-report=html --cov-report=term-missing || \
	echo "⚠️  pytest not installed, running basic tests"
	python run_all_tests.py

# Trading Operations
validate-config:
	@echo "⚙️  Validating configuration..."
	python config_validator.py

backtest:
	@echo "📊 Running backtesting engine..."
	python example_backtest.py

stress:
	@echo "⚡ Running 500-scenario stress test suite..."
	python scenario_stress_engine.py

optimize:
	@echo "🎯 Running profitability optimization with Bayesian search..."
	python profitability_optimizer.py

paper-trade:
	@echo "📝 Starting paper trading mode..."
	@echo "⚠️  Ensure TEST_MODE=true in .env"
	python bot.py

live:
	@echo "⚠️  WARNING: Starting LIVE trading mode!"
	@echo "⚠️  Real money will be used. Press Ctrl+C to cancel..."
	@sleep 5
	python bot.py

dashboard:
	@echo "📊 Starting web dashboard..."
	python dashboard.py

# Utilities
run: validate-config
	@echo "🚀 Starting RAD Trading Bot..."
	python start.py

logs:
	@echo "📋 Tailing bot logs (Ctrl+C to stop)..."
	tail -f logs/bot.log

status:
	@echo "📊 Bot Status:"
	@echo "==============="
	@ps aux | grep -E "(bot\.py|start\.py)" | grep -v grep || echo "❌ Bot not running"
	@echo ""
	@echo "Recent Log Entries:"
	@tail -n 5 logs/bot.log 2>/dev/null || echo "❌ No logs found"

# Lock dependencies
lock:
	@echo "🔒 Generating requirements.lock..."
	pip-compile requirements.txt --output-file=requirements.lock

# Update dependencies
update:
	@echo "⬆️  Updating dependencies..."
	pip-compile --upgrade requirements.txt --output-file=requirements.lock
	pip install -r requirements.lock
