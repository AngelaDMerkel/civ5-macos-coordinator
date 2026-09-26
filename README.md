# Civ V macOS Coordinator

This repository keeps the source needed to build Lekmod, Vox Populi, and
Wir Schaffen DLC together. It records an exact version of each project so
developers can reproduce a build or return to an earlier set of versions.

## What each component does

| Repository | Purpose and value |
| --- | --- |
| [Lekmod](repos/lekmod) | Adds civilizations, balance changes, and multiplayer-focused gameplay. It contains Lekmod's game rules, content, and custom GameCore, including the macOS port. |
| [Vox Populi](repos/vox-populi) | Reworks Civ V's game systems and AI. It contains VP's own GameCore and content, with a separate macOS port so VP can develop independently of Lekmod. |
| [macOS compatibility](repos/compat) | Provides the platform functions, data layouts, build tools, and binary checks needed by both ports. A Mac compatibility fix can be shared by both mods instead of being maintained twice. |
| [Wir Schaffen DLC](repos/wsdlc) | Packages supported mods and maps as DLC for ordinary single-player and multiplayer games. Its GameCore installer checks packages, switches the active mod and matching content, and keeps one original GameCore backup for restoration. |

The **GameCore** is the library that runs Civ V's rules and AI. Aspyr's Mac
version needs a macOS library in place of the Windows DLL supplied by these
mods. Lekmod and VP each have their own implementation; only one GameCore can
be active in the game at a time.

## Shared work

The point of sharing this work is that a fix made for one Mac port can help
the others. Common compatibility fixes, build tools, and tests belong in the
shared repository, where both Lekmod and VP can use and improve them.

Gameplay changes stay with each mod. Installation work stays in WSDLC. Each
project keeps its own history, authorship, and license. Useful changes should
be documented and offered back to the upstream projects, so the benefit is
not limited to these Mac forks.

## How the coordinator works

The coordinator connects them using Git submodules. Each submodule points to a
specific commit. Its checks confirm that both mods use the selected compatibility
revision and that WSDLC expects the same binary interface. Component updates
are included by changing these pointers and checking the new combination.

## Development goals

- Produce complete macOS GameCore releases with matching DLC content, source
  revisions, and verified hashes.
- Extend test coverage for gameplay, saves, multiplayer, and large or unusually
  shaped maps.
- Add validated GameCore releases to WSDLC's download and update workflow.

## Working with the source

See the [developer guide](docs/workspace.md) for requirements, submodule setup,
build commands, tests, and the contribution workflow.
The GameCores target Aspyr's Intel macOS Steam release and run through Rosetta 2
on Apple Silicon. WSDLC has separate Apple Silicon and Intel executables.
