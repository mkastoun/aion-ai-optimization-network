import json
import unittest
from aion.expanded_reference import image_output,kv_output,expected_expanded
from aion.benchmarks import load_benchmarks


class ExpandedApplicationTests(unittest.TestCase):
    def test_ten_workloads_and_two_new_multifile_programs(self):
        self.assertEqual(len(load_benchmarks()),10)
        for benchmark in load_benchmarks('image,kv'):
            self.assertEqual(len(benchmark.sources),4)
            self.assertTrue(all(p.is_file() for p in benchmark.source_files))
            self.assertNotEqual(benchmark.case('training')['args'][1],benchmark.performance_case['args'][1])

    def test_flat_and_single_pixel_have_zero_gradient(self):
        for n in (0,1,3):
            output=json.loads(image_output(n,0))
            self.assertEqual(output['sum'],0)
            self.assertEqual(sum(output['histogram']),n*n)
            self.assertEqual(output['histogram'][0],n*n)
        self.assertEqual(json.loads(image_output(1,123))['sum'],0)
        self.assertGreater(json.loads(image_output(4,(1<<32)-1))['sum'],0)

    def test_hotspot_crud_has_independently_known_state(self):
        output=json.loads(kv_output(16,0))
        self.assertEqual((output['queries'],output['hits'],output['updates'],output['deletes']),(6,6,2,2))
        self.assertEqual([k for k,_ in output['entries']],[0,1])
        self.assertTrue(all(8<=len(value)<=96 for _,value in output['entries']))
        self.assertEqual(json.loads(kv_output(0,42))['entries'],[])

    def test_fixed_patterns_survive_round_seed_wrap(self):
        self.assertEqual(expected_expanded('image',4,0,2),str((int(expected_expanded('image',4,0,1))*2)&((1<<64)-1)))
