default:
    @just --list

# Run tests on the current interpreter; extra arguments go to tox.
test *ARGS:
    uvx tox -e py {{ ARGS }}

# Run all linters and formatters.
check:
    uvx prek run --all-files

# Cut a release: `just release 0.15.0`, then `just push-release 0.15.0`.
release version:
    #!/usr/bin/env bash
    set -euo pipefail
    test -z "$(git status --porcelain)" || { echo "Working tree is not clean" >&2; exit 1; }
    grep -qx '## \[Unreleased\]' CHANGELOG.md
    previous=$(sed -n 's/^version = "\(.*\)"$/\1/p' pyproject.toml | head -1)
    sed -i '0,/^version = ".*"$/s//version = "{{ version }}"/' pyproject.toml
    sed -i "s/^## \[Unreleased\]$/## [Unreleased]\n\n## [{{ version }}] - $(date +%F)/" CHANGELOG.md
    sed -i "s|^\[Unreleased\]: \(.*\)/compare/.*\.\.\.HEAD$|[Unreleased]: \1/compare/v{{ version }}...HEAD\n[{{ version }}]: \1/compare/v$previous...v{{ version }}|" CHANGELOG.md
    git commit --quiet --all --message "chore: Release {{ version }}"
    git tag --sign --message "Release {{ version }}" v{{ version }}
    echo "Tagged v{{ version }}; publish with: just push-release {{ version }}"

# Push the release commit and its tag; the tag triggers the publishing workflow.
push-release version:
    git push origin master v{{ version }}
