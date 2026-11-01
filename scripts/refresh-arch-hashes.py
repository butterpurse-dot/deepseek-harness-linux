#!/usr/bin/env python3
"""Refresh the Arch PKGBUILD version and AppImage hashes from a release."""

import re
import sys
from pathlib import Path


def main() -> None:
    version, x64, arm64 = sys.argv[1:4]
    pkgver = re.sub(r'-(alpha|beta|rc)\.', r'\1', version).replace('-', '')
    path = Path('packaging/arch/PKGBUILD')
    text = path.read_text()
    text = re.sub(r'^_version=.*$', f'_version={version}', text, flags=re.M)
    text = re.sub(r'^_tag=.*$', '_tag=v${_version}', text, flags=re.M)
    text = re.sub(r'^pkgver=.*$', f'pkgver={pkgver}', text, flags=re.M)
    text = re.sub(r"(sha256sums_x86_64=\(')[0-9a-f]{64}('\))", rf'\g<1>{x64}\g<2>', text)
    text = re.sub(r"(sha256sums_aarch64=\(')[0-9a-f]{64}('\))", rf'\g<1>{arm64}\g<2>', text)
    path.write_text(text)


if __name__ == '__main__':
    main()
