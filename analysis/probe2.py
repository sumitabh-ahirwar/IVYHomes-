from api import *
import json
a = Api()
r = a.get("/v1/listings", limit=1)
print("LISTING OBJECT:"); print(json.dumps(r.json()["results"][0], indent=1))
r = a.get("/v1/rentals", limit=1)
print("RENTAL OBJECT:"); print(json.dumps(r.json()["results"][0], indent=1))
r = a.get("/v1/projects", limit=1)
print("PROJECT OBJECT:"); print(json.dumps(r.json()["results"][0], indent=1))
