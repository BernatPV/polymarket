import numpy as np
from scipy.optimize import minimize

# ────────────────────────────────────────────────
# Your provided matches: "home win draw lose" probabilities
# Format: (home_team, away_team, [p_win, p_draw, p_lose])

games = [
    ("atm", "bog", 0.765,  0.145, 0.095),
    ("ars", "kai", 0.9435, 0.041, 0.018),
    ("paf", "slp", 0.365,  0.295, 0.345),
    ("bru", "olm", 0.355,  0.255, 0.395),
    ("fcb", "kob", 0.865,  0.0875,0.0475),
    ("liv", "qar", 0.87,   0.091, 0.035),
    ("ben", "rma", 0.215,  0.225, 0.565),
    ("ath", "spo", 0.395,  0.275, 0.335),
    ("lev", "vil", 0.585,  0.225, 0.195),
    ("usg", "ata", 0.275,  0.255, 0.465),
    ("bvb", "int", 0.315,  0.275, 0.405),
    ("aja", "oly", 0.335,  0.255, 0.405),
    ("mnc", "gal", 0.805,  0.125, 0.075),
    ("asm", "juv", 0.285,  0.275, 0.445),
    ("nap", "cfc", 0.29,   0.265, 0.445),
    ("psv", "bay", 0.165,  0.195, 0.625),
    ("fra", "tot", 0.235,  0.235, 0.525),
    ("psg", "new", 0.635,  0.205, 0.165),
]
matches = [
    ('aja', 'oly', 2.83, 3.58, 2.39),
    ('ars', 'kai', 1.03, 19.45, 51.45),
    ('ath', 'spo', 2.74, 3.32, 2.60),
    ('atm', 'bog', 1.28, 6.60, 8.71),
    ('fcb', 'kob', 1.11, 10.14, 19.41),
    ('lev', 'vil', 1.70, 4.19, 4.47),
    ('ben', 'rma', 3.85, 4.07, 1.83),
    ('bru', 'olm', 2.71, 3.72, 2.43),
    ('bvb', 'int', 2.92, 3.51, 2.37),
    ('fra', 'tot', 4.18, 4.05, 1.77),
    ('liv', 'qar', 1.10, 11.29, 22.00),
    ('mnc', 'gal', 1.24, 7.01, 10.15),
    ('asm', 'juv', 4.16, 3.75, 1.84),
    ('nap', 'cfc', 3.39, 3.59, 2.10),
    ('paf', 'slp', 2.86, 3.45, 2.44),
    ('psg', 'new', 1.61, 4.65, 4.74),
    ('psv', 'bay', 5.13, 4.74, 1.55),
    ('usg', 'ata', 3.35, 3.66, 2.09),
]
matches += [
    ('ata', 'ath', 1.67, 3.75, 5.33),
    ('bay', 'usg', 1.12, 10.05, 17.45),
    ('cfc', 'paf', 1.11, 10.47, 20.05),
    ('juv', 'ben', 1.65, 3.85, 5.42),
    ('olm', 'liv', 3.69, 3.91, 1.90),
    ('new', 'psv', 1.30, 5.94, 8.56),
    ('slp', 'fcb', 7.80, 6.01, 1.33),
    ('gal', 'atm', 3.23, 3.67, 2.11),
    ('qar', 'fra', 3.33, 3.80, 2.05)
]
matches += [
    # FC Copenhagen / Napoli / Inter / Arsenal / etc.
    ('kob', 'nap', 3.92, 3.39, 2.00),
    ('int', 'ars', 2.73, 3.24, 2.66),
    ('oly', 'lev', 2.25, 3.56, 3.07),
    ('rma', 'asm', 1.30, 6.12, 8.50),
    ('spo', 'psg', 4.43, 4.18, 1.71),
    ('tot', 'bvb', 2.70, 3.51, 2.54),
    ('vil', 'aja', 1.34, 5.69, 7.63),
    ('bog', 'mnc', 6.47, 5.61, 1.39),
    ('kai', 'bru', 6.42, 4.86, 1.45),

    # Jornada següent
    ('ath', 'psg', 4.41, 3.90, 1.76),
    ('lev', 'new', 3.23, 3.71, 2.12),
    ('ben', 'nap', 2.76, 3.10, 2.73),
    ('bru', 'ars', 7.16, 5.12, 1.40),
    ('bvb', 'bog', 1.36, 5.61, 7.53),
    ('juv', 'paf', 1.18, 7.43, 15.45),
    ('rma', 'mnc', 3.18, 3.90, 2.09),
    ('qar', 'aja', 2.12, 3.73, 3.23),
    ('vil', 'kob', 1.40, 5.21, 6.77),

    # Atalanta / Barça / Inter / PSV / Tottenham
    ('ata', 'cfc', 3.42, 3.50, 2.12),
    ('fcb', 'fra', 1.14, 9.36, 14.56),
    ('int', 'liv', 2.01, 3.68, 3.56),
    ('psv', 'atm', 3.00, 3.73, 2.21),
    ('tot', 'slp', 1.43, 4.61, 7.55),

    # Monaco / Bayern / Olympiacos
    ('asm', 'gal', 1.94, 3.92, 3.59),
    ('usg', 'olm', 3.00, 3.46, 2.34),
    ('bay', 'spo', 1.22, 7.05, 11.41),
    ('kai', 'oly', 7.26, 4.68, 1.43),

    # Arsenal / Atleti / PSG / etc.
    ('ars', 'bay', 1.99, 3.62, 3.65),
    ('atm', 'int', 2.60, 3.40, 2.70),
    ('fra', 'ata', 2.82, 3.54, 2.42),
    ('liv', 'psv', 1.23, 7.29, 10.03),
    ('oly', 'rma', 4.68, 4.51, 1.63),
    ('psg', 'tot', 1.39, 4.90, 7.82),
    ('spo', 'bru', 1.50, 4.58, 6.03),
    ('kob', 'kai', 1.29, 5.45, 10.85),
    ('paf', 'asm', 6.42, 4.60, 1.48),

    # Darrera tanda
    ('bog', 'juv', 3.04, 3.65, 2.23),
    ('cfc', 'fcb', 2.15, 3.91, 3.03),
    ('bvb', 'vil', 1.94, 3.66, 3.80),
    ('mnc', 'lev', 1.36, 5.34, 8.01),
    ('olm', 'new', 3.04, 3.44, 2.33),
    ('nap', 'qar', 1.19, 7.04, 15.03),
    ('slp', 'ath', 3.05, 3.22, 2.42),
    ('aja', 'ben', 3.91, 3.58, 1.94),
    ('gal', 'usg', 1.74, 4.08, 4.28),
]
match_data = []
for team1,team2, win_odds, draw_odds, lose_odds in matches:
    if(team1=='atm' and team2=='bog'):
        print(win_odds, draw_odds, lose_odds)
        print(1/win_odds, 1/draw_odds, 1/lose_odds)
    pwin = 1 / win_odds
    plose = 1 / lose_odds
    match_data.append((team1,team2,pwin/(plose+pwin)))
