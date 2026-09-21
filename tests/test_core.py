# Purpose: Verify statistical, family, chunking, audit, resume and export invariants.
import tempfile, unittest
from pathlib import Path
from jev_tar import *

PROTOCOL={"matter":"x","responsive":{"statement":"responsive"},"privilege":{"statement":"privileged"},"issues":{},"thresholds":{"review_above":.5},"target_recall":.8}

class CoreTests(unittest.TestCase):
    def test_sample_plan_and_wilson(self):
        self.assertEqual(plan_sample(120000,.02,.95)["sample_size"],2354)
        self.assertEqual(plan_sample(10**12,.05,.95)["sample_size"],385)
        low,high=wilson_interval(0,100);self.assertEqual(low,0);self.assertGreater(high,.03)
    def test_elusion_zero_is_not_zero_risk(self):
        result=elusion_estimate([{"human_responsive":"false"} for _ in range(100)],1000,80)
        self.assertEqual(result["estimated_missed"],0);self.assertGreater(result["missed_interval"][1],0)
    def test_family_and_chunk_max(self):
        provider=FakeJev({"a":{"responsive":.8,"privilege":.1},"b":{"responsive":.1,"privilege":.1}})
        rows=classify([{"id":"a","text":"x"*8,"family_id":"f"},{"id":"b","text":"x","family_id":"f"}],PROTOCOL,provider,chunk_chars=4)
        result,report=family_propagate(rows,.5);self.assertEqual(report,{"direct":1,"family_propagated":1,"total_review":2});self.assertEqual(len(provider.calls),3);self.assertTrue(result[1]["family_propagated"])
    def test_cutoff_splits_ids(self):
        judgments=[{"id":str(i),"responsive_score":i/10} for i in range(10)]
        control=[{"id":str(i),"human_responsive":i>=5} for i in range(10)]
        result=select_cutoff(judgments,control,.8,seed=3);self.assertFalse(set(result["tune_ids"]) & set(result["holdout_ids"]))
    def test_seed_and_privilege_log(self):
        rows=[{"id":str(i),"responsive_score":.1,"privilege_score":i/10} for i in range(10)]
        self.assertEqual(sample_elusion(rows,.5,4,7),sample_elusion(rows,.5,4,7))
        self.assertTrue(all("attorney confirmation" in x["status"] for x in privilege_log(rows)))
    def test_audit_interrupt_resume_and_export(self):
        class Interrupt(FakeJev):
            def judge(self,state,questions):
                if len(self.calls)==1: raise RuntimeError("interrupt")
                return super().judge(state,questions)
        with tempfile.TemporaryDirectory() as folder:
            audit=Path(folder)/"audit.jsonl"; rows=[{"id":"1","text":"x"},{"id":"2","text":"y"}]
            with self.assertRaises(RuntimeError): classify(rows,PROTOCOL,Interrupt(),audit_path=audit)
            self.assertEqual(len(audit.read_text().splitlines()),1)
            first=classify(rows[:1],PROTOCOL,FakeJev()); resumed=classify(rows,PROTOCOL,FakeJev(),existing=first)
            self.assertEqual(len(resumed),2)
            manifest=export_production(resumed,Path(folder)/"out"); data=(Path(folder)/"out/production.dat").read_text()
            self.assertIn("\x14",data);self.assertIn("\x13",data);self.assertEqual(manifest["documents"],2)

if __name__=="__main__": unittest.main()
