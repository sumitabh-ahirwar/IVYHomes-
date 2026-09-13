from api import *
a = Api()
paths = [
 "/v1/listings", "/v1/listing/100-1000042", "/v1/rentals", "/v1/projects",
 "/v1/favourites", "/v1/favorites", "/v1/analytics/summary",
 "/v1/analytics", "/v1/localities", "/v1/cities", "/v1/me", "/v1/stats",
 "/openapi.json", "/docs", "/v1/search",
]
for p in paths:
    r = a.get(p, limit=2)
    show(r, 700)