from pprint import pprint
pprint(match_data)


# Extract all unique teams
teams = ['aja', 'ars', 'asm', 'ata', 'ath', 'atm', 'bay', 'ben', 'bog', 'bru', 'bvb', 'cfc', 'fcb', 'fra', 'gal', 'int', 'juv', 'kai', 'kob', 'lev', 'liv', 'mnc', 'nap', 'new', 'olm', 'oly', 'paf', 'psg', 'psv', 'qar', 'rma', 'slp', 'spo', 'tot', 'usg', 'vil']

print(teams)
n_teams = len(teams)
team_to_idx = {team: i for i, team in enumerate(teams)}



# ────────────────────────────────────────────────
# Model

def headsup(s_home, s_away, home_adv, T=6):
    diff = (s_home + home_adv - s_away) * T
    return 1 / (1 + np.exp(-diff))


def loss(params):
    # params = [strength_team0, strength_team1, ..., home_advantage]
    strengths = params[:-1]
    home_adv   = params[-1]
    
    total_loss = 0.0
    for home, away, target_p in match_data:
        i = team_to_idx[home]
        j = team_to_idx[away]
        p_model = headsup(strengths[i], strengths[j], home_adv)
        total_loss += (p_model - target_p) ** 2
    
    return total_loss


# ────────────────────────────────────────────────
# Initial guess: all strengths = 0, home adv = 0.3
initial_strengths = np.zeros(n_teams)
initial_home_adv  = np.array([0.3])
initial_params    = np.concatenate([initial_strengths, initial_home_adv])

# Bounds: strengths roughly [-3, 3], home adv [0, 2]
bounds = [(-3, 3)] * n_teams + [(0, 2)]

# Optimize
result = minimize(
    loss,
    initial_params,
    method='L-BFGS-B',
    bounds=bounds,
    options={'maxiter': 2000, 'disp': False}
)

# ────────────────────────────────────────────────
# Extract and normalize strengths to [0,1]
fitted_params = result.x
fitted_strengths = fitted_params[:-1]
fitted_home_adv      = fitted_params[-1]
"""
# Shift & scale to [0,1]
min_s = fitted_strengths_raw.min()
max_s = fitted_strengths_raw.max()
if max_s > min_s:
    fitted_strengths = (fitted_strengths_raw - min_s) / (max_s - min_s)
else:
    fitted_strengths = np.zeros_like(fitted_strengths_raw)
"""

# Build strength dictionary
strength = {teams[i]: round(float(fitted_strengths[i]), 3) for i in range(n_teams)}

print("Fitted HOME_ADVANTAGE_LOGIT =", round(fitted_home_adv, 3))
print("\nstrength = {")
for team, s in sorted(strength.items(), key=lambda x: -x[1]):
    print(f'    "{team}": {s},')
print("}")

print(f"\nOptimization success: {result.success}")
print(f"Final loss (sum of squared errors): {result.fun:.6f}")