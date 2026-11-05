import unittest
from jev_tar.core import classify
from jev_tar.client import FakeJev
P={'responsive':{'statement':'responsive'},'privilege':{'statement':'privilege'}}
class ResumeIdentityTests(unittest.TestCase):
 def test_unchanged_no_calls(self):
  rows=[{'id':'a','text':'source'}];first=classify(rows,P,FakeJev());provider=FakeJev();self.assertEqual(classify(rows,P,provider,existing=first),first)
 def test_changed_text_refused(self):
  first=classify([{'id':'a','text':'old'}],P,FakeJev())
  with self.assertRaises(ValueError):classify([{'id':'a','text':'new'}],P,FakeJev(),existing=first)
 def test_changed_protocol_refused(self):
  rows=[{'id':'a','text':'source'}];first=classify(rows,P,FakeJev());q={**P,'responsive':{'statement':'new question'}}
  with self.assertRaises(ValueError):classify(rows,q,FakeJev(),existing=first)
 def test_noul_without_distribution(self):
  class Provider:
   def judge(self,state,questions):return {'answers':{k:{'noul':.6}for k in questions}}
  self.assertEqual(classify([{'id':'a','text':'source'}],P,Provider())[0]['responsive_score'],.6)
