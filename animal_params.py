ANIMAL_PARAMS = {
    "goat": {
        "t_max_male": 144,
        "t_max_female": 144,
        "t_prod_start": 7,
        "t_prod_end": 120,
        "t_preg_duration": 6,
        "t_sell_min_male": 12,
        "t_sell_min_female": 120,
        "p_kids": [0.45, 0.45, 0.10],
        "p_get_pregnant": 0.85,
        "p_prod_start" : 0.90,             # Probability that the female goat survives until t_prod_start
        "p_prod_end" : 0.85,               # Probability that the female goat survives until t_prod_end
        "p_female_kid" : 0.50,             # Probability that a new born kid is a female
        "p_sell_male" : 0.95,              # Probability of being sold (in a given month) for male goats over the age of t_sell_min_male
        "p_sell_female" : 0.95,
        "t_preg_gap" : 7, 
        "female_age_ranges": [(1, 7), (7, 120), (120, 144)],
        "death_probs": [
            (0, 6, 0.03),     # kids
            (6, 12, 0.01),    # young
            (12, 120, 0.005), # adult
            (120, 144, 0.10)  # old
        ],            # Probability of being sold (in a given month) for female goats over the age
    },
    "cow": {
        "t_max_male": 240,
        "t_max_female": 240,
        "t_prod_start": 18,
        "t_prod_end": 180,
        "t_preg_duration": 9,
        "t_sell_min_male": 24,
        "t_sell_min_female": 180,
        "p_kids": [0.95, 0.05],
        "p_get_pregnant": 0.85,
        "p_prod_start" : 0.90,             # Probability that the female goat survives until t_prod_start
        "p_prod_end" : 0.85,               # Probability that the female goat survives until t_prod_end
        "p_female_kid" : 0.50,             # Probability that a new born kid is a female
        "p_sell_male" : 0.95,              # Probability of being sold (in a given month) for male goats over the age of t_sell_min_male
        "p_sell_female" : 0.95,
        "t_preg_gap" : 10,  
        "female_age_ranges": [(1, 18), (18, 180), (180, 240)],
        "death_probs": [
            (0, 12, 0.02),
            (12, 18, 0.01),
            (18, 180, 0.003),
            (180, 240, 0.08)
        ]  
    },
    "buffalo": {
        "t_max_male": 300,
        "t_max_female": 300,
        "t_prod_start": 30,
        "t_prod_end": 220,
        "t_preg_duration": 11,
        "t_sell_min_male": 30,
        "t_sell_min_female": 220,
        "p_kids": [0.98, 0.02],
        "p_get_pregnant": 0.80,
        "p_prod_start" : 0.90,             # Probability that the female goat survives until t_prod_start
        "p_prod_end" : 0.85,               # Probability that the female goat survives until t_prod_end
        "p_female_kid" : 0.50,             # Probability that a new born kid is a female
        "p_sell_male" : 0.95,              # Probability of being sold (in a given month) for male goats over the age of t_sell_min_male
        "p_sell_female" : 0.95,
        "t_preg_gap" : 10,    
        "female_age_ranges": [(1, 30), (30, 220), (220, 300)],
        "death_probs": [
            (0, 18, 0.02),
            (18, 30, 0.01),
            (30, 220, 0.003),
            (220, 300, 0.07)
        ],
    }
}