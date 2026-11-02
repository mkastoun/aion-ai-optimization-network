"""Reports for typed non-promotion evidence."""
from .errors import AionError


def render_diagnostic_report(run):
    kind=run.get("evidence_kind")
    lines=[f"# AION {kind} evidence","",f"Run: `{run.get('run_id')}`; status: **{run.get('status')}**.",
           f"Session: `{run.get('session',{}).get('session_id','unavailable')}`; environment: **{run.get('host_start',{}).get('environment_classification','unavailable')}**.",
           "This diagnostic record cannot create optimization presets. No primary timing samples are pooled.",""]
    if kind=='package-smoke':
        lines += ["Independent installed-wheel smoke; single samples are package validation only.",
                  f"Installed package: `{run.get('installed_package')}`.","",
                  "| Workload | Baseline status | Correctness | Samples |","|---|---|---|---:|"]
        for w,b in run['benchmarks'].items():
            e=b['configurations']['baseline']
            lines.append(f"| {w} | {e['status']} | {e['verification']['passed']} | {len(e['samples'])} |")
    elif kind=="preflight":
        lines += [f"Ready for local validation: **{run['ready_for_local_validation']}**.",
                  f"Native Linux environment detected: **{run['native_environment_detected']}**; native performance evidence available: **False**.",
                  "A successful preflight does not validate measurement quality.","",*[f"- {s}" for s in run['warnings']]]
        counters=run.get("checks",{}).get("counters",{})
        lines += ["",f"Counter capability: {counters.get('available')}; {counters.get('reason','see per-event observations')}.",""]
        for e in counters.get("events",[]): lines.append(f"- {e['name']} ({e['kind']}): {e['status']}; {e.get('reason') or 'counted'}.")
    elif kind=="sanitizer-validation":
        lines += [run['scope'],run['limits_note'],"","| Workload | Mode | Cases passed/total | Outcome |","|---|---|---:|---|"]
        for w,b in run['benchmarks'].items():
            for mode,e in b['modes'].items(): lines.append(f"| {w} | {mode} | {sum(c['passed'] for c in e['checks'])}/{len(e['checks'])} | {e['status']} |")
        lines += ["","ASan/UBSan diagnostics, commands, limits, source/binary/build hashes and per-case output checks remain in JSON."]
    elif kind=="profiling":
        lines += [f"Source timing result: `{run['source_result']['run_id']}` / SHA-256 `{run['source_result']['sha256']}`.",
                  "Counters cover whole-process exec through exit, including setup; primary comparisons use compute-only clocks. Rusage is software accounting. Multiplexed scaled estimates are labeled and ratios are suppressed.",
                  "","| Workload | Config | Timed binary matches | Checks passed | Counted events / attempted event observations | Hotspots |","|---|---|---|---:|---:|---|"]
        for w,b in run['benchmarks'].items():
            for n,e in b['configurations'].items():
                events=[v for s in e['samples'] for v in s['counters']['events']]
                lines.append(f"| {w} | {n} | {e['matches_timed_binary']} | {sum(s['passed'] for s in e['samples'])}/{len(e['samples'])} | {sum(v['status']=='counted' for v in events)}/{len(events)} | {e.get('hotspots',{}).get('available','not requested')} |")
        lines += ["","## Event observations","","| Workload/config | Sample | Event | Kind | Status | Raw count | Enabled/running ns | Scaled estimate |","|---|---:|---|---|---|---:|---|---:|"]
        for w,b in run['benchmarks'].items():
            for n,e in b['configurations'].items():
                for s in e['samples']:
                    for event in s['counters']['events']:
                        lines.append(f"| {w}/{n} | {s['iteration']} | {event['name']} | {event['kind']} | {event['status']} | {event['raw_count']} | {event['time_enabled_ns']}/{event['time_running_ns']} | {event['scaled_estimate']} |")
        lines += ["","Per-sample IPC and miss rates are in JSON only when both source events are counted and unmultiplexed. Missing counters do not produce zeros. Available wait4 context-switch/fault observations are preserved separately. Static assembly/IR counts are not retired instructions or evidence of hot regions."]
        lines += ["","## Derived and software observations","",
                  "| Workload/config | Sample | IPC | Cache miss rate | Branch miss rate | wait4 voluntary/involuntary switches | wait4 minor/major faults |",
                  "|---|---:|---:|---:|---:|---|---|"]
        for w,b in run['benchmarks'].items():
            for n,e in b['configurations'].items():
                for s in e['samples']:
                    d=s['counters']['derived'];usage=s['counters']['resource_usage'].get('values') or {}
                    metrics=[d[k]['value'] if d[k]['value'] is not None else 'unavailable' for k in ('instructions_per_cycle','cache_miss_rate','branch_miss_rate')]
                    lines.append(f"| {w}/{n} | {s['iteration']} | {' | '.join(str(v) for v in metrics)} | {usage.get('voluntary_context_switches')}/{usage.get('involuntary_context_switches')} | {usage.get('minor_page_faults')}/{usage.get('major_page_faults')} |")
        lines += ["","## Separate sampled hot regions","",
                  "Sample fractions are fractions of recorded user-cycle IPs, not exact CPU time or causal optimization effects. Raw addresses, mappings, symbols, unresolved IPs and loss indicators remain in JSON."]
        for w,b in run['benchmarks'].items():
            for n,e in b['configurations'].items():
                h=e.get('hotspots',{})
                if not h: continue
                lines += ["",f"### {w}/{n}","",f"Sampling available: {h.get('available')}; complete without reported loss: {h.get('complete','unavailable')}. {h.get('reason') or ''}","",
                          "| Object | Symbol | Samples | Fraction of recorded samples |","|---|---|---:|---:|"]
                for symbol in h.get('resolved',{}).get('symbols',[])[:10]:
                    verified=h.get('resolved',{}).get('resolution_methodology_version',1)>=2
                    label=((symbol.get('symbol') or 'unresolved') if verified else 'unverified nearest-symbol hint; use a range-verified symbol audit').replace('|','\\|')
                    lines.append(f"| {symbol.get('object')} | {label} | {symbol['sample_count']} | {symbol['sample_fraction']:.3f} |")
    elif kind=='symbol-resolution':
        lines += [run['note'],f"Source profile: `{run['source_profile']['run_id']}`, SHA-256 `{run['source_profile']['sha256']}`."]
        for w,b in run['benchmarks'].items():
            for n,e in b['configurations'].items():
                lines += ['',f'## {w}/{n}','',f"Recorded samples: {e['sample_count']}; lost: {e['lost_samples']}; overrun: {e['buffer_overrun']}. Binary matches timing: {e['matches_timed_binary']}.",
                          '', '| Object | Range-verified symbol | Samples | Sample fraction |','|---|---|---:|---:|']
                for s in e['resolved']['symbols'][:15]:
                    label=(s['symbol'] or 'unresolved (no verified function range)').replace('|','\\|')
                    lines.append(f"| {s['object']} | {label} | {s['sample_count']} | {s['sample_fraction']:.3f} |")
    elif kind=="measurement-quality":
        lines += [run['pooling'],run['uncertainty_caveat'],"","## Benchmark readiness",""]
        for key,value in run['readiness'].items(): lines.append(f"- {key}: {value}")
        for s in run['strata']:
            lines += ["",f"## Stratum {s['stratum']}: {s['environment_classification']}, CPUs {s['requested_cpus']}",
                      f"Sessions: {len(s['session_ids'])}; runs: {len(s['run_ids'])}; cross-session design complete: {s['cross_session_design_complete']}.",
                      f"Measurement quality checks passed: **{s['measurement_quality_checks_passed']}**.","",
                      "| Descriptive rate | Count/total | Fraction | Approximate 95% interval |","|---|---:|---:|---|"]
            for name,r in s['rates'].items():
                fraction=f"{100*r['fraction']:.1f}%" if r['fraction'] is not None else "unavailable"
                interval=f"[{100*r['interval_95'][0]:.1f}%, {100*r['interval_95'][1]:.1f}%]" if r['interval_95'] else "unavailable"
                lines.append(f"| {name} | {r['count']}/{r['total']} | {fraction} | {interval} |")
            if s.get('descriptive_distributions'):
                d=s['descriptive_distributions']
                lines += ['',f"Duration band: {d['target_band_executions']}/{d['measured_executions']} executions; correctness: {d['correct_executions']}/{d['measured_executions']}.",
                          f"CV range/median: {d['cv']['minimum']} / {d['cv']['median']} / {d['cv']['maximum']}; drifting summaries: {d['drifting_summary_count']}. Raw distributions remain in JSON."]
            lines += ["","| Run | Session | Workload | Control | Outcome | Failed gates | CV baseline/candidate % | Paired interval % |","|---|---|---|---|---|---|---|---|"]
            for r in s['rows']:
                c=r.get('comparison',{});u=c.get('uncertainty',{})
                cvs='/'.join(f"{100*c[k]['coefficient_of_variation']:.2f}" if (c.get(k) or {}).get('coefficient_of_variation') is not None else "unavailable" for k in ('paired_baseline_summary','paired_candidate_summary'))
                ci=f"[{100*u['improvement_ci_low']:.2f}, {100*u['improvement_ci_high']:.2f}]" if u else "unavailable"
                lines.append(f"| {r['run_id']} | {r.get('session_id','unavailable')} | {r['workload']} | {r['control']} | {r['outcome']} | {', '.join(r.get('gates',{}).get('failed',[]))} | {cvs} | {ci} |")
        lines += ["","Descriptive outcome counts do not establish equivalence, a universal false-positive rate, or validated physical isolation. Start/end host observations and source JSON hashes remain in the audit."]
    else: raise AionError("Unknown diagnostic evidence kind.")
    return '\n'.join(lines)+'\n'
