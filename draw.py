"""Secret Santa draw: generates a random valid assignment and builds index.html
with the pairings encrypted under a password.

Usage:  SANTA_PASSWORD='...' python3 draw.py            -> writes index.html
The pairings are never printed or written in plain text.
"""
import hashlib
import hmac
import itertools
import json
import os
import secrets
import sys

PEOPLE = ["Alvise", "Wissia", "Matteo", "Rachele", "Luca", "Ivana"]

FIXED = {"Alvise": "Ivana"}  # already extracted
FORBIDDEN = {
    ("Wissia", "Alvise"),
    ("Matteo", "Rachele"),
    ("Rachele", "Matteo"),
    ("Luca", "Ivana"),
    ("Ivana", "Luca"),
}

ITERATIONS = 200_000
PAD = 16


def is_valid(assignment):
    """assignment: dict giver -> receiver. True if it obeys every rule."""
    if sorted(assignment) != sorted(PEOPLE):
        return False  # every person gives exactly once
    if sorted(assignment.values()) != sorted(PEOPLE):
        return False  # every person receives exactly once
    for giver, receiver in assignment.items():
        if giver == receiver or (giver, receiver) in FORBIDDEN:
            return False
    return all(assignment[g] == r for g, r in FIXED.items())


def all_valid_assignments():
    out = []
    for perm in itertools.permutations(PEOPLE):
        a = dict(zip(PEOPLE, perm))
        if is_valid(a):
            out.append(a)
    return out


def draw():
    """Pick uniformly among all valid assignments."""
    return secrets.SystemRandom().choice(all_valid_assignments())


def derive_key(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)


def keystream(key, giver):
    return hmac.new(key, ("pair:" + giver).encode(), hashlib.sha256).digest()[:PAD]


def encrypt(assignment, password):
    salt = secrets.token_bytes(16)
    key = derive_key(password, salt)
    check = hmac.new(key, b"check", hashlib.sha256).hexdigest()
    pairs = {}
    for giver, receiver in assignment.items():
        plain = receiver.encode().ljust(PAD, b" ")
        pairs[giver] = bytes(a ^ b for a, b in zip(plain, keystream(key, giver))).hex()
    return {"salt": salt.hex(), "iterations": ITERATIONS, "check": check,
            "people": PEOPLE, "pairs": pairs}


def decrypt(payload, password):
    key = derive_key(password, bytes.fromhex(payload["salt"]))
    if hmac.new(key, b"check", hashlib.sha256).hexdigest() != payload["check"]:
        raise ValueError("wrong password")
    out = {}
    for giver, hexdata in payload["pairs"].items():
        data = bytes.fromhex(hexdata)
        out[giver] = bytes(a ^ b for a, b in zip(data, keystream(key, giver))).decode().strip()
    return out


def build(password, template="template.html", target="index.html"):
    payload = encrypt(draw(), password)
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, template)) as f:
        html = f.read()
    html = html.replace("/*__PAYLOAD__*/null", json.dumps(payload))
    with open(os.path.join(here, target), "w") as f:
        f.write(html)
    return payload


if __name__ == "__main__":
    pw = os.environ.get("SANTA_PASSWORD")
    if not pw:
        sys.exit("Set SANTA_PASSWORD")
    build(pw)
    print("index.html written (pairings encrypted, not shown).")
