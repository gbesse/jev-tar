import unittest,copy,math
from jev_tar.family_workload import family_workload_curve
class FamilyWorkload(unittest.TestCase):
 def test_family_pullup_visible(self):
  rows=[{'id':'a','family_id':'f','responsive_score':.95},{'id':'b','family_id':'f','responsive_score':.1},{'id':'c','responsive_score':.1}];x=family_workload_curve(rows,[.9,.99]);self.assertEqual(x['points'][0]['direct'],1);self.assertEqual(x['points'][0]['family_propagated'],1);self.assertEqual(x['points'][0]['review_units'],1);self.assertEqual(x['points'][1]['total_review'],0)
 def test_singletons_not_one_shared_family(self):
  x=family_workload_curve([{'id':'a','responsive_score':1},{'id':'b','responsive_score':1}],[.5]);self.assertEqual(x['points'][0]['review_units'],2)
 def test_invalid_probability(self):
  with self.assertRaises(ValueError):family_workload_curve([{'id':'a','responsive_score':math.nan}],[.5])
