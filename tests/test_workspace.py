import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import bootstrap
import check_workspace as workspace


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.sources = self.base / 'sources'
        self.sources.mkdir()
        self.root = self.base / 'coordinator'
        self.init(self.root)
        self.commits = {}
        for name, (_, directory) in workspace.COMPONENTS.items():
            source = self.sources / directory
            self.init(source)
            if name == 'compat':
                self.write(source / 'abi/aspyr-bnw.json', json.dumps({'abi_id': 'fixture-abi'}))
            elif name in workspace.LOCKS:
                self.write(source / workspace.LOCKS[name], json.dumps({
                    'schema_version': 1, 'repository': workspace.repository_url('compat'),
                    'commit': self.commits['compat'], 'abi_id': 'fixture-abi',
                }))
            else:
                self.write(source / 'civ5_gamecore.py', "ABI = 'fixture-abi'\n")
            self.commits[name] = self.commit(source)
        self.write(self.root / '.gitmodules', ''.join(
            f'[submodule "{name}"]\n\tpath = repos/{name}\n\turl = {workspace.repository_url(name)}\n'
            for name in workspace.COMPONENTS))
        self.git(self.root, 'add', '.gitmodules')
        for name, commit in self.commits.items():
            self.git(self.root, 'update-index', '--add', '--cacheinfo', '160000', commit, f'repos/{name}')
        self.git(self.root, 'commit', '-qm', 'coordinator fixture')

    def git(self, root, *args):
        return workspace.git(root, *args)

    def init(self, path):
        path.mkdir()
        self.git(path, 'init', '-q', '-b', 'main')
        self.git(path, 'config', 'user.name', 'Coordinator test')
        self.git(path, 'config', 'user.email', 'test@example.invalid')

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)

    def commit(self, path):
        self.git(path, '-c', 'user.name=Coordinator test', '-c', 'user.email=test@example.invalid',
                 'add', '.')
        self.git(path, '-c', 'user.name=Coordinator test', '-c', 'user.email=test@example.invalid',
                 'commit', '-qm', 'fixture change')
        return self.git(path, 'rev-parse', 'HEAD')

    def start(self):
        bootstrap.bootstrap(self.root, self.sources)

    def change_lock(self, component, **values):
        source = self.root / 'repos' / component
        lock = source / workspace.LOCKS[component]
        data = json.loads(lock.read_text())
        data.update(values)
        lock.write_text(json.dumps(data))
        self.commit(source)
        self.git(self.root, 'add', f'repos/{component}')

    def test_fresh_clone_restores_exact_commits_despite_newer_and_dirty_sources(self):
        dirty = self.sources / 'civ5-macos-gamecore-compat/abi/aspyr-bnw.json'
        dirty.write_text('uncommitted compatibility experiment')
        newer = self.sources / 'Civ5ModDlcPacker'
        (newer / 'civ5_gamecore.py').write_text("ABI = 'future-incompatible-abi'\n")
        new_head = self.commit(newer)
        clone = self.base / 'fresh-clone'
        subprocess.run(['git', 'clone', '-q', str(self.root), str(clone)], check=True)
        bootstrap.bootstrap(clone, self.sources)
        self.assertEqual(workspace.check_workspace(clone), self.commits)
        self.assertEqual(dirty.read_text(), 'uncommitted compatibility experiment')
        self.assertEqual(self.git(newer, 'rev-parse', 'HEAD'), new_head)
        self.assertEqual(self.git(clone, 'status', '--porcelain'), '')

    def test_dirty_component_is_preserved_when_bootstrap_refuses_update(self):
        self.start()
        path = self.root / 'repos/wsdlc/civ5_gamecore.py'
        path.write_text('unfinished installer work')
        with self.assertRaisesRegex(ValueError, 'uncommitted or untracked'):
            self.start()
        self.assertEqual(path.read_text(), 'unfinished installer work')

    def test_untracked_work_is_preserved_when_bootstrap_refuses_update(self):
        self.start()
        path = self.root / 'repos/wsdlc/my-notes.txt'
        path.write_text('keep these notes')
        with self.assertRaisesRegex(ValueError, 'uncommitted or untracked'):
            self.start()
        self.assertEqual(path.read_text(), 'keep these notes')

    def test_different_compatibility_commit_in_consumer_is_rejected(self):
        self.start()
        self.change_lock('lekmod', commit='a' * 40)
        with self.assertRaisesRegex(ValueError, 'compatibility lock differs'):
            workspace.check_workspace(self.root)

    def test_different_consumer_abi_is_rejected(self):
        self.start()
        self.change_lock('vox-populi', abi_id='wrong-abi')
        with self.assertRaisesRegex(ValueError, 'ABI differs'):
            workspace.check_workspace(self.root)

    def test_different_installer_abi_is_rejected(self):
        self.start()
        source = self.root / 'repos/wsdlc'
        (source / 'civ5_gamecore.py').write_text("ABI = 'wrong-abi'\n")
        self.commit(source)
        self.git(self.root, 'add', 'repos/wsdlc')
        with self.assertRaisesRegex(ValueError, 'wsdlc: supported ABI differs'):
            workspace.check_workspace(self.root)

    def test_checkout_ahead_of_recorded_pin_is_rejected(self):
        self.start()
        source = self.root / 'repos/wsdlc'
        (source / 'new-file').write_text('unselected commit')
        self.commit(source)
        with self.assertRaisesRegex(ValueError, 'checkout does not match'):
            workspace.check_workspace(self.root)

    def test_unexpected_repository_url_is_rejected_before_cloning(self):
        self.git(self.root, 'config', '-f', '.gitmodules', 'submodule.compat.url', 'https://example.invalid/repo.git')
        with self.assertRaisesRegex(ValueError, 'unexpected submodule repository'):
            self.start()
        self.assertFalse((self.root / 'repos/compat/.git').exists())

    def test_symlink_to_original_checkout_is_rejected_before_updating(self):
        (self.root / 'repos').mkdir()
        (self.root / 'repos/compat').symlink_to(self.sources / 'civ5-macos-gamecore-compat', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'refusing a linked'):
            self.start()


if __name__ == '__main__':
    unittest.main()
