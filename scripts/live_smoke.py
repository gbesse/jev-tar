# Purpose: Opt-in paid smoke test capped at one synthetic Jev request.
from jev_tar.client import JevClient
client=JevClient()
result=client.judge({"id":"synthetic-1","text":"A synthetic document about a contract."},{"responsive":{"type":"noul","instructions":"Responsive to a synthetic request"}})
print({"answers":result["answers"],"usage":result.get("usage"),"estimated_cost_usd":result.get("estimated_cost_usd")})
