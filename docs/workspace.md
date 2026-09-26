# Working with the coordinator

## Initial state

The initial snapshot records the committed heads inspected on 26 September
2026. The Git submodule entries are the authoritative revision list; run
`python3 scripts/check_workspace.py` to display and verify it.

The original Lekmod checkout contains ongoing uncommitted playtest work.
Those edits remain in that checkout and are not part of this committed
snapshot. The coordinator has separate component checkouts and never borrows
files from a mutable source worktree during builds.

This is a source-coordination baseline, not a qualified combined release.
The shared compatibility repository currently has no published remote, and
the selected VP commit was not available through GitHub's public API when
this snapshot was created. WSDLC's native GameCore download catalog is still
empty. VP still needs a prepared DLC payload and runtime qualification.

## Initialize from local repositories

Requirements: Git and Python 3.10 or newer. Native checks and builds also need
macOS, Xcode Command Line Tools, and Intel execution support (Rosetta 2 on
Apple Silicon).

The local source directory must contain:

| Local directory | Coordinator path |
| --- | --- |
| `civ5-macos-gamecore-compat` | `repos/compat` |
| `Lekmod` | `repos/lekmod` |
| `Community-Patch-DLL-macOS` | `repos/vox-populi` |
| `Civ5ModDlcPacker` | `repos/wsdlc` |

For another local workspace:

```sh
git clone /path/to/civ5-macos-coordinator civ5-workspace
cd civ5-workspace
python3 scripts/bootstrap.py --local-root /path/to/existing/repositories
python3 scripts/check_workspace.py
```

The bootstrap checks the pinned commits exist before initialization, refuses
dirty component checkouts, and uses the Git-recorded commits. Local paths are
overrides in the clone configuration; `.gitmodules` retains the intended
GitHub URLs. No global Git configuration is changed.

After the coordinator and every pinned component commit are published:

```sh
git clone --recurse-submodules https://github.com/AngelaDMerkel/civ5-macos-coordinator.git
cd civ5-macos-coordinator
python3 scripts/check_workspace.py
```

To move an existing locally initialized clone to the published sources, run
`git submodule sync --recursive` and then `python3 scripts/bootstrap.py`.

## Check and build the selected combination

```sh
export PYTHONDONTWRITEBYTECODE=1
python3 scripts/check_workspace.py
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s repos/compat/tests -v
python3 -m unittest discover -s repos/wsdlc/tests -v
```

The checks require clean component source and exact Git pins. Normal ignored
build/cache outputs are permitted; the shared bootstrap separately validates
its compatibility cache, including ignored files. Both consumer locks must
match the selected shared commit and ABI. WSDLC must declare that same ABI.
These are integration checks for source and contracts, not gameplay tests.

To build either GameCore from the shared revision already in this workspace:

```sh
export CIV5_COMPAT_SOURCE="$PWD/repos/compat"
bash repos/lekmod/LEKMOD_DLL/macos/build-macos.sh --jobs 4
bash repos/vox-populi/macos/build-macos.sh --jobs 4
```

Each product's build script runs its ABI validator and writes the binary and
build report to that product's `build/macos` directory. Building does not
prepare a validated VP DLC payload or launch/install the game.

Once published, the coordinator's GitHub Actions workflow runs the pin checks,
coordinator tests, shared ABI tests, and WSDLC tests. A manual workflow run
can additionally build both GameCores. Those jobs keep CI artifacts for seven
days; they do not publish product releases. Existing per-product CI and WSDLC
automatic releases continue independently.

## Advance a component

1. Commit and test changes in the component's own repository. Publish that
   commit before publishing a coordinator that references it.
2. In the coordinator, fetch the relevant component and check out its exact
   commit: `git -C repos/lekmod fetch origin`, then
   `git -C repos/lekmod checkout --detach FULL_COMMIT` (for example).
3. Stage the pointer with `git add repos/lekmod`, run the checks above, and
   commit the pointer update with an explanation of what was checked together.
4. Push the coordinator commit after its component commits are accessible.

When changing shared compatibility code, update and commit both consumer
lockfiles, then advance all three coordinator pointers together. Pins are
read from the Git index so a staged update can be checked before committing.
Avoid `git submodule update --remote`: following branch tips would bypass the
selected combination. Create a branch before developing inside a detached
submodule checkout, and preserve local edits before switching revisions.

## Publication and qualification

Before publishing this initial coordinator, publish the shared compatibility
repository and the selected VP history under the configured personal account.
Verify all four pinned commits are fetchable from the URLs in `.gitmodules`,
then publish the coordinator and run its CI from a fresh GitHub checkout.
Source-publication permission does not imply permission to install or launch
Civilization V. Runtime, UI, save/load, and multiplayer qualification remain
separate, explicit activities. Tag a combined release only when its stated
qualification gates have actually passed.
