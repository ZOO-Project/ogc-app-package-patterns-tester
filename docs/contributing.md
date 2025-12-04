# Contributing

Contributions are welcome! Here's how to get started.

## Getting Started

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ogc-app-package-patterns-tester.git
   cd ogc-app-package-patterns-tester
   ```
3. **Install Hatch**:
   ```bash
   pip install hatch
   ```
4. **Build the package**:
   ```bash
   hatch build --clean
   ```

## Development Workflow

### Running Tests

```bash
# Run all unit tests
hatch run test

# Run tests with coverage
hatch run test-cov

# Run specific test file
hatch run pytest tests/test_client.py -v

# Run integration tests (requires server credentials)
export OGC_TEST_SERVER_URL="https://your-server.com/ogc-api/"
export OGC_TEST_ACCESS_TOKEN="your-bearer-token"
hatch run test -m integration
```

### Code Quality

```bash
# Format code with Black
hatch run fmt

# Run linter with Ruff
hatch run lint

# Run all quality checks
hatch run check
```

### Testing Your Changes

Before submitting a pull request:

1. **Run all tests**: `hatch run test`
2. **Check code quality**: `hatch run check`
3. **Test manually**: Try the CLI with your changes
4. **Update documentation**: If you added features

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines (enforced by Black)
- Use type hints for function parameters and return values
- Add docstrings to public functions and classes
- Keep functions focused and small

### Testing

- Write tests for new features
- Keep test coverage above 80%
- Use mocks for external API calls in unit tests
- Add integration tests for end-to-end scenarios

### Commit Messages

Use clear and descriptive commit messages:

```bash
# Good
git commit -m "Add support for pattern-13 with multiple outputs"
git commit -m "Fix timeout handling in job monitoring"

# Not so good
git commit -m "fix bug"
git commit -m "updates"
```

## Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes** and commit them:
   ```bash
   git commit -am 'Add amazing feature'
   ```

3. **Push to your fork**:
   ```bash
   git push origin feature/amazing-feature
   ```

4. **Open a Pull Request** on GitHub with:
   - Clear description of changes
   - Link to related issues
   - Screenshots/examples if applicable

## Project Structure

```
ogc-app-package-patterns-tester/
├── src/ogc_patterns_tester/    # Main package
│   ├── cli.py                  # CLI with Click
│   ├── client.py               # OGC API client wrapper
│   ├── patterns_manager.py     # Pattern orchestration
│   ├── models.py               # Data models
│   └── utils.py                # Utilities
├── tests/                      # Test suite
│   ├── test_client.py
│   ├── test_patterns_manager.py
│   ├── test_models.py
│   └── test_integration.py
├── data/patterns/              # Pattern configurations
├── docs/                       # Documentation
└── pyproject.toml             # Project configuration
```

## Adding New Features

### Adding a New Pattern

1. Add pattern configuration in `data/patterns/pattern-X.json`
2. Update pattern list in documentation
3. Add tests in `tests/test_patterns_manager.py`

### Adding a New CLI Command

1. Add command in `src/ogc_patterns_tester/cli.py`
2. Update CLI documentation
3. Add tests for the command

## Getting Help

- Open an issue for bugs or feature requests
- Join discussions on GitHub
- Check existing issues and pull requests

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
