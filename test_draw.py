"""Runs N full draws (generate -> encrypt -> build -> decrypt) and checks every rule.
Prints only PASS/FAIL per rule, never the pairings."""
import json
import os
import re
import sys

import draw

PW = os.environ.get("SANTA_PASSWORD", "test-password")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 10


def check(a):
    return {
        "everyone gives exactly one gift": sorted(a) == sorted(draw.PEOPLE),
        "everyone receives exactly one gift": sorted(a.values()) == sorted(draw.PEOPLE),
        "nobody draws themselves": all(g != r for g, r in a.items()),
        "Alvise -> Ivana": a["Alvise"] == "Ivana",
        "Wissia does not get Alvise": a["Wissia"] != "Alvise",
        "Matteo does not get Rachele": a["Matteo"] != "Rachele",
        "Rachele does not get Matteo": a["Rachele"] != "Matteo",
        "Luca does not get Ivana": a["Luca"] != "Ivana",
        "Ivana does not get Luca": a["Ivana"] != "Luca",
    }


print(f"{len(draw.all_valid_assignments())} valid assignments exist.")
failures = 0
seen = set()
for i in range(1, N + 1):
    draw.build(PW, target="test_build.html")
    html = open("test_build.html").read()
    payload = json.loads(re.search(r"const DATA = (\{.*?\});", html).group(1))
    a = draw.decrypt(payload, PW)
    seen.add(tuple(sorted(a.items())))
    results = check(a)
    ok = all(results.values())
    failures += not ok
    bad = [k for k, v in results.items() if not v]
    print(f"Run {i:2d}: {'PASS' if ok else 'FAIL ' + ', '.join(bad)}")
    try:
        draw.decrypt(payload, PW + "x")
        print("        FAIL: wrong password accepted"); failures += 1
    except ValueError:
        pass
os.remove("test_build.html")
print(f"{len(seen)} distinct assignments across {N} runs.")
print("ALL PASSED" if failures == 0 else f"{failures} FAILED")
sys.exit(1 if failures else 0)
