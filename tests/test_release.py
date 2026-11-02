"""Release configuration checks; they do not simulate a successful hosted CI run."""
from pathlib import Path
import re
import tomllib
from unittest.mock import patch

import yaml

from tools.public_audit import scan_text

ROOT=Path(__file__).resolve().parents[1]


def test_ci_pins_actions_and_declares_real_platforms():
    workflow=yaml.load((ROOT/'.github/workflows/ci.yml').read_text(),Loader=yaml.BaseLoader)
    assert set(workflow['on'])=={'push','pull_request','workflow_dispatch'}
    assert workflow['permissions']=={'contents':'read'}
    job=workflow['jobs']['compatibility']
    assert {r['os'] for r in job['strategy']['matrix']['include']}=={'ubuntu-24.04','windows-latest','macos-15'}
    assert int(job['timeout-minutes'])<=40
    assert all(re.fullmatch(r'actions/[a-z-]+@[0-9a-f]{40}',step['uses']) for step in job['steps'] if 'uses' in step)
    assert workflow['jobs']['compatibility']['steps'][0]['with']['persist-credentials']=='false'
    mac=next(s for s in job['steps'] if s.get('name','').startswith('Homebrew'))
    assert 'uname -m' in mac['run'] and 'arm64' in mac['run'] and 'brew --prefix llvm@18' in mac['run']
    assert 'M4' not in mac['name']


def test_release_version_license_and_runtime_dependencies():
    metadata=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']
    from aion import __version__
    assert metadata['version']==__version__=='0.6.0.dev0'
    assert metadata['license']=='MIT' and metadata['dependencies']==[]
    assert metadata['scripts']['aion']=='aion.cli:main'
    assert 'MIT License' in (ROOT/'LICENSE').read_text()
    assert 'urls' not in metadata  # No invented GitHub username/repository URL.


def test_public_secret_scanner_finds_credentials_without_echoing_values():
    token='ghp_'+'a'*36
    rows=scan_text('safe\n'+token+'\n'+'-----BEGIN '+'PRIVATE KEY-----')
    assert {'kind':'github-token','line':2} in rows
    assert {'kind':'private-key','line':3} in rows
    assert token not in str(rows)
    assert not scan_text('aion/workloads/manifest.json\nC:/private/path\n'+'9e2af3e3'*8)


def test_private_home_paths_are_flagged_but_portable_variables_are_not():
    assert scan_text('/'+'Users/example/private.txt')[0]['kind']=='private-home-path'
    assert not scan_text('$HOME/project and $(brew --prefix llvm@18)')
