

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import numpy as np
import model
# from model import FIXED_ITERATIONS
from animal_params import ANIMAL_PARAMS


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------- Pydantic models -----------------
class SimulationConfig(BaseModel):
    
    animal_type: str

    sim_duration_months: int
    expand_ownership: bool = False
    # iterations: int =25

    # Female distribution
    init_female_total: int
    init_female_by_age: List[int]   # 👈 GENERIC

    # Male
    init_male_goats: int
    init_male_age: int

    # Parameters (overridable)
    t_preg_gap: int
    t_sell_min_male: int
    t_sell_min_female: int

    p_prod_start: float
    p_prod_end: float
    p_female_kid: float
    p_get_pregnant: float
    p_kids: List[float]
    p_sell_male: float
    p_sell_female: float
    death_probs: List[List[float]] = [] 


   
   
    


class SimulationResult(BaseModel):
    animal_type: str = "goat"   # NEW
    months: List[int]
    num_families: List[int]
    inactive_families: List[int]
    num_male: List[int]
    dead_male: List[int]
    num_female: List[int]
    dead_female: List[int]
    born_male: List[int]
    born_female: List[int]
    sold_male: List[int]      # new
    sold_female: List[int]      # new


# ----------------- Endpoint -----------------
@app.post("/simulate", response_model=SimulationResult)
async def run_simulation(config: SimulationConfig):
    print("Received payload:", config.dict(), flush=True)
    print("Simulation started")

    try:
        animal = config.animal_type.lower()
        if animal not in ANIMAL_PARAMS:
            raise HTTPException(status_code=400, detail="Invalid animal type")
        
        params = ANIMAL_PARAMS[animal].copy()
        params.update({
            'p_kids': config.p_kids,
            'p_get_pregnant': config.p_get_pregnant,
            'p_female_kid': config.p_female_kid,
            'p_sell_male': config.p_sell_male,
            'p_sell_female': config.p_sell_female,
            't_preg_gap': config.t_preg_gap,
            't_sell_min_male': config.t_sell_min_male,
            't_sell_min_female': config.t_sell_min_female,
            'death_probs': config.death_probs,
        })
        ANIMAL_PARAMS[animal] = params  # 👈 NOW PROPERLY DEDENTED
        
        model.expand_ownership = config.expand_ownership
        
        MAX_AGE = params["t_max_male"]
        female_ranges = params["female_age_ranges"]

        if len(config.init_female_by_age) != len(female_ranges):
            raise HTTPException(status_code=400, detail="Female age distribution length mismatch")

        # Build initial society
        s = model.Society(animal_type=animal)
        for count, (min_age, max_age) in zip(config.init_female_by_age, female_ranges):
            s.add_females_by_age_range(count, min_age, max_age)
        s.add_goats(is_female=False, count=config.init_male_goats, age=config.init_male_age)

        # Validations (shortened)
        if config.init_male_age > MAX_AGE or config.init_female_total < 0 or config.init_male_goats < 0:
            raise HTTPException(status_code=400, detail="Invalid initial counts/ages")
        if not np.isclose(sum(config.p_kids), 1.0):
            raise HTTPException(status_code=400, detail="Kids probabilities must sum to 1")
        if config.sim_duration_months <= 0:
            raise HTTPException(status_code=400, detail="Duration must be >0")

        # Build df
        df = pd.DataFrame({
            "female_by_age": [config.init_female_by_age],
            "M Goats": [config.init_male_goats],
            "M Ages": [config.init_male_age],
            "Months": [0],
        })
        print("Initial DF:\n", df, flush=True)

        # Run simulation (reduce iterations for speed)
        t_sim = config.sim_duration_months
        unique_months = np.array([0])
        res_agg = pd.DataFrame({k: np.zeros(t_sim + 1, dtype=int) 
                               for k in model.Society(animal_type=animal).stats.keys()})
        iter_count = 50  # 👈 Reduced from 30 to prevent timeout
        valid_iters = 0
        
        for i in range(iter_count):
            print(f"Running iteration {i+1}/{iter_count}", flush=True)
            ha, hi, ma, md, fa, fd, bm, bf, sm, sf = model.iterate_history_full(
                df, t_sim, unique_months, animal
            )
            if np.sum(fa) > 0:  # Only aggregate valid runs
                res_agg["num_families"] += ha
                res_agg["inactive_families"] += hi
                res_agg["num_male"] += ma
                res_agg["dead_male"] += md
                res_agg["num_female"] += fa
                res_agg["dead_female"] += fd
                res_agg["born_male"] += bm
                res_agg["born_female"] += bf
                res_agg["sold_male"] += sm
                res_agg["sold_female"] += sf
                valid_iters += 1
        
        res_agg = np.ceil(res_agg / max(valid_iters, 1)).astype(int)
        print("Simulation finished")
        
        return SimulationResult(
            animal_type=animal,
            months=list(range(t_sim + 1)),
            num_families=res_agg["num_families"].tolist(),
            inactive_families=res_agg["inactive_families"].tolist(),
            num_male=res_agg["num_male"].tolist(),
            dead_male=res_agg["dead_male"].tolist(),
            num_female=res_agg["num_female"].tolist(),
            dead_female=res_agg["dead_female"].tolist(),
            born_male=res_agg["born_male"].tolist(),
            born_female=res_agg["born_female"].tolist(),
            sold_male=res_agg["sold_male"].tolist(),
            sold_female=res_agg["sold_female"].tolist(),
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Simulation error: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))
    animal = config.animal_type.lower()
    if animal not in ANIMAL_PARAMS:
        raise HTTPException(status_code=400, detail="Invalid animal type")
    params = ANIMAL_PARAMS[animal] 
   


@app.get("/health")
def health_check():
    return {"status": "ok"}