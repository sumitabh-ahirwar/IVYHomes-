from api import *
a = Api()
lid = "SQU-5004678"
for p in [f"/v1/listings/{lid}", f"/v1/listing/{lid}", f"/v1/listings/{lid}/similar",
          "/v1/rentals/R5000001", "/v1/rental/R5000001", "/v1/projects/P50001",
          "/v1/saved", "/v1/user/favourites", "/v1/bookmarks", "/v1/shortlist",
          "/v1/users/me/favourites", "/v1/wishlist", "/v1/saved-listings",
          "/auth/me", "/v1/analytics/summary/", "/v1/summary", "/v1/analytics/overview"]:
    r = a.get(p)
    print(f"{r.status_code}  {p}  -> {r.text[:220]}")
