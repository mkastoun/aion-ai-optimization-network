"""Audit intended Git files without printing possible secret values. Not a proof of absence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SECRET_PATTERNS={
    'private-key':r'-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----',
    'github-token':r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b',
    'aws-access-key':r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'provider-key':r'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}',
    'private-home-path':r'(?:[A-Za-z]:[/\\]Users[/\\]|/Users/|/home/)[A-Za-z0-9_.-]+',
}


def git(*parts):
    return subprocess.run(['git',*parts],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)


def scan_text(text):
    return [{'kind':kind,'line':text.count('\n',0,match.start())+1} for kind,pattern in SECRET_PATTERNS.items()
            for match in re.finditer(pattern,text)]


def audit():
    tracked=git('ls-files','-z')
    untracked=git('ls-files','--others','--exclude-standard','-z')
    if tracked.returncode or untracked.returncode:raise RuntimeError('A local Git repository is required')
    tracked_paths=tracked.stdout.decode().strip('\0').split('\0') if tracked.stdout else []
    paths=sorted(set(tracked_paths+[p for p in untracked.stdout.decode().split('\0') if p]))
    findings=[];manifest={}
    forbidden={'.aion','.venv','build','dist','__pycache__','.pytest_cache','.git','.idea','.vscode'}
    for name in paths:
        path=ROOT/name
        if path.is_symlink():
            findings.append({'path':name,'kind':'symlink-needs-review'});continue
        if not path.is_file():
            findings.append({'path':name,'kind':'missing-tracked-file'});continue
        if any(p in forbidden or p.startswith('.venv') or p.endswith('.egg-info') for p in Path(name).parts) or path.suffix.lower() in {'.exe','.o','.obj','.whl','.profraw','.profdata','.key','.pem','.pfx','.p12'} or path.name=='.env' or path.name.startswith('.env.'):
            findings.append({'path':name,'kind':'generated-or-sensitive-file-in-intended-tree'})
        data=path.read_bytes();manifest[name]=hashlib.sha256(data).hexdigest()
        try:text=data.decode('utf-8')
        except UnicodeError:
            findings.append({'path':name,'kind':'binary-needs-review'});continue
        findings.extend({'path':name,**item} for item in scan_text(text))
    whitespace={}
    for command in (('diff','--check'),('diff','--cached','--check')):
        result=git(*command);whitespace[' '.join(command)]={'returncode':result.returncode,'output':result.stdout.decode(errors='replace')}
    history=git('log','-1','--format=%H')
    return {'schema_version':1,'passed':not findings and all(v['returncode']==0 for v in whitespace.values()),
        'tracked_files':len(tracked_paths),'intended_files':len(paths),'findings':findings,'files':manifest,'whitespace':whitespace,
        'history':'existing history requires a separate historical-secret audit' if history.returncode==0 and history.stdout.strip() else 'unborn local repository; no commit history',
        'scope':'current tracked plus untracked nonignored files; pattern scan, not a credential/ownership guarantee',
        'owner_review_required':['source ownership and license authority','private security/conduct contact','publication authorization']}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=audit();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
