"""Data-only proposal validation and an honestly labeled offline ranking baseline."""
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re

from .errors import AionError
from .mvp_catalog import available,MAX_PROPOSALS,MAX_SELECTED
from .optimization import ALLOWED_FLAGS

MAX_IMPORT_BYTES=65536


def exact_keys(value,keys,label):
    if not isinstance(value,dict) or set(value)!=set(keys):
        raise AionError(f'{label} must contain exactly: {", ".join(sorted(keys))}.')


def read_proposals(path):
    path=Path(path)
    if path.stat().st_size>MAX_IMPORT_BYTES:raise AionError('AI proposal file exceeds 64 KiB.')
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise AionError('Duplicate JSON keys are not accepted.')
            result[key]=value
        return result
    def constant(_):raise AionError('Nonfinite JSON numbers are not accepted.')
    try:
        return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=pairs,parse_constant=constant)
    except (ValueError,UnicodeError) as exc:raise AionError(f'Invalid AI proposal JSON: {exc}') from exc


def plain_reason(value):
    if not isinstance(value,str) or not 1<=len(value.strip())<=1200 or any(ord(c)<32 for c in value):
        raise AionError('Proposal reasons must be a bounded single paragraph.')
    try:value.encode('utf-8')
    except UnicodeError as exc:raise AionError('Proposal reasons must contain valid Unicode text.') from exc
    if any(c in value for c in ('`','<','>','{','}',';','|','\\','/','$')) or re.search(
        r'(?i)\b(bash|powershell|pwsh|python|cmd|sh|exec|eval|subprocess|curl|wget|whoami|chmod|echo|rm|del|touch|cat|invoke-expression)\b|#include|\b__\w+__|\b(open|system|popen|compile|globals|getattr|import|lambda)\s*\(',value):
        raise AionError('Executable content, markup, shell syntax and paths are not proposal reasons.')
    if re.search(r'(?i)\b(native[- ]validated|scientifically[- ]verified|guaranteed|universally faster|verified improvement|verified speedup)\b',value):
        raise AionError('AI reasons may describe hypotheses, not verified performance claims.')
    if any(flag not in ALLOWED_FLAGS for flag in re.findall(r'(?<!\w)-[A-Za-z][\w=+-]*',value)):
        raise AionError('Unknown compiler flag in proposal text.')
    return value.strip()


def validate_ai(payload,workload,context_sha):
    exact_keys(payload,{'schema_version','evidence_kind','context_sha256','provenance','proposals'},'AI response')
    if type(payload['schema_version']) is not int or payload['schema_version']!=1 or payload['evidence_kind']!='mvp-proposals' or payload['context_sha256']!=context_sha:
        raise AionError('AI response has a wrong schema, kind or discovery-only context fingerprint.')
    provenance=payload['provenance']
    exact_keys(provenance,{'kind','origin','provider','model','generated_at','evidence_scope'},'AI provenance')
    if provenance['kind']!='external-llm' or not isinstance(provenance['origin'],str) or provenance['origin'] not in {'coding-assistant','external-model'} or provenance['evidence_scope']!='discovery-only':
        raise AionError('AI provenance must identify external generation using discovery-only evidence.')
    for key in ('provider','model'):
        if not isinstance(provenance[key],str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._()+-]{0,119}',provenance[key]):
            raise AionError('Provider/model labels must be bounded names, not executable content or paths.')
    try:
        if not isinstance(provenance['generated_at'],str) or len(provenance['generated_at'])>40 or datetime.fromisoformat(provenance['generated_at']).tzinfo is None:raise ValueError()
    except ValueError as exc:raise AionError('AI generation time must be an ISO timestamp with a timezone.') from exc
    proposals=payload['proposals']
    if not isinstance(proposals,list) or not 1<=len(proposals)<=MAX_PROPOSALS:
        raise AionError('AI response needs 1..16 bounded proposals.')
    catalog={p.name:p for p in available(workload)};seen=set();result=[]
    for item in proposals:
        exact_keys(item,{'workload_id','panel_id','reason','priority','estimated_cost'},'AI proposal')
        name=item['panel_id']
        if not isinstance(name,str) or name not in catalog or item['workload_id']!=workload or name in seen:
            raise AionError('Proposal references an unknown, duplicate, unavailable or incompatible panel.')
        seen.add(name)
        if type(item['priority']) is not int or not 1<=item['priority']<=100:raise AionError('Priority must be an integer from 1 to 100.')
        reason=plain_reason(item['reason']);cost=item['estimated_cost']
        if cost is not None:
            exact_keys(cost,{'commands','seconds'},'Estimated cost')
            if type(cost['commands']) is not int or not 1<=cost['commands']<=10000 or type(cost['seconds']) not in {int,float} or not math.isfinite(cost['seconds']) or not 0<cost['seconds']<=7200:
                raise AionError('Estimated cost must be finite and bounded; it cannot change execution limits.')
        result.append({**item,'reason':reason,'provenance':{**provenance,'authenticity':'caller supplied; external model authorship is not authenticated by AION; no model call was made'}})
    return result


def deterministic(workload,seed,iterations=7,warmups=1):
    result=[]
    for panel in available(workload):
        original_anchor=(panel.reference.mode=='standard' and panel.reference.flags==('-O3',) and panel.reference.variant==panel.candidate.variant)
        source_o3=panel.reference.mode=='standard' and panel.reference.flags==('-O3',)
        tier=0 if original_anchor else 1 if source_o3 else 2 if panel.reference.mode==panel.candidate.mode=='standard' else 3
        pgo=sum(r.mode=='pgo' for r in (panel.reference,panel.candidate))
        commands=55+2*(iterations+warmups)+pgo*12
        result.append({'workload_id':workload,'panel_id':panel.name,'reason':
            ('Prioritize a standard O3 anchor.' if original_anchor else 'Test a bundled source intervention against O3.' if source_o3 else 'Test one bounded compiler policy against its declared reference.')+
            ' Prefer lower estimated build cost within the same tier; use a seeded stable tie break.',
            'priority':tier+1,'estimated_cost':{'commands':commands,'seconds':25+4*(iterations+warmups)*.375+pgo*20+10*sum('-flto' in r.flags for r in (panel.reference,panel.candidate))},
            'provenance':{'kind':'deterministic','algorithm':'catalog-cost-v1','seed':seed,
                          'cost_scope':'rough two-role compute/build estimate; correctness/setup and toolchain costs vary'}})
    return result


def rank(proposals,seed,maximum):
    if type(maximum) is not int or not 1<=maximum<=MAX_SELECTED:raise AionError('Select 1..4 candidates.')
    if not proposals or len(proposals)>MAX_PROPOSALS:raise AionError('Bounded proposal count exceeded.')
    def key(item):
        cost=item['estimated_cost'];commands=cost['commands'] if cost else 10000
        seconds=cost['seconds'] if cost else 7200
        tie=hashlib.sha256(f"{seed}:{item['panel_id']}".encode()).hexdigest()
        return (item['priority'],commands,seconds,tie,item['panel_id'])
    ordered=sorted(proposals,key=key)
    return [{'proposal':p,'rank':i+1,'selected':i<maximum,
             'decision':'selected before discovery' if i<maximum else 'rejected by the declared candidate-count budget'} for i,p in enumerate(ordered)]
