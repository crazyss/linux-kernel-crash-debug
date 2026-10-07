"""Boundary tests use fake crash/timeout executables; no kernel is accessed."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/agent-crash.sh'


@unittest.skipIf(os.geteuid() == 0, 'wrapper intentionally refuses root')
class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('vmlinux', 'vmcore'):
            (self.root / name).touch()
        self.record = self.root / 'calls.jsonl'
        self.env = dict(os.environ, PATH=f'{self.root}:{os.environ["PATH"]}',
                        WRAPPER_RECORD=str(self.record))
        programs = {
            'crash': '''#!/usr/bin/env python3
import json, os, sys
with open(os.environ['WRAPPER_RECORD'], 'a') as f:
    f.write(json.dumps({'argv': sys.argv[1:], 'stdin': sys.stdin.read()}) + '\\n')
print('test output')
sys.exit(int(os.environ.get('MOCK_CRASH_STATUS', '0')))
''',
            'timeout': '#!/bin/sh\nshift\nexec "$@"\n',
            # Portable test shim; production requires GNU realpath on Linux.
            'realpath': '''#!/usr/bin/env python3
import os, sys
print(os.path.realpath(sys.argv[-1]))
''',
        }
        for name, source in programs.items():
            p = self.root / name
            p.write_text(source)
            p.chmod(0o700)

    def invoke(self, *args, paths=True):
        prefix = ['-k', str(self.root/'vmlinux'), '-c', str(self.root/'vmcore')] if paths else []
        return subprocess.run(['bash', str(SCRIPT), *prefix, *args], cwd=self.root,
                              env=self.env, capture_output=True, text=True, timeout=5)

    def test_rejected_inputs_never_start_crash(self):
        cases = [('run', 'sys'), ('run', '!id'), ('triage', 'extra'),
                 ('dis-regs', 'panic\n!id', '1'), ('dis-regs', 'panic', '1\\n!id'),
                 ('disassemble', 'panic;id'), ('disassemble', 'panic | id'),
                 ('disassemble', 'panic>file'), ('disassemble', '$rip'),
                 ('check-poison', 'ffff\\n!id'), ('check-poison', 'ffff\nquit'),
                 ('read-memory', '-r'), ('read-memory', 'ffff', '257'),
                 ('read-memory', 'ffff', '0'), ('read-memory', 'ffff', '01'),
                 ('backtrace', '-1'), ('backtrace', '1\r!id'),
                 ('flow-arm64', '48', '0x0', '0x0', '0x0\n!id')]
        for args in cases:
            with self.subTest(args=args):
                self.assertNotEqual(self.invoke(*args).returncode, 0)
                self.assertFalse(self.record.exists())

    def test_missing_and_nonregular_inputs(self):
        for args in [('-k',), ('-k', str(self.root/'vmlinux'), 'triage'),
                     ('-k', str(self.root/'vmlinux'), '-c', '/dev/null', 'triage')]:
            with self.subTest(args=args):
                self.assertNotEqual(self.invoke(*args, paths=False).returncode, 0)
                self.assertFalse(self.record.exists())

    def test_gdb_startup_is_rejected(self):
        (self.root/'.gdbinit').write_text('shell id\n')
        self.assertNotEqual(self.invoke('triage').returncode, 0)
        self.assertFalse(self.record.exists())

    def test_valid_macros_and_primitives(self):
        for args in [('triage',), ('flow-oom',), ('flow-deadlock',), ('flow-lockdown',),
                     ('dis-regs', 'panic.isra.0', '42'), ('check-poison', 'ffff'),
                     ('read-memory', '0xffff', '256'), ('backtrace', '42'),
                     ('disassemble', 'panic'), ('flow-arm64', '48', '0x0', '0x0', '0x0')]:
            with self.subTest(args=args):
                result = self.invoke(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
        for call in map(json.loads, self.record.read_text().splitlines()):
            self.assertIn('--no_crashrc', call['argv'])
            self.assertIn(str((self.root/'vmcore').resolve()), call['argv'])
            lines = call['stdin'].splitlines()
            self.assertEqual(len(lines), 3)
            self.assertEqual(lines[0], 'set scroll off')
            self.assertEqual(lines[-1], 'quit')
            self.assertFalse(any(c in lines[1] for c in '!;|<>\\\r'))

    def test_crash_failure_is_visible(self):
        self.env['MOCK_CRASH_STATUS'] = '7'
        self.assertEqual(self.invoke('backtrace', '42').returncode, 7)


if __name__ == '__main__':
    unittest.main()
