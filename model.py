
import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from animal_params import ANIMAL_PARAMS

rng = np.random.default_rng()


expand_ownership = False      

### ESTIMATE THE MAXIMUM AGE OF A GOAT
def predict_max_age(is_female, current_age, animal_type):
    # params = ANIMAL_PARAMS[s.animal_type]
    params = ANIMAL_PARAMS[animal_type.lower()]  
    t_max_male = params['t_max_male']
    t_max_female = params['t_max_female']
    t_prod_start = params['t_prod_start']
    t_prod_end = params['t_prod_end']
    p_prod_start = params['p_prod_start']
    p_prod_end = params['p_prod_end']
    f_1 = lambda x: (((t_max_female - t_prod_end) / (0 - p_prod_start*p_prod_end)) * x) + t_max_female
    f_2 = lambda x: (((t_prod_end - t_prod_start) / (p_prod_start*p_prod_end - p_prod_start)) * (x - p_prod_start)) + t_prod_start
    f_3 = lambda x: (t_prod_start / (p_prod_start - 1)) * (x - 1)
    m_1 = lambda x: t_max_male * (1 - x)
    attempts=0
    while attempts < 1000:
        x = rng.uniform(0,1)
        t = m_1(x)
        if is_female:
            t = f_1(x) if x < p_prod_start*p_prod_end else (f_2(x) if x < p_prod_start else f_3(x))
        if t > current_age:
            return int(np.ceil(t))
        attempts +=1
    return params['t_max_female'] if is_female else params['t_max_male']

# WHAT IS A GOAT?
class Animal():
    def __init__(self, is_female, age, max_age, starts_new, animal_type="goat"):
        self.animal_type = animal_type.lower()
        self.is_female = is_female
        self.age = age
        self.max_age = max_age
        self.starts_new = starts_new

        self.is_alive = self.age <= self.max_age
        self.is_preg = False

        self.months_preg = 0
        self.last_birth_at = None

# FAMILY MEANS OWNER
class Family():
    def __init__(self):
        self.goats = []
        self.first_female_born = False

