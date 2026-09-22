from dataclasses import dataclass, field
from typing import List, Dict, Optional

MODE_PV = "pv"
MODE_ANNUAL = "annual"
MODE_SPREAD = "spread"
VALID_MODES = (MODE_PV, MODE_ANNUAL, MODE_SPREAD)

def normalize_mode(mode) -> str:
    if mode is True:
        return MODE_ANNUAL
    if mode is False:
        return MODE_PV
    m = str(mode).strip().lower()
    return m if m in VALID_MODES else MODE_PV

# DISCOUNTING
def discount_factor(rate: float, year: int) -> float: 
    """Returns the factor that converts a dollar in 'year' into today dollars."""
    return 1.0 / ((1.0 + rate) ** year)

MAX_YEARS = 30

def _horizon(year: int) -> int:
    """Benefits and costs stop accruing past the horizon."""
    return max(1, min(int(year), MAX_YEARS))

def annual_amount(total: float, years: int, mode: str) -> float:
    mode = normalize_mode(mode)
    if mode == MODE_SPREAD:
        n = max(1, int(years))
        return total / n
    return total

def present_value(total: float, rate: float, years: int, mode: str) -> float: 
    mode = normalize_mode(mode)
    if mode == MODE_PV:   # <--- Make sure this is the line with ==
        return total
    per_year == annual_amount(total, years, mode)
    last == _horizon(years)
    return sum(per_year * discount_factor(rate, t) for t in range(1, last + 1))

@dataclass
class CategoryResults:
    pv_benefits: float
    pv_costs: float
    bcr: Optional[float]
    npv: float
    benefit_by_category: Dict[str, float]
    cost_by_category: Dict[str, float]
    benefit_mode: str = MODE_PV
    cost_mode: str = MODE_PV
    schedule: List[dict] = field(default_factory=list)

def _sum_values(items: List[dict]) -> float:
    return sum(float(x.get("value") or 0.0) for x in items)

def build_schedule(benefits: List[dict], 
                   costs: List[dict], 
                   rate: float,
                   years: int,
                   benefit_mode: str,
                   cost_mode: str) -> List[dict]:
    """Builds the year-by-year table that drives everything else."""
    benefit_mode = normalize_mode(benefit_mode)
    cost_mode = normalize_mode(cost_mode)

    if benefit_mode == MODE_PV and cost_mode == MODE_PV:
        return []

    last = _horizon(years)

    ben_year = (0.0 if benefit_mode == MODE_PV else
                sum(annual_amount(float(b.get("value") or 0.0), years, benefit_mode)
                    for b in benefits))
    
    cost_year = (0.0 if cost_mode == MODE_PV else
                sum(annual_amount(float(c.get("value") or 0.0), years, cost_mode)
                    for c in costs))

    ben_up = _sum_values(benefits) if benefit_mode == MODE_PV else 0.0
    cost_up = _sum_values(costs) if cost_mode == MODE_PV else 0.0

    rows: List[dict] = []

    if ben_up or cost_up:
        rows.append({
            "year": 0,
            "factor": 1.0, 
            "benefits_nominal": ben_up,
            "benefits_pv": ben_up, 
            "costs_nominal": cost_up,
            "costs_pv": cost_up,
        })

    for t in range(1, last + 1):
        f = discount_factor(rate, t)
        rows.append({
            "year": t,
            "factor": f,
            "benefits_nominal": ben_year,
            "benefits_pv": ben_year * f,
            "costs_nominal": cost_year,
            "costs_pv": cost_year * f,
        })
    return rows

def run_categories(benefits: List[dict], 
                   costs: List[dict], 
                   rate: float,
                   years: int,
                   benefit_mode: str = MODE_PV,
                   cost_mode: str = MODE_PV) -> CategoryResults:
    benefit_mode = normalize_mode(benefit_mode)
    cost_mode = normalize_mode(cost_mode)

    pv_ben = 0.0
    pv_costs = 0.0 
    ben_by_cat: Dict[str, float] = {}
    cost_by_cat: Dict[str, float] = {}

    for b in benefits:
        v = present_value(float(b.get("value") or 0.0), rate, years, benefit_mode)
        pv_ben += v
        cat = b.get("category", "other")
        ben_by_cat[cat] = ben_by_cat.get(cat, 0.0) + v

    for c in costs:
        v = present_value(float(c.get("value") or 0.0), rate, years, cost_mode)
        pv_costs += v
        cat = c.get("category", "other")
        cost_by_cat[cat] = cost_by_cat.get(cat, 0.0) + v

    bcr = (pv_ben / pv_costs) if pv_costs > 0 else None
    npv = pv_ben - pv_costs
    
    schedule = build_schedule(benefits, costs, rate, years, benefit_mode, cost_mode)                      

    return CategoryResults(
        pv_benefits=pv_ben, 
        pv_costs=pv_costs,
        bcr=bcr,
        npv=npv,
        benefit_by_category=ben_by_cat,
        cost_by_category=cost_by_cat,
        benefit_mode=benefit_mode,
        cost_mode=cost_mode,
        schedule=schedule,
    )
