# Civ V macOS Coordinator

This project brings together the work needed to make Lekmod and Vox Populi
practical, dependable choices for Civilization V on macOS. **Wir Schaffen DLC**
provides one place to install a supported product, switch between products,
and restore the original game. This repository records the exact source
revisions that are developed and checked together.

## Philosophy

Keep each mod's identity and gameplay independent. Share the macOS compatibility
work that benefits both, make builds reproducible, and give users a clear path
back to their original installation. Compatibility claims should follow test
evidence, with remaining limitations stated plainly. Each component retains
its own history, releases, ownership, and licensing.

## Long-term goals

- Deliver validated native macOS Lekmod and Vox Populi packages through WSDLC.
- Check coordinated versions in CI, covering build compatibility and eventually
  installation, switching, UI, save/load, and multiplayer behavior.
- Expand mod and map compatibility through repeatable tests, while keeping
  updates and restoration reliable.

## How the repositories fit together

| Submodule | Functional responsibility |
| --- | --- |
| [`repos/compat`](repos/compat) | Shared macOS compatibility code, ABI contract, build tools, and binary validation |
| [`repos/lekmod`](repos/lekmod) | Lekmod gameplay, content, and its native GameCore |
| [`repos/vox-populi`](repos/vox-populi) | Vox Populi gameplay, content, and its native GameCore |
| [`repos/wsdlc`](repos/wsdlc) | WSDLC package verification, installation, switching, and restoration |

Git submodules pin exact commits. Lekmod and VP retain their own compatibility
lockfiles; the coordinator checks that both agree with its shared-code pin and
that WSDLC recognizes the same ABI. Updating a component does not automatically
advance the coordinator's tested combination.

## Getting started

The initial coordinator is a **local development snapshot**. Its shared
compatibility repository and VP revision must be published before the complete
workspace can be cloned from GitHub. With the existing repositories together
in a local directory, initialize a coordinator checkout with:

```sh
python3 scripts/bootstrap.py --local-root /path/to/existing/repositories
python3 scripts/check_workspace.py
```

The local bootstrap reads committed source and creates separate checkouts;
uncommitted work in the original repositories stays there. See
[the workspace guide](docs/workspace.md) for clone, update, testing, and
publication instructions.

The GameCore target is Aspyr's Intel macOS Civ V host, including execution
through Rosetta 2 on Apple Silicon. WSDLC itself has arm64 and amd64 builds.
Passing source checks does not certify gameplay, and this coordinator does
not launch or modify an installed game.
