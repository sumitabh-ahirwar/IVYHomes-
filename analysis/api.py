"""Shared API client for Ivy Homes probing. Handles auth + refresh + retries."""
import json, os, time, urllib.parse
import requests

BASE = "https://solve.ivy.homes"
KEY = "IVY26-0D2F818EE4B7"
EMAIL = "demo1@ivy.homes"
PASSWORD = "8adfaaa62a"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

class Api:
    def __init__(self, email=EMAIL):
        self.s = requests.Session()
        self.s.headers["X-API-Key"] = KEY
        self.email = email
        self.access = None
        self.refresh = None
        self.exp = 0
        self.calls = 0
        self.login()

    def login(self):
        r = self.s.post(f"{BASE}/auth/login", json={"email": self.email, "password": PASSWORD})
        r.raise_for_status()
        j = r.json()
        self.access = j["access_token"]
        self.refresh = j.get("refresh_token")
        self.exp = time.time() + j.get("expires_in", 900)
        self.s.headers["Authorization"] = f"Bearer {self.access}"
        return j

    def ensure(self):
        if time.time() > self.exp - 60:
            if self.refresh:
                r = self.s.post(f"{BASE}/auth/refresh", json={"refresh_token": self.refresh})
                if r.status_code == 200:
                    j = r.json()
                    self.access = j["access_token"]
                    self.refresh = j.get("refresh_token", self.refresh)
                    self.exp = time.time() + j.get("expires_in", 900)
                    self.s.headers["Authorization"] = f"Bearer {self.access}"
                    return
            self.login()

    def get(self, path, **params):
        self.ensure()
        for attempt in range(5):
            r = self.s.get(f"{BASE}{path}", params=params or None)
            self.calls += 1
            if r.status_code == 429:
                time.sleep(2 + attempt)
                continue
            if r.status_code == 401:
                self.login()
                continue
            return r
        return r

    def raw(self, method, path, **kw):
        self.ensure()
        r = self.s.request(method, f"{BASE}{path}", **kw)
        self.calls += 1
        return r

def show(r, n=1400):
    print(f"HTTP {r.status_code} {r.url}")
    t = r.text
    print(t[:n] + ("..." if len(t) > n else ""))
    print("-" * 70)
