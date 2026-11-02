from contextlib import redirect_stdout,redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aion.cli import main,parser
from aion.storage import atomic_json,read_json
from tests.test_reliable_benchmarking import synthetic_run
from tests.test_quality import study


class Phase4CliTests(unittest.TestCase):
    def invoke(self,args):
        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):code=main(args)
        return code,out.getvalue(),err.getvalue()

    def test_diagnostic_commands_and_confirmation_role_parse(self):
        self.assertTrue(parser().parse_args(['preflight','--require-native']).require_native)
        self.assertEqual(parser().parse_args(['benchmark','--input-role','confirmation']).input_role,'confirmation')
        self.assertTrue(parser().parse_args(['profile','--from-result','result.json','--hotspots']).hotspots)
        self.assertEqual(parser().parse_args(['sanitize','--sanitizer','address']).sanitizer,['address'])

    def test_confirmation_input_role_reaches_existing_engine_protocol(self):
        run=synthetic_run(purpose='independent_confirmation')
        with tempfile.TemporaryDirectory() as directory,patch('aion.cli.ClangAdapter'),patch('aion.cli.run_experiment',return_value=run) as experiment:
            code,_,err=self.invoke(['--store',directory,'benchmark','--candidate','o2','--input-role','confirmation'])
        self.assertEqual(code,0,err)
        self.assertEqual(experiment.call_args.kwargs['purpose'],'independent_confirmation')
        self.assertIn('session',experiment.call_args.kwargs)

    def test_heldout_role_rejects_legacy_wall_timing(self):
        code,_,err=self.invoke(['benchmark','--input-role','confirmation','--no-calibration'])
        self.assertEqual(code,2)
        self.assertIn('calibrated',err)

    def test_quality_directory_selects_controls_and_preserves_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);sources=root/'sources';sources.mkdir()
            for i,run in enumerate(study()):atomic_json(sources/f'control-{i}.json',run)
            atomic_json(sources/'other.json',{'schema_version':1,'evidence_kind':'preflight'})
            before={p:p.read_bytes() for p in sources.glob('*.json')}
            code,_,err=self.invoke(['--store',str(root/'output'),'quality','--directory',str(sources),'--output',str(root/'quality.md')])
            self.assertEqual(code,0,err)
            self.assertTrue(all(p.read_bytes()==data for p,data in before.items()))
            self.assertIn('Benchmark readiness',(root/'quality.md').read_text())
            self.assertEqual(read_json(next((root/'output/results').glob('*.json')))['evidence_kind'],'measurement-quality')

    def test_diagnostic_evidence_cannot_use_promotion_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'profile.json'
            atomic_json(source,{'schema_version':1,'evidence_kind':'profiling'})
            code,_,err=self.invoke(['report','--result',str(source),'--audit-json',str(root/'audit.json')])
            self.assertEqual(code,2)
            self.assertIn('primary timing',err)
            self.assertFalse((root/'audit.json').exists())

    def test_malformed_diagnostic_report_is_a_clear_error(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'malformed.json'
            atomic_json(source,{'schema_version':1,'evidence_kind':'profiling'})
            code,_,err=self.invoke(['report','--result',str(source)])
            self.assertEqual(code,2)
            self.assertIn('Invalid diagnostic evidence JSON',err)
            self.assertNotIn('Traceback',err)
