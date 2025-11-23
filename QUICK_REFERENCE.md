# Quick Reference Guide - TeaPot User Service Tests

## 🚀 Quick Start Commands

```bash
# Setup (one-time)
cd /Users/janithpriyankara/Documents/projects/teapot/repos/teapot-integration-tests
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 📝 Running Tests

### Basic Commands
```bash
# Activate virtual environment (always do this first!)
source venv/bin/activate

# Run all tests
pytest

# Run with verbose output
pytest -v
pytest -vv  # Very verbose

# Run with print statements visible
pytest -s
```

### Run Specific Test Types
```bash
# Functional tests only
pytest -m functional

# Performance tests only
pytest -m performance

# Security tests only
pytest -m security

# Smoke tests (quick validation)
pytest -m smoke

# Auth tests only
pytest -m auth

# User management tests only
pytest -m users
```

### Run Specific Files or Tests
```bash
# Single file
pytest tests/functional/test_health.py

# Single test class
pytest tests/functional/test_users.py::TestCreateUser

# Single test
pytest tests/functional/test_health.py::TestHealthEndpoint::test_health_check_returns_200

# Multiple files
pytest tests/functional/test_health.py tests/functional/test_auth.py
```

### Using Test Runner Scripts
```bash
# Make executable (first time only)
chmod +x run_tests.sh run_load_test.sh

# Run test suites
./run_tests.sh functional    # Functional tests
./run_tests.sh performance    # Performance tests
./run_tests.sh security       # Security tests
./run_tests.sh smoke         # Smoke tests
./run_tests.sh all           # All tests

# With verbose output
./run_tests.sh functional -v
./run_tests.sh all -vv
```

## 📊 Advanced Options

### Parallel Execution
```bash
# Install xdist first (if not already)
pip install pytest-xdist

# Run with all CPU cores
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

### Coverage Reports
```bash
# Install coverage (if not already)
pip install pytest-cov

# Run with coverage
pytest --cov=tests

# Generate HTML report
pytest --cov=tests --cov-report=html
open htmlcov/index.html
```

### HTML Test Reports
```bash
# Install pytest-html (if not already)
pip install pytest-html

# Generate HTML report
pytest --html=report.html --self-contained-html
open report.html
```

### Re-run Failed Tests
```bash
# Run only last failed tests
pytest --lf

# Run failed tests first, then others
pytest --ff
```

### Stop on First Failure
```bash
# Stop after first failure
pytest -x

# Stop after 3 failures
pytest --maxfail=3
```

## 🔍 Debugging Tests

### Show Print Statements
```bash
pytest -s
```

### Show Detailed Errors
```bash
pytest -vv --tb=long
```

### Show Local Variables on Failure
```bash
pytest -l
```

### Debug Specific Test
```bash
pytest tests/functional/test_auth.py::TestAuthLogin::test_login_with_valid_credentials -vv -s
```

### Show Test Duration
```bash
# Show 10 slowest tests
pytest --durations=10

# Show all test durations
pytest --durations=0
```

## ⚡ Performance Testing

### Using pytest-benchmark
```bash
# Run performance tests
pytest tests/performance/test_performance.py

# Compare benchmarks
pytest tests/performance/ --benchmark-compare
```

### Using Locust

#### Web UI Mode (Interactive)
```bash
# Default (localhost:8080)
./run_load_test.sh

# Custom host
./run_load_test.sh http://api-dev.teapot.lk

# Or manually
locust -f tests/performance/locustfile.py --host=http://localhost:8080
# Then open http://localhost:8089
```

#### Headless Mode (Automated)
```bash
# Run load test
./run_load_test.sh http://localhost:8080 10 2 60s headless

# Custom parameters
locust -f tests/performance/locustfile.py \
  --host=http://localhost:8080 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 120s \
  --headless \
  --html=load_test_report.html
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Edit configuration
nano .env

# View current config (without showing secrets)
grep -v "PASSWORD\|TOKEN" .env
```

### Test Different Environments
```bash
# Local
export TEST_ENV=local
export BASE_URL=http://localhost:8080/api/v1
pytest

# Dev
export TEST_ENV=dev
export BASE_URL=https://api-dev.teapot.lk/api/v1
pytest

# Prod (be careful!)
export TEST_ENV=prod
export BASE_URL=https://api.teapot.lk/api/v1
pytest -m smoke  # Only smoke tests on prod!
```

## 📈 CI/CD Integration

### Run Tests in CI Pipeline
```bash
# Functional + Security (recommended for PR checks)
pytest -m "functional or security" --junitxml=report.xml

# All tests with coverage
pytest --cov=tests --cov-report=xml --junitxml=report.xml

# Smoke tests only (quick validation)
pytest -m smoke --junitxml=report.xml
```

## 🐛 Troubleshooting

### Clear Cache
```bash
pytest --cache-clear
rm -rf .pytest_cache
```

### Install Missing Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Check Test Discovery
```bash
# List all tests without running
pytest --collect-only

# Count tests
pytest --collect-only -q | tail -1
```

### Verify Environment
```bash
# Check Python version
python --version

# Check installed packages
pip list | grep pytest

# Check current directory
pwd

# Verify service is running
curl http://localhost:8080/api/v1/health
```

## 📋 Common Test Patterns

### Run Tests by Pattern
```bash
# All tests with "login" in name
pytest -k login

# All tests with "create" or "update"
pytest -k "create or update"

# Exclude slow tests
pytest -m "not slow"
```

### Watch Mode (Continuous Testing)
```bash
# Install pytest-watch
pip install pytest-watch

# Run in watch mode
ptw  # Re-runs tests on file changes
```

## 💡 Pro Tips

1. **Always activate venv first**: `source venv/bin/activate`
2. **Run smoke tests first**: `pytest -m smoke` to validate setup
3. **Use parallel execution**: `pytest -n auto` for faster runs
4. **Check service first**: `curl http://localhost:8080/api/v1/health`
5. **Review failures**: Use `-vv` for detailed output
6. **Clean up**: Tests auto-cleanup but check for orphaned data
7. **Update dependencies**: `pip install -r requirements.txt --upgrade`

## 🔒 Security Testing Reminders

- ⚠️ Never run security tests against production
- ⚠️ Use isolated test environments
- ⚠️ Some security tests may trigger rate limiting
- ⚠️ Review test data before committing

## 📞 Get Help

```bash
# Pytest help
pytest --help

# List all markers
pytest --markers

# List all fixtures
pytest --fixtures
```

---

**Happy Testing! 🧪**
