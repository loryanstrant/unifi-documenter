# UniFi Documenter

UniFi Documenter is a Python-based tool for automatically generating documentation and network diagrams from UniFi controller configurations. It connects to UniFi controllers via API to extract network topology, device configurations, and settings to create comprehensive network documentation.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

- Bootstrap and setup the development environment:
  - `python3 --version` -- verify Python 3.8+ is installed
  - `python3 -m venv venv` -- create virtual environment (takes 30 seconds)
  - `source venv/bin/activate` -- activate virtual environment
  - `pip install --upgrade pip` -- upgrade pip (takes 1 minute)
  - `pip install -r requirements.txt` -- install dependencies. NEVER CANCEL. Takes 2-5 minutes depending on network speed. Set timeout to 10+ minutes.
  - `pip install -e .` -- install package in development mode (takes 30 seconds)

- Build and test the application:
  - ALWAYS run the bootstrapping steps first
  - `python -m pytest` -- run test suite. NEVER CANCEL. Takes 3-8 minutes. Set timeout to 15+ minutes.
  - `python -m pytest --cov=unifi_documenter` -- run tests with coverage (takes 5-10 minutes)
  - `flake8 .` -- run linting (takes 30 seconds)
  - `black --check .` -- check code formatting (takes 15 seconds)
  - `mypy unifi_documenter/` -- run type checking (takes 1-2 minutes)

- Run the CLI application:
  - ALWAYS run the bootstrapping steps first
  - `python -m unifi_documenter --help` -- show available commands
  - `python -m unifi_documenter discover --host <controller-ip>` -- discover UniFi controller
  - `python -m unifi_documenter document --host <controller-ip> --username <user> --password <pass>` -- generate documentation
  - `python -m unifi_documenter export --format pdf --output ./network-docs.pdf` -- export documentation

- Development server (if web interface exists):
  - `python -m unifi_documenter serve --port 8080` -- start development server
  - Access at http://localhost:8080

## Validation

- ALWAYS manually validate any new code changes by running through complete end-to-end scenarios after making changes.
- **SCENARIO VALIDATION**: After making changes, always test the core workflow:
  1. `python -m unifi_documenter discover --host demo.ubnt.com` -- test controller discovery
  2. `python -m unifi_documenter document --host demo.ubnt.com --username ubnt --password ubnt --dry-run` -- test documentation generation in dry-run mode
  3. `python -m unifi_documenter export --format html --output ./test-output.html` -- test export functionality
  4. Verify the output files are created and contain expected content
- Test the CLI help system: `python -m unifi_documenter --help` and verify all commands are listed
- Always test authentication flows with invalid credentials to ensure proper error handling
- **CRITICAL**: Test network connectivity scenarios - the tool should gracefully handle network timeouts and connection failures
- Test different UniFi controller versions if multiple test environments are available
- Always run `flake8 .`, `black --check .`, and `mypy unifi_documenter/` before committing changes or the CI will fail

## Build and CI Information

- **CRITICAL**: Build and test times vary significantly based on network conditions when testing against UniFi controllers
- NEVER CANCEL builds or tests - they may take up to 15 minutes depending on network latency to UniFi controllers
- The CI pipeline (.github/workflows/test.yml) runs the full test suite including integration tests against demo controllers
- Integration tests can take 10-20 minutes to complete - DO NOT timeout early
- Set explicit timeout values of 30+ minutes for test commands to account for network dependencies

## Common Tasks

The following are outputs from frequently run commands. Reference them instead of viewing, searching, or running bash commands to save time.

### Repository Structure
```
.
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── pyproject.toml
├── .flake8
├── .github/
│   └── workflows/
│       ├── test.yml
│       └── release.yml
├── unifi_documenter/
│   ├── __init__.py
│   ├── cli.py
│   ├── controller.py
│   ├── documenter.py
│   ├── exporters/
│   │   ├── __init__.py
│   │   ├── html.py
│   │   ├── pdf.py
│   │   └── json.py
│   └── utils/
│       ├── __init__.py
│       ├── network.py
│       └── formatting.py
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   ├── test_controller.py
│   ├── test_documenter.py
│   └── fixtures/
│       └── sample_data.json
└── docs/
    ├── api.md
    ├── installation.md
    └── examples/
```

### Key Dependencies (requirements.txt)
```
requests>=2.28.0
click>=8.0.0
jinja2>=3.0.0
pydantic>=1.10.0
python-dotenv>=0.19.0
reportlab>=3.6.0  # for PDF generation
beautifulsoup4>=4.11.0  # for HTML parsing
PyYAML>=6.0  # for configuration files
```

### Development Dependencies (requirements-dev.txt)
```
pytest>=7.0.0
pytest-cov>=4.0.0
black>=22.0.0
flake8>=5.0.0
mypy>=0.991
pre-commit>=2.20.0
```

## Project-Specific Guidelines

- **UniFi API Patterns**: Always use the controller.py module for UniFi API interactions - it handles authentication, rate limiting, and error recovery
- **Authentication**: Use environment variables for sensitive credentials (UNIFI_USERNAME, UNIFI_PASSWORD, UNIFI_HOST)
- **Rate Limiting**: The UniFi controller API has rate limits - always use the built-in retry logic in controller.py
- **Data Validation**: All UniFi API responses should be validated using Pydantic models before processing
- **Error Handling**: Network operations should always include timeout handling and graceful degradation
- **Configuration**: Use .env files for local development settings, never commit credentials
- **Testing**: Mock UniFi API calls in unit tests, use integration tests only for critical end-to-end validation

## Environment Setup

- Create `.env` file for local development:
  ```
  UNIFI_HOST=demo.ubnt.com
  UNIFI_USERNAME=ubnt
  UNIFI_PASSWORD=ubnt
  UNIFI_PORT=443
  UNIFI_SSL_VERIFY=true
  LOG_LEVEL=INFO
  ```
- Demo UniFi controller credentials for testing:
  - Host: demo.ubnt.com
  - Username: ubnt
  - Password: ubnt
  - Port: 443 (HTTPS)
- **NEVER** commit real UniFi controller credentials to the repository

## Troubleshooting

- If `pip install -r requirements.txt` fails due to network issues, retry with `--timeout 300 --retries 3`
- If UniFi controller connection fails, verify SSL certificate settings and network connectivity
- If tests fail due to "Connection refused", ensure the demo controller is accessible or use mock tests only
- PDF generation may fail without proper system fonts - install `fonts-liberation` on Ubuntu/Debian
- If type checking fails, ensure all dependencies have type stubs: `pip install types-requests types-PyYAML`

## Performance Notes

- **Documentation Generation**: Large UniFi networks (100+ devices) may take 5-15 minutes to fully document
- **Export Operations**: PDF generation for complex networks can take 2-5 minutes
- **API Calls**: UniFi controller responses vary from 100ms to 5+ seconds depending on network complexity
- **Memory Usage**: Large network documentation may require 512MB+ RAM during processing
- NEVER CANCEL operations that appear slow - UniFi controllers can be legitimately slow to respond

## Security Considerations

- Always validate SSL certificates when connecting to UniFi controllers in production
- Use read-only UniFi accounts when possible to minimize security exposure
- Never log or display UniFi passwords in plain text
- Sanitize network topology data before including in exported documentation
- Be aware that generated documentation may contain sensitive network information