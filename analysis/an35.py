from api import *
import json
a=Api()
r=a.get("/v1/projects", limit=50, sort_by="price_min", order="asc").json()["results"]
print("price_min ASC, first 16 (project_id, price_min shown):")
for x in r[:16]: print(f"  {x['project_id']} price_min={x['price_min']:7.2f} price_max={x['price_max']:6.2f}")
lakh={'P50096','P50174','P50243','P50247','P50446','P50462'}
pos=[i for i,x in enumerate(r) if x["project_id"] in lakh]
print("\npositions of the 6 lakh-valued projects in ASC order:", pos)
print("their shown price_min:", [x["price_min"] for x in r if x["project_id"] in lakh])
print("their /100 (i.e. lakh->crore):", [round(x["price_min"]/100,3) for x in r if x["project_id"] in lakh])
print("\nneighbours' price_min around those positions:", [round(x['price_min'],2) for x in r[:12]])
