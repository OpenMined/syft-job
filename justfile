# Guidelines for new commands
# - Start with a verb
# - Keep it short (max. 3 words in a command)
# - Group commands by context. Include group name in the command name.
# - Mark things private that are util functions with [private] or _var
# - Don't over-engineer, keep it simple.
# - Don't break existing commands
# - Run just --fmt --unstable after adding new commands

set dotenv-load := true

# ---------------------------------------------------------------------------------------------------------------------
# Private vars

_red := '\033[1;31m'
_cyan := '\033[1;36m'
_green := '\033[1;32m'
_yellow := '\033[1;33m'
_nc := '\033[0m'

# ---------------------------------------------------------------------------------------------------------------------
# Aliases

alias rj := run-jupyter

# ---------------------------------------------------------------------------------------------------------------------

@default:
    just --list

[group('utils')]
run-jupyter:
    #!/bin/bash
    uv venv
    uv sync
    uv run jupyter-lab


# ---------------------------------------------------------------------------------------------------------------------

# Build syft job wheel
[group('build')]
build:
    @echo "{{ _cyan }}Building syft-job wheel...{{ _nc }}"
    rm -rf dist/
    uv build
    @echo "{{ _green }}Build complete!{{ _nc }}"
    @echo "{{ _cyan }}To inspect the build:{{ _nc }}"
    @echo "{{ _cyan }}1. Go to the build directory and unzip the .tar.gz file to inspect the contents{{ _nc }}"
    @echo "{{ _cyan }}2. Inspect the .whl file with: uvx wheel unpack <path_to_whl_file>{{ _nc }}"
    @echo "{{ _cyan }}3. To upload to pypi, run: just publish-pypi{{ _nc }}"



# Build syft job wheel
[group('publish')]
publish-pypi:
    @echo "{{ _cyan }}Building syft-job wheel...{{ _nc }}"
    rm -rf dist/
    uv build
    uvx twine upload ./dist/*
    @echo "{{ _green }}Published to pypi!{{ _nc }}"
# ---------------------------------------------------------------------------------------------------------------------
