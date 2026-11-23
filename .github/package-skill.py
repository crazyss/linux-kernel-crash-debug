"""Build the two OpenClaw-compatible release archives from the portable source."""

import argparse
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


NAME = 'linux-kernel-crash-debug'
SOURCE = Path(__file__).resolve().parents[1] / 'skills' / NAME
MANIFESTS = ('SKILL.md', 'SKILL_CN.md')
RUNTIME_FILES = (*MANIFESTS, 'scripts/agent-crash.sh', *(
    f'references/{name}.md' for name in (
        'advanced-commands', 'agentic-heuristics', 'arm64-crash-params',
        'arm64-lock-analysis', 'case-studies', 'debug-tools-guide',
        'evidence-first-workflow', 'kdump-setup-guide', 'sources', 'vmcore-format',
    )
))
OPENCLAW_METADATA = f'''metadata:
  openclaw:
    requires:
      bins:
        - crash
    os:
      - linux
    homepage: https://github.com/crazyss/{NAME}
'''


def render_manifest(filename):
    original = (SOURCE / filename).read_text(encoding='utf-8')
    prefix, header, body = original.split('---\n', 2)
    version_match = re.search(r'^metadata:\n  version: "(\d+\.\d+\.\d+)"\n\Z', header, re.M)
    if prefix or not header.startswith(f'name: {NAME}\n') or version_match is None:
        raise SystemExit(f'{filename}: expected the portable name and version metadata')

    version = version_match[1]
    fields = header[:version_match.start()]
    fields = fields.replace(f'name: {NAME}\n', f'name: {NAME}\nversion: {version}\n', 1)
    return version, f'---\n{fields}{OPENCLAW_METADATA}---\n{body}'.encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output_dir', type=Path)
    parser.add_argument('--tag', help='Require that both source manifests match this tag')
    args = parser.parse_args()

    runtime_paths = {p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob('*')
                     if not p.is_dir() or p.is_symlink()}
    expected = set(RUNTIME_FILES)
    if runtime_paths != expected:
        raise SystemExit(f'Runtime files differ: missing {expected - runtime_paths}, extra {runtime_paths - expected}')
    for name in RUNTIME_FILES:
        path = SOURCE / name
        if not path.is_file() or path.is_symlink():
            raise SystemExit(f'Expected a regular file: {path}')

    version, english = render_manifest(MANIFESTS[0])
    version_cn, chinese = render_manifest(MANIFESTS[1])
    tag = f'v{version}'
    if version != version_cn or (args.tag is not None and args.tag != tag):
        raise SystemExit(f'Manifest versions or release tag differ: {version}, {version_cn}, {args.tag}')

    files = dict(zip(MANIFESTS, (english, chinese)))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for filename, prefix in ((f'{NAME}.skill', ''), (f'{NAME}-{tag}.zip', f'{NAME}-{tag}/')):
        destination = args.output_dir / filename
        with ZipFile(destination, 'w', compression=ZIP_DEFLATED) as archive:
            for name in RUNTIME_FILES:
                path = SOURCE / name
                if name in files:
                    entry = ZipInfo.from_file(path, prefix + name)
                    archive.writestr(entry, files[name], compress_type=ZIP_DEFLATED)
                else:
                    archive.write(path, prefix + name)
        print(destination)


if __name__ == '__main__':
    main()
