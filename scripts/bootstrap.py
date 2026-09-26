#!/usr/bin/env python3
"""Initialize pinned submodules from GitHub or existing local repositories."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

from check_workspace import COMPONENTS, ROOT, check_workspace, git, pins, require_clean


def bootstrap(root: Path, local_root: Path | None = None) -> None:
    selected = pins(root)
    options = []
    # Check every destination and local source before changing any checkout.
    for name, commit in selected.items():
        target = root / 'repos' / name
        if target.is_symlink():
            raise ValueError(f'{name}: refusing a linked component checkout')
        if (target / '.git').exists():
            require_clean(target)
        elif target.exists() and any(target.iterdir()):
            raise ValueError(f'{name}: refusing to replace a nonempty directory')
        if local_root is not None:
            source = (local_root / COMPONENTS[name][1]).resolve()
            if not source.is_dir() or Path(git(source, 'rev-parse', '--show-toplevel')).resolve() != source:
                raise ValueError(f'{name}: local source is not its own Git repository: {source}')
            git(source, 'cat-file', '-e', commit + '^{commit}')
            options.extend(['-c', f'submodule.{name}.url={source}'])
    if local_root is not None:
        # File transport is enabled only for this explicit local-source command.
        options.extend(['-c', 'protocol.file.allow=always'])
    subprocess.run(['git', '-C', str(root), *options, 'submodule', 'update', '--init', '--checkout',
                    '--', *(f'repos/{name}' for name in COMPONENTS)], check=True)
    check_workspace(root)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-root', type=Path,
                        help='directory containing the existing four repositories; defaults to their GitHub URLs')
    args = parser.parse_args()
    try:
        bootstrap(ROOT, args.local_root)
    except (ValueError, KeyError, OSError, SyntaxError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'error: {error}\n')
    print('Pinned workspace initialized and checked. Original source worktrees were not modified.')


if __name__ == '__main__':
    main()
