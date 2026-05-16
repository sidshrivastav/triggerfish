{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Python 3.13 (latest stable)
    python313
    python313Packages.pip
    python313Packages.setuptools
    python313Packages.wheel

    # Development tools
    python313Packages.pytest
    python313Packages.black
    python313Packages.mypy
    python313Packages.pylint

    # LSP related dependencies
    universal-ctags
    git
  ];

  shellHook = ''
    echo "Python development environment"
    echo "Python version: $(python --version)"
    echo "pip version: $(pip --version)"
    echo ""
    echo "Available tools:"
    echo "  - pytest (testing)"
    echo "  - black (formatting)"
    echo "  - mypy (type checking)"
    echo "  - pylint (linting)"
    echo "  - ctags (code indexing)"
    echo ""

    # Create virtual environment if it doesn't exist
    if [ ! -d .venv ]; then
      echo "Creating virtual environment..."
      python -m venv .venv
    fi

    # Activate virtual environment
    source .venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip > /dev/null 2>&1

    echo "Virtual environment activated!"
    echo "Run 'pip install -e .' to install the project in development mode"
  '';
}
