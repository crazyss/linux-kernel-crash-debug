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
commands = sys.stdin.read()
with open(os.environ['WRAPPER_RECORD'], 'a') as f:
    f.write(json.dumps({'argv': sys.argv[1:], 'stdin': commands}) + '\\n')
query = commands.splitlines()[1]
outputs = json.loads(os.environ.get('MOCK_CRASH_OUTPUTS', '{}'))
if query == os.environ.get('MOCK_CRASH_LARGE_COMMAND'):
    for n in range(6000):
        print(f'BUG: generated line {n:05d} ' + 'x' * 100)
else:
    print(outputs.get(query, 'test output'))
errors = json.loads(os.environ.get('MOCK_CRASH_ERRORS', '{}'))
if query in errors:
    print(errors[query], file=sys.stderr)
statuses = json.loads(os.environ.get('MOCK_CRASH_STATUSES', '{}'))
sys.exit(int(statuses.get(query, os.environ.get('MOCK_CRASH_STATUS', '0'))))
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
        self.env['MOCK_CRASH_OUTPUTS'] = json.dumps({'bt -f 42': 'partial stack evidence'})
        self.env['MOCK_CRASH_ERRORS'] = json.dumps({'bt -f 42': 'cannot read saved page'})
        result = self.invoke('backtrace', '42')
        self.assertEqual(result.returncode, 7)
        self.assertIn('partial stack evidence', result.stdout)
        self.assertIn('cannot read saved page', result.stderr)

    def test_macro_failures_are_not_hidden_by_later_success(self):
        cases = [(('triage',), 'sys'), (('triage',), 'log'),
                 (('flow-oom',), 'ps -G'), (('flow-deadlock',), 'ps -m'),
                 (('flow-lockdown',), 'foreach UN bt'),
                 (('dis-regs', 'panic', '42'), 'bt -f 42'),
                 (('flow-arm64', '48', '0x0', '0x0', '0x0'), 'log'),
                 (('check-poison', 'ffff'), 'rd ffff 64')]
        for args, failed in cases:
            with self.subTest(args=args, failed=failed):
                self.env['MOCK_CRASH_STATUSES'] = json.dumps({failed: 7})
                self.env['MOCK_CRASH_OUTPUTS'] = json.dumps({failed: 'partial diagnostic output'})
                result = self.invoke(*args)
                self.assertEqual(result.returncode, 7, result.stderr)
                self.assertIn('partial diagnostic output', result.stdout)
                self.assertIn('crash query failed', result.stderr)
                last = json.loads(self.record.read_text().splitlines()[-1])
                self.assertEqual(last['stdin'].splitlines()[1], failed)
                self.assertNotIn('corruption is not excluded', result.stdout)

    def test_successful_empty_results_are_not_query_failures(self):
        self.env['MOCK_CRASH_OUTPUTS'] = json.dumps(
            {'log': '', 'ps -m': '', 'foreach UN bt': ''})
        for args in [('triage',), ('flow-deadlock',), ('flow-lockdown',)]:
            with self.subTest(args=args):
                result = self.invoke(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn('crash query failed', result.stderr)

    def test_large_queries_are_consumed_before_display_filtering(self):
        for command, macro in [('log', ('triage',)),
                               ('kmem -i', ('flow-oom',)),
                               ('bt -a', ('triage',))]:
            with self.subTest(command=command):
                self.env['MOCK_CRASH_LARGE_COMMAND'] = command
                result = self.invoke(*macro)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertLess(len(result.stdout.splitlines()), 650)
                if command == 'bt -a':
                    self.assertIn('Output truncated', result.stdout)
                    self.assertIn('generated line 05999', result.stdout)

    def test_oom_ranks_rss_and_allocated_object_bytes(self):
        self.env['MOCK_CRASH_OUTPUTS'] = json.dumps({
            'ps -G': ('PID PPID CPU TASK ST %MEM VSZ RSS COMM\n'
                      '30 1 0 ffff1000 UN 90.0 999999 20 large-vsz\n'
                      '> 20 1 0 ffff2000 RU 0.1 200 150 largest-rss\n'
                      '10 1 0 ffff3000 IN 0.2 1000 80 middle-rss'),
            'kmem -s': ('CACHE OBJSIZE ALLOCATED TOTAL SLABS SSIZE NAME\n'
                        'ffff1000 8 100 99999 1 4k most-capacity\n'
                        'ffff2000 1024 3 4 1 4k largest-object-bytes\n'
                        'ffff3000 256 8 100 1 4k middle-object-bytes')})
        result = self.invoke('flow-oom')
        self.assertEqual(result.returncode, 0, result.stderr)
        for names in [('largest-rss', 'middle-rss', 'large-vsz'),
                      ('largest-object-bytes', 'middle-object-bytes', 'most-capacity')]:
            positions = [result.stdout.index(name) for name in names]
            self.assertEqual(positions, sorted(positions))
        self.assertIn('3072', result.stdout)
        self.assertIn('2048', result.stdout)

    def test_poison_checks_only_complete_data_words(self):
        self.env['MOCK_CRASH_OUTPUTS'] = json.dumps({
            'rd ffff 64': ('ffffabcd6b6b6b6b: 0000000000000001 0000000000000002  6b6b6b6b\n'
                           'ffff000000000010: 12346b6b6b6b5678 0000000000000100  ....')})
        result = self.invoke('check-poison', 'ffff')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('(candidate only;', result.stdout)
        self.env['MOCK_CRASH_OUTPUTS'] = json.dumps({
            'rd ffff 64': 'ffff000000000000: 6b6b6b6b6b6b6b6b 5a5a5a5a5a5a5a5a  ........'})
        result = self.invoke('check-poison', 'ffff')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count('(candidate only;'), 2)

    def test_arm64_uses_explicit_hex_relocation_before_inputs(self):
        result = self.invoke('flow-arm64', '48', '80000000', 'ffffffc000000000', '100000')
        self.assertEqual(result.returncode, 0, result.stderr)
        for call in map(json.loads, self.record.read_text().splitlines()):
            argv = call['argv']
            self.assertIn('--kaslr=0x100000', argv)
            self.assertFalse(any(arg.startswith('kaslr=') for arg in argv))
            self.assertLess(argv.index('--kaslr=0x100000'),
                            argv.index(str((self.root/'vmlinux').resolve())))

    def test_private_query_files_are_cleaned_on_success_and_failure(self):
        scratch = self.root/'scratch'
        scratch.mkdir()
        self.env['TMPDIR'] = str(scratch)
        for status in ('0', '7'):
            with self.subTest(status=status):
                self.env['MOCK_CRASH_STATUS'] = status
                self.assertEqual(self.invoke('backtrace', '42').returncode, int(status))
                self.assertEqual(list(scratch.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
