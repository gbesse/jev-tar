# Purpose: Run a synthetic end-to-end review without a network call or API key.
from jev_tar import FakeJev, classify, family_propagate, elusion_estimate

protocol={"matter":"Synthetic matter","responsive":{"statement":"Responsive to the request"},"privilege":{"statement":"Potentially privileged"},"issues":{"pricing":"Discusses pricing"},"thresholds":{"review_above":.5},"target_recall":.8}
rows=[{"id":"D1","text":"responsive pricing note","family_id":"F1"},{"id":"D2","text":"attachment","family_id":"F1"},{"id":"D3","text":"lunch menu"}]
provider=FakeJev({"D1":{"responsive":.91,"privilege":.1,"pricing":.8},"D2":{"responsive":.2,"privilege":.2,"pricing":.1},"D3":{"responsive":.1,"privilege":.1,"pricing":.1}})
judged=classify(rows,protocol,provider); propagated,report=family_propagate(judged,.5)
sample=[{"human_responsive":"false"} for _ in range(9)]+[{"human_responsive":"true"}]
print({"source":"synthetic fixture, not measured Jev output","calls":len(provider.calls),"family":report,"elusion":elusion_estimate(sample,100,9),"ids":[r["id"] for r in propagated]})
