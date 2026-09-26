# Developer guide

## Requirements

Use Git and Python 3.10 or newer. Building the GameCores also requires macOS
and Xcode Command Line Tools. Apple Silicon Macs need Rosetta 2 to run the
Intel binaries used by the game and some tests.

## Clone and initialize

```sh
git clone https://github.com/AngelaDMerkel/civ5-macos-coordinator.git
cd civ5-macos-coordinator
python3 scripts/bootstrap.py
python3 scripts/check_workspace.py
```

The bootstrap fetches the recorded commits from the repositories listed in
[.gitmodules](../.gitmodules). It refuses to update component checkouts
containing edits or untracked files. Commit or stash those changes before
updating submodules.

**Known checkout issue:** `repos/vox-populi` pins commit
`655df2a0253a59c6858535b238c7a095958155ed`, which is unavailable from its
configured remote. Full initialization and CI checkout are blocked on that
commit. Replacing it with a branch tip would bypass the recorded version.

## Check the selected versions

```sh
export PYTHONDONTWRITEBYTECODE=1
python3 scripts/check_workspace.py
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s repos/compat/tests -v
python3 -m unittest discover -s repos/wsdlc/tests -v
```

The workspace check prints all four commit IDs and confirms that:

- Each checkout matches its recorded commit and has no uncommitted source changes.
- Lekmod and VP both use the compatibility revision selected by the coordinator.
- Both mods and WSDLC agree on the GameCore's binary interface, or ABI.

Ignored build outputs and caches are allowed. The compatibility bootstrap
checks its own cached source separately, including ignored files.

These checks catch version and interface mismatches. Gameplay, UI, save/load,
and multiplayer testing still need to be done in the game.

## Build the GameCores

Point both builds at the compatibility source already in the workspace:

```sh
export CIV5_COMPAT_SOURCE="$PWD/repos/compat"
bash repos/lekmod/LEKMOD_DLL/macos/build-macos.sh --jobs 4
bash repos/vox-populi/macos/build-macos.sh --jobs 4
```

Each build writes its GameCore library and build report to that mod's
`build/macos` directory. It also checks the binary's architecture, exported
functions, and other properties required by Aspyr's game. The scripts do not
install the result or start Civ V.

A playable package also needs the mod's matching DLC content. In the checked-out
workspace, see `repos/lekmod/LEKMOD_DLL/macos/README.md` for Lekmod packaging
instructions and `repos/vox-populi/macos/package-macos.sh` for VP packaging.
VP packaging requires a prepared DLC directory; raw SQL and modinfo sources
are not an installable payload.

The coordinator's GitHub Actions workflow runs the version checks and the
coordinator, shared compatibility, and WSDLC tests. A manual workflow run can
also build both GameCores and retain the outputs for seven days. It needs
all pinned commits to be available on GitHub. Each component keeps its own
release process; WSDLC's automatic releases are separate from these checks.

## Include a component update

1. Commit, test, and push the change in the component's own repository.
2. Fetch that repository in the coordinator and select the commit to include.
   For example: `git -C repos/lekmod fetch origin`, followed by
   `git -C repos/lekmod checkout --detach FULL_COMMIT`.
3. Stage the new pointer with `git add repos/lekmod` and run the checks above.
4. Commit and push the coordinator update, explaining which versions changed
   and what was tested.

For a shared compatibility update, change and commit both mods' lockfiles,
then update all three coordinator pointers together. The checker reads staged
pointers, so you can check the combination before committing it.

Submodules normally open at a detached commit. Create a branch before making
changes inside one, and save local work before switching versions. Use
`git submodule update --init` to restore the recorded versions. Adding
`--remote` instead follows branch tips and changes the selected combination.
