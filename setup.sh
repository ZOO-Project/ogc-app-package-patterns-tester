#!/bin/bash

# Installation and validation script for the OGC API Processes patterns tester
# This script configures the development environment and verifies installation

set -e  # Stop on error

# Colors for display
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python
check_python() {
    print_info "Checking Python..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 8 ]]; then
        print_error "Python 3.8+ required, detected version: $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION detected"
}

# Create virtual environment
setup_venv() {
    print_info "Setting up virtual environment..."
    
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Existing virtual environment detected"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Update pip
    pip install --upgrade pip setuptools wheel
    print_success "Base tools updated"
}

# Install dependencies
install_dependencies() {
    print_info "Installing dependencies..."
    
    # Install base dependencies
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
        print_success "Base dependencies installed"
    fi
    
    # Install package in development mode
    pip install -e .
    print_success "Package installed in development mode"
    
    # Install optional development dependencies
    pip install pytest black flake8 mypy || print_warning "Some development tools could not be installed"
}

# Validate installation
validate_installation() {
    print_info "Validating installation..."
    
    # Check package import
    python3 -c "from ogc_patterns_tester import PatternsManager, ServerConfig; print('✓ Package import successful')" || {
        print_error "Unable to import package"
        return 1
    }
    
    # Check CLI
    python3 -m ogc_patterns_tester --help > /dev/null || {
        print_error "CLI interface not functional"
        return 1
    }
    
    # Check patterns
    if [[ -d "data/patterns" ]]; then
        PATTERN_COUNT=$(ls data/patterns/pattern-*.json 2>/dev/null | wc -l)
        if [[ $PATTERN_COUNT -gt 0 ]]; then
            print_success "$PATTERN_COUNT patterns detected"
        else
            print_warning "No patterns detected"
        fi
    fi
    
    # Test JSON validation of patterns
    python3 -c "
import json
from pathlib import Path

patterns_dir = Path('data/patterns')
if patterns_dir.exists():
    valid_patterns = 0
    for pattern_file in patterns_dir.glob('pattern-*.json'):
        try:
            with open(pattern_file) as f:
                json.load(f)
            valid_patterns += 1
        except json.JSONDecodeError:
            print(f'JSON error in {pattern_file}')
    print(f'✓ {valid_patterns} patterns with valid JSON')
" || print_warning "Errors in pattern validation"
    
    print_success "Installation validated successfully"
}

# Display usage instructions
show_usage() {
    print_info "Usage instructions:"
    echo
    echo "1. Activate virtual environment:"
    echo "   source venv/bin/activate"
    echo
    echo "2. Run tests (requires an OGC API Processes server):"
    echo "   python -m ogc_patterns_tester --server-url http://localhost:5000 run-all"
    echo
    echo "3. Or use Make for common tasks:"
    echo "   make help              # View all commands"
    echo "   make run-all-patterns  # Execute all patterns"
    echo "   make list-patterns     # List patterns"
    echo
    echo "4. To configure a local server, see:"
    echo "   make setup-local-server"
    echo
    echo "5. Complete documentation in README.md"
}

# Quick test without server
quick_test() {
    print_info "Quick test of basic functionality..."
    
    python3 -c "
from ogc_patterns_tester import ServerConfig, PatternsManager
from pathlib import Path

# Configuration test
config = ServerConfig(base_url='http://test.example.com')
print('✓ Server configuration creation')

# Manager test (without real connection)
manager = PatternsManager(config, patterns_dir='data/patterns')
print('✓ Patterns manager creation')

# Pattern loading test
if Path('data/patterns').exists():
    patterns = list(Path('data/patterns').glob('pattern-*.json'))
    if patterns:
        pattern_id = patterns[0].stem
        config = manager.load_pattern_config(pattern_id)
        if config:
            print(f'✓ Configuration loading for {pattern_id}')
        else:
            print('✗ Configuration loading failed')
    else:
        print('⚠ No patterns found for testing')

print('✓ Basic tests successful')
" || {
        print_error "Basic tests failed"
        return 1
    }
    
    print_success "Quick tests successful"
}

# Main menu
main() {
    echo
    echo "=================================================="
    echo "   OGC API Processes Patterns Tester - Setup    "
    echo "=================================================="
    echo
    
    # Preliminary checks
    check_python
    
    # Installation options
    if [[ "$1" == "--quick" ]]; then
        print_info "Quick installation..."
        setup_venv
        install_dependencies
        validate_installation
        quick_test
    elif [[ "$1" == "--test-only" ]]; then
        print_info "Tests only..."
        source venv/bin/activate 2>/dev/null || {
            print_error "Virtual environment not found. Run installation first."
            exit 1
        }
        validate_installation
        quick_test
    elif [[ "$1" == "--help" ]]; then
        echo "Usage: $0 [--quick|--test-only|--help]"
        echo
        echo "Options:"
        echo "  --quick      Complete quick installation"
        echo "  --test-only  Validation tests only"
        echo "  --help       Display this help"
        echo
        echo "No option: complete interactive installation"
        exit 0
    else
        # Interactive installation
        print_info "Complete interactive installation..."
        
        setup_venv
        install_dependencies
        validate_installation
        quick_test
        
        echo
        print_success "Installation completed successfully!"
        echo
        show_usage
    fi
}

# Error handling
trap 'print_error "Script interrupted"; exit 1' INT TERM

# Entry point
main "$@"