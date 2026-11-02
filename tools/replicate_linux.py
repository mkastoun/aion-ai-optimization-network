"""Run one explicit local replication session; no remote or privileged actions."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import uuid


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store',type=Path,required=True)
    parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--cpus',default='auto')
    parser.add_argument('--label',default='local replication session')
    parser.add_argument('--require-native',action='store_true')
    parser.add_argument('--compare-unpinned',action='store_true')
    parser.add_argument('--stage',choices=('all','controls','timing','validation','preflight','report','research'),default='all')
    parser.add_argument('--role',choices=('discovery','confirmation'),help='explicit independent-session timing; omit for legacy immediate optimize workflow')
    parser.add_argument('--peer-store',type=Path,help='other observation session for report stage')
    parser.add_argument('--research-declaration',type=Path)
    parser.add_argument('--research-store',type=Path,help='shared research journal across separate replication sessions')
    parser.add_argument('--native-host-note',help='operator physical-host and observation-window record; new sessions only')
    args=parser.parse_args()
    store=args.store.resolve();store.mkdir(parents=True,exist_ok=True)
    if args.stage=='report':
        if not args.peer_store:parser.error('--stage report requires --peer-store')
        from aion.native_report import replication_report
        from aion.report import render_report
        from aion.storage import ResultStore
        report=replication_report([args.peer_store.resolve(),store])
        path=ResultStore(store).save(report)
        path.with_suffix('.md').write_text(render_report(report),encoding='utf-8')
        print('Replication report:',path)
        return 0  # A pending scientific milestone is explicit in the report.
    session=store/'session.json'
    commands=[['preflight','--cpus',args.cpus,'--counters','--session-file',str(session),'--label',args.label,
               *(['--native-host-note',args.native_host_note] if args.native_host_note and not session.exists() else []),
               *(['--require-native'] if args.require_native else [])]]
    common=['--cpus',args.cpus,'--session-file',str(session)]
    if args.stage in ('all','controls'):
        commands.append(['controls','--benchmark','matrix,records,logs',*common,'--seed',str(args.seed),
                         '--repetitions','2','--iterations','11','--warmups','2',*(['--compare-unpinned'] if args.compare_unpinned else [])])
        commands.append(['controls','--benchmark','image,kv',*common,'--seed',str(args.seed+20),
                         '--distribution-suite','--repetitions','2','--iterations','11','--warmups','2'])
    if args.stage in ('all','timing'):
        commands.append([('benchmark' if args.role else 'optimize'),'--benchmark','all',*common,'--seed',str(args.seed+100),'--iterations','11','--warmups','2',
                         '--candidate','o2','--candidate','lto','--candidate','pgo','--candidate','pgo-lto',
                         *(['--input-role','confirmation' if args.role=='confirmation' else 'performance'] if args.role else ['--confirm-all'])])
    if args.stage=='research':
        if not args.research_declaration or not args.role:parser.error('Research stage requires --research-declaration and --role')
        commands.append(['research','run','--declaration',str(args.research_declaration),'--session-file',str(session),'--role',args.role])
    if args.stage in ('all','validation'):
        commands.append(['sanitize','--benchmark','all',*common,'--evidence',str(store/'sanitizer-artifacts')])
    journal=store/f'replication-invocation-{uuid.uuid4().hex}.json'
    journal.write_text(json.dumps({'scope':'one explicit observation session; run separate sessions for cross-session studies',
                                  'commands':commands,'results':[]},indent=2),encoding='utf-8')
    for command in commands:
        destination=args.research_store.resolve() if command[0]=='research' and args.research_store else store
        invocation=[sys.executable,'-m','aion','--store',str(destination),*command]
        print('Running:',subprocess.list2cmdline(invocation),flush=True)
        completed=subprocess.run(invocation,check=False)
        data=json.loads(journal.read_text(encoding='utf-8'));data['results'].append({'command':invocation,'exit_code':completed.returncode})
        journal.write_text(json.dumps(data,indent=2),encoding='utf-8')
        if completed.returncode:return completed.returncode
    return 0


if __name__=='__main__':raise SystemExit(main())
