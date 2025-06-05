#!/usr/bin/env python3
"""
Generate requirements.txt from pyproject.toml for deployment platforms.
This is useful for platforms like Streamlit Cloud that require requirements.txt.
"""

import sys
from pathlib import Path

import tomli


def generate_requirements():
    """Generate requirements.txt from pyproject.toml dependencies."""

    # Read pyproject.toml
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        sys.exit(1)

    with open(pyproject_path, "rb") as f:
        pyproject = tomli.load(f)

    # Extract main dependencies
    dependencies = pyproject.get("project", {}).get("dependencies", [])

    if not dependencies:
        print("Error: No dependencies found in pyproject.toml")
        sys.exit(1)

    # Write requirements.txt
    with open("requirements.txt", "w") as f:
        f.write("# Generated from pyproject.toml\n")
        f.write("# To regenerate: python scripts/generate_requirements.py\n\n")
        for dep in sorted(dependencies):
            f.write(f"{dep}\n")

    print(f"✅ Generated requirements.txt with {len(dependencies)} dependencies")
    print("📋 Contents:")
    for dep in sorted(dependencies):
        print(f"  {dep}")


if __name__ == "__main__":
    try:
        import tomli
    except ImportError:
        print("Error: tomli package required. Install with: pip install tomli")
        sys.exit(1)

    generate_requirements()
