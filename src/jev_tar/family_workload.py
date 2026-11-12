import math
from .core import family_propagate

def family_workload_curve(rows,cutoffs):
 error='Charge familiale invalide / Invalid family workload / Carga familiar inválida'
 if not isinstance(rows,list)or len(rows)>100000 or not isinstance(cutoffs,list)or not 1<=len(cutoffs)<=100:raise ValueError(error)
 seen=set()
 for r in rows:
  if not isinstance(r.get('id'),str)or not r['id']or r['id']in seen or type(r.get('responsive_score'))not in(int,float)or not math.isfinite(r['responsive_score'])or not 0<=r['responsive_score']<=1:raise ValueError(error)
  if r.get('family_id')is not None and not isinstance(r['family_id'],str):raise ValueError(error)
  seen.add(r['id'])
 points=[]
 for cutoff in cutoffs:
  if type(cutoff)not in(int,float)or not math.isfinite(cutoff)or not 0<=cutoff<=1:raise ValueError(error)
  marked,counts=family_propagate(rows,cutoff);families={('family',r['family_id'])if r.get('family_id')else('single',r['id'])for r in marked if r['in_review']}
  points.append({'cutoff':cutoff,**counts,'review_units':len(families),'family_inflation':counts['total_review']-counts['direct']})
 return {'points':points,'effectiveness_measured':False,'independent_document_samples_assumed':False}
