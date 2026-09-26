#!/usr/bin/env python3
"""Check exact submodule revisions and the shared GameCore ABI contract."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = {
    'compat': ('civ5-macos-gamecore-compat', 'civ5-macos-gamecore-compat'),
    'lekmod': ('Lekmod', 'Lekmod'),
    'vox-populi': ('Community-Patch-DLL-macOS', 'Community-Patch-DLL-macOS'),
    'wsdlc': ('Wir-Schaffen-DLC', 'Civ5ModDlcPacker'),
}
LOCKS = {
    'lekmod': 'LEKMOD_DLL/macos/compat.lock.json',
    'vox-populi': 'macos/compat.lock.json',
}


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def repository_url(name: str) -> str:
    return f'https://github.com/AngelaDMerkel/{COMPONENTS[name][0]}.git'


def pins(root: Path) -> dict[str, str]:
    if Path(git(root, 'rev-parse', '--show-toplevel')).resolve() != root.resolve():
        raise ValueError('the workspace must be its own Git repository')
    paths = git(root, 'config', '-f', '.gitmodules', '--get-regexp', r'^submodule\..*\.path$').splitlines()
    expected_paths = {f'submodule.{name}.path repos/{name}' for name in COMPONENTS}
    if {' '.join(line.split()) for line in paths} != expected_paths:
        raise ValueError('.gitmodules must contain exactly the four coordinator components')
    result = {}
    for name in COMPONENTS:
        path = f'repos/{name}'
        if git(root, 'config', '-f', '.gitmodules', '--get', f'submodule.{name}.url') != repository_url(name):
            raise ValueError(f'{name}: unexpected submodule repository URL')
        entry = git(root, 'ls-files', '--stage', '--', path).split()
        if len(entry) != 4 or entry[0] != '160000' or entry[2:] != ['0', path] or not re.fullmatch('[0-9a-f]{40}', entry[1]):
            raise ValueError(f'{name}: expected one exact, conflict-free Git submodule pin')
        result[name] = entry[1]
    return result


def require_clean(path: Path) -> None:
    if path.is_symlink() or (path / '.git').is_symlink():
        raise ValueError(f'{path.name}: refusing a linked component checkout')
    if Path(git(path, 'rev-parse', '--show-toplevel')).resolve() != path.resolve():
        raise ValueError(f'{path.name}: submodule is not initialized')
    if git(path, 'status', '--porcelain', '--untracked-files=all', '--ignore-submodules=none'):
        raise ValueError(f'{path.name}: submodule has uncommitted or untracked work; preserve it before updating')


def check_workspace(root: Path = ROOT) -> dict[str, str]:
    selected = pins(root)
    for name, commit in selected.items():
        path = root / 'repos' / name
        if not (path / '.git').exists():
            raise ValueError(f'{name}: submodule is not initialized; run scripts/bootstrap.py')
        require_clean(path)
        if git(path, 'rev-parse', 'HEAD') != commit:
            raise ValueError(f'{name}: checkout does not match the coordinator pin')
    contract = json.loads((root / 'repos/compat/abi/aspyr-bnw.json').read_text())
    abi = contract['abi_id']
    for name, filename in LOCKS.items():
        lock = json.loads((root / 'repos' / name / filename).read_text())
        if lock.get('schema_version') != 1 or lock.get('repository') != repository_url('compat'):
            raise ValueError(f'{name}: unsupported compatibility lock or repository')
        if lock.get('commit') != selected['compat']:
            raise ValueError(f'{name}: compatibility lock differs from the coordinator pin')
        if lock.get('abi_id') != abi:
            raise ValueError(f'{name}: compatibility ABI differs from the shared contract')
    # Read WSDLC's declaration without executing installer code.
    module = ast.parse((root / 'repos/wsdlc/civ5_gamecore.py').read_text())
    declarations = [node.value for node in module.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'ABI' for target in node.targets)]
    if len(declarations) != 1 or ast.literal_eval(declarations[0]) != abi:
        raise ValueError('wsdlc: supported ABI differs from the shared contract')
    return selected


def main() -> None:
    try:
        for name, commit in check_workspace().items():
            print(f'{name:12} {commit}')
        print('All four pins, both compatibility locks, and the installer ABI agree.')
    except (ValueError, KeyError, OSError, SyntaxError, subprocess.CalledProcessError) as error:
        sys.exit(f'error: {error}')


if __name__ == '__main__':
    main()