# SOCIETY IS A COLLECTION OF OWNERS
class Society():
    def __init__(self, animal_type="goat"):
        # self.config = config
        self.families = []
        self.animal_type = animal_type.lower()
        self.stats = {
            'num_families': 0,
            'inactive_families': 0,
            'num_male': 0,
            'dead_male': 0,
            'num_female': 0,
            'dead_female': 0,
            'born_male': 0,
            'born_female': 0,
            'sold_male': 0,
            'sold_female': 0,

            
        } 

    def add_goats(self, is_female=True, count=1, age=0):
        params = ANIMAL_PARAMS[self.animal_type.lower()]
        if expand_ownership:
            for _ in range(count):
                f = Family()
                max_age = predict_max_age(is_female, age, self.animal_type)
                f.goats.append( Animal(is_female, age, max_age, False, animal_type=self.animal_type) )
                self.families.append(f)
        else:
            if len(self.families) == 0:
                f = Family()
                f.first_female_born = True
                self.families.append(f)
            
            for _ in range(count):
                f = self.families[0]
                max_age = predict_max_age(is_female, age, self.animal_type)
                f.goats.append( Animal(is_female, age, max_age, False, animal_type=self.animal_type) )

        self.stats['num_families'] = len(self.families)
        if is_female:
            self.stats['num_female'] += count
        else:
            self.stats['num_male'] += count
    # def natural_death(self, animal: Animal):
    #    # """Determine if the animal dies naturally this month."""
    #     age = animal.age
    #     params = ANIMAL_PARAMS[animal.animal_type]

    #     # Death probability increases with age
    
    
    #     if age < 6:  # young animals
    #         death_prob = 0.03
    #     elif age < params["t_prod_start"]:
    #         death_prob = 0.01
    #     elif age < params["t_prod_end"]:
    #         death_prob = 0.005
    #     elif age < animal.max_age:
    #         death_prob = 0.02
    #     else:  # max age reached
    #         death_prob = 1.0

    #     return rng.random() < death_prob
    def natural_death(self, animal: Animal):
    # """Determine if the animal dies naturally this month using animal-specific death_probs."""
        params = ANIMAL_PARAMS[animal.animal_type]
        age = animal.age
    
    # Find matching age range from death_probs list
        for min_age, max_age, death_prob in params["death_probs"]:
            if min_age <= age < max_age:
                prob = death_prob
                break
        else:
        # Past last range or max_age reached
            prob = 1.0
    
        return rng.random() < prob

    
    def add_females_by_age_range(self, count, min_age, max_age):
        for _ in range(count):
            age = rng.integers(min_age, max_age + 1)
            self.add_goats(is_female=True, count=1, age=int(age))


    def next_month(self):
        params = ANIMAL_PARAMS[self.animal_type.lower()]
     
        if sum(len(f.goats) for f in self.families) > 50000:
            return  # Prevent explosion
        new_families_bucket = []
        dfam, dfem, dmal = 0, 0, 0
        
        for f in self.families:
            for g in f.goats:

                # New family dynamics
                if g.starts_new and g.age >= params["t_prod_start"]:
                    g.is_alive = False
                    new_families_bucket.append((g.age+1, g.max_age))
                    continue

                # Birthing dynamics
                if g.months_preg == params["t_preg_duration"]:
                    g.is_preg = False
                    g.months_preg = 0
                    g.last_birth_at = g.age

                    if self.animal_type in ["cow", "buffalo"]:
                        kids = 1
                    else:  # goat
                        kids = rng.choice(
                        np.arange(len(params["p_kids"])) + 1,
                        p=params["p_kids"]
                        )


                    for _ in range(kids):
                            
                        is_female = True if rng.uniform() < params["p_female_kid"] else False
                        max_age = predict_max_age(is_female, 0, self.animal_type)
                        starts_new = (not f.first_female_born) and is_female and (max_age > params["t_prod_start"])
                        f.goats.append( Animal(is_female, 0, max_age, starts_new, animal_type=g.animal_type.lower()) )
                        if starts_new: f.first_female_born = True
                        if is_female:
                            self.stats['born_female'] += 1
                        else:
                            self.stats['born_male'] += 1

                # Pregnancy dynamics
                if (not g.is_preg) and g.is_female and g.age >= params["t_prod_start"] and g.age < params["t_prod_end"] and ((g.last_birth_at is None) or (g.age - g.last_birth_at) >= params["t_preg_gap"]):
                    g.is_preg = True if rng.uniform() < params["p_get_pregnant"] else False
                if g.is_preg: g.months_preg += 1

                # # Selling dynamics (male)
                # if (not g.is_female) and g.age >= t_sell_min_male:
                #     g.is_alive = False if rng.uniform(0,1) < p_sell_male else True
                #     if not g.is_alive:
                #         self.stats['dead_male'] += 1
                #     continue
                # Selling dynamics (male)
                if (not g.is_female) and g.age >= params["t_sell_min_male"]:
                    if rng.uniform(0,1) < params["p_sell_male"]:
                        g.is_alive = False
                        self.stats['sold_male'] += 1   # <-- increment sold
                    continue  # sold goats are removed from population but NOT counted as dead


                # # Selling dynamics (female old)
                # if g.is_female and g.age >= t_sell_min_female:
                #     g.is_alive = False if rng.uniform(0,1) < p_sell_female else True
                #     if not g.is_alive:
                #         self.stats['dead_female'] += 1
                #     continue
                # Selling dynamics (female old)
                if g.is_female and g.age >= params["t_sell_min_female"]:
                    if rng.uniform(0,1) < params["p_sell_female"]:
                        g.is_alive = False
                        self.stats['sold_female'] += 1  # <-- increment sold
                    continue

                g.age += 1
                # Ageing and death dynamics
                # Ageing and death dynamics
                if self.natural_death(g):
                    g.is_alive = False
                    if g.is_female:
                        self.stats['dead_female'] += 1
                    else:
                        self.stats['dead_male'] += 1


            # Remove all the goats that died during this months
            f.goats = [g for g in f.goats if g.is_alive]

        a = len(self.families)
        self.families = [f for f in self.families if len(f.goats) > 0]
        b = len(self.families)
        self.stats['inactive_families'] = self.stats['inactive_families'] + (a-b)

        for j in new_families_bucket:
            f = Family()
            f.goats.append( Animal(True, j[0], j[1], False, self.animal_type.lower()) )
            self.families.append(f)

        self.stats['num_families'] = len(self.families)
        self.stats['num_male'] = sum([len([g for g in f.goats if not g.is_female]) for f in self.families])
        self.stats['num_female'] = sum([len([g for g in f.goats if g.is_female]) for f in self.families])

