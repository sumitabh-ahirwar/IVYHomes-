from api import *
import json
from datetime import datetime, timedelta, timezone
a=Api()
IST=timezone(timedelta(hours=5,minutes=30))
def grab(order, n=300):
    out=[]; off=0
    while len(out)<n:
        out+=a.get("/v1/listings", limit=50, offset=off, sort_by="posted_at", order=order).json()["results"]; off+=50
    return out
for order in ("asc","desc"):
    rows=grab(order)
    utc=[datetime.fromisoformat(x["posted_at"].replace("Z","+00:00")) for x in rows]
    d_utc=[d.date() for d in utc]
    d_ist=[d.astimezone(IST).date() for d in rows and utc]
    def mono(seq): 
        return all(seq[i]<=seq[i+1] for i in range(len(seq)-1)) if order=="asc" else all(seq[i]>=seq[i+1] for i in range(len(seq)-1))
    print(f"order={order}: full-timestamp monotonic={mono(utc)}  UTC-date monotonic={mono(d_utc)}  IST-date monotonic={mono(d_ist)}")
    bad=[(i,d_ist[i],d_ist[i+1]) for i in range(len(d_ist)-1) if not (d_ist[i]<=d_ist[i+1] if order=="asc" else d_ist[i]>=d_ist[i+1])]
    print(f"   IST-date violations: {len(bad)} {bad[:3]}")
    badu=[(i,d_utc[i],d_utc[i+1]) for i in range(len(d_utc)-1) if not (d_utc[i]<=d_utc[i+1] if order=="asc" else d_utc[i]>=d_utc[i+1])]
    print(f"   UTC-date violations: {len(badu)} {badu[:3]}")
