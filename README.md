# Secret Santa 2026

Password-protected Secret Santa draw. Open the site, enter the password, pick your own name and see who you give a gift to.

The full assignment is drawn once (uniformly at random among all assignments that obey the rules) by `draw.py` and stored in `index.html` encrypted with the password, so nobody, including whoever published it, sees the pairings.

- Rebuild with a fresh draw: `SANTA_PASSWORD='...' python3 draw.py`
- Run the rule tests: `python3 test_draw.py 10`