### Auxiliary Tools (I/O)
def delta_months(this, base):
    d = relativedelta(this,base)
    return d.months + 12*d.years

def read_data(datafile, sim_end_date=None):
    df = pd.read_csv(
        datafile,
        header=None,
        parse_dates=[0],
        names=["Date", "F Goats", "F Ages", "M Goats", "M Ages"],
        dtype={"F Goats": int, "F Ages": int, "M Goats": int, "M Ages": int},
        comment="#",
    )
    df["Date"] = pd.to_datetime(df["Date"])
    earliest_date = df["Date"].min()
    df["Months"] = df['Date'].apply( lambda x: delta_months(x, earliest_date) )
    months = np.sort(df['Months'].unique())
    df.drop('Date', axis=1, inplace=True)

    if sim_end_date is None:
        duration = None
    elif sim_end_date == 'today':
        duration = delta_months(date.today(), earliest_date)
    else:
        n = datetime.strptime(sim_end_date, '%Y-%m')
        duration = delta_months(n, earliest_date)

    return df, months, duration

### Auxiliary Tools (Running the simulation)
def iterate_history_full(df, duration, additions, animal_type):
    
    ha, hi, ma, md, fa, fd = np.zeros((6,duration+1), dtype=int)
    bm = np.zeros(duration + 1, dtype=int)
    bf = np.zeros(duration + 1, dtype=int)
    sm = np.zeros(duration+1, dtype=int) 
    sf = np.zeros(duration+1, dtype=int)
    s = Society(animal_type=animal_type.lower())
    
    for month in range(duration):
    
        if month in additions:
            
            a = df.loc[df['Months'] == month]
            
            for _ , row in a.iterrows():
                female_ranges = ANIMAL_PARAMS[animal_type]["female_age_ranges"]
                
                female_counts = row["female_by_age"]

                for count, (min_age, max_age) in zip(female_counts, female_ranges):
                     s.add_females_by_age_range(count, min_age, max_age)
               
                # Male goats (unchanged)
                s.add_goats(False, row["M Goats"], row["M Ages"])


        ha[month] = s.stats['num_families']
        hi[month] = s.stats['inactive_families']
        ma[month] = s.stats['num_male']
        md[month] = s.stats['dead_male']
        fa[month] = s.stats['num_female']
        fd[month] = s.stats['dead_female']
        bm[month] = s.stats['born_male']
        bf[month] = s.stats['born_female']
        sm[month] = s.stats['sold_male']
        sf[month] = s.stats['sold_female']


        s.next_month()

    ha[-1] = s.stats['num_families']
    hi[-1] = s.stats['inactive_families']
    ma[-1] = s.stats['num_male']
    md[-1] = s.stats['dead_male']
    fa[-1] = s.stats['num_female']
    fd[-1] = s.stats['dead_female']
    bm[-1] = s.stats['born_male']
    bf[-1] = s.stats['born_female']
    sm[-1] = s.stats['sold_male']
    sf[-1] = s.stats['sold_female']

    return ha, hi, ma, md, fa, fd, bm, bf , sm , sf 

def iterate_history_final(df, duration, additions, animal_type):
    ha, hi, ma, md, fa, fd , bm , bf, sm , sf  = 0, 0, 0, 0, 0, 0 , 0 ,0 ,0 ,0

    s = Society(animal_type=animal_type.lower())
   
    for month in range(duration):
        if month in additions:
            a = df.loc[df['Months'] == month]

            for _ , row in a.iterrows():
                female_ranges = ANIMAL_PARAMS[s.animal_type]["female_age_ranges"]
                
                female_counts = row["female_by_age"]

                for count, (min_age, max_age) in zip(female_counts, female_ranges):
                     s.add_females_by_age_range(count, min_age, max_age)

# Males
                s.add_goats(False, row["M Goats"], row["M Ages"])



        s.next_month()

    ha = s.stats['num_families']
    hi = s.stats['inactive_families']
    ma = s.stats['num_male']
    md = s.stats['dead_male']
    fa = s.stats['num_female']
    fd = s.stats['dead_female']
    bm = s.stats['born_male']
    bf = s.stats['born_female']
    sm = s.stats['sold_male']
    sf = s.stats['sold_female']
    

    return ha, hi, ma, md, fa, fd , bm , bf, sm , sf

### Auxiliary Tools (Running the simulation: final result)


