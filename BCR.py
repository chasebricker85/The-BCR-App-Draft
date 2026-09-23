"""
shell_streamlit_app_full.py
A streamlit version of the BCR Model
"""
import streamlit as st 
import pandas as pd
import plotly.graph_objects as go

from shell_bcr_full_three import run_categories, present_value

st.set_page_config(page_title="IML Research Benefit-Cost Model-Shell with Categories", 
                   page_icon="chart_with_upwards_trend", layout="wide")

st.title("IML Research Benefit-Cost Model Shell with Categories")
st.caption("Enter one total for each benefit-cost category for research return on investment. Any cost figure is a placeholder.")

#BENEFITS
BENEFIT_CATEGORIES = [
    ("maintenance", "Reduction in lifecycle maintenance and rehabilitation costs", 
     "agency", "Lower upkeep and fewer rehabilitations over the asset life."), 
    ("durability", "Improved durability and extended service life", 
     "agency", "The value of postponing replacement through longer life."), 
    ("safety", "Safety", 
     "user", "Fewer crashes, injuries and fatalities, at published values."), 
    ("traffic", "Traffic reduction", 
     "user", "Reduced delay and congestion, e.g. from shorter work zones."), 
    ("commercialization", "Commercialization", 
     "other", "Royalties and producer surplus from a method brought to market."), 
]

COST_CATEGORIES = [
    ("rd", "Research and Development", 
     "research", "The cost of the research itself."),
     ("deployment", "Deployment and Dissemination", 
      "deployment", "Outreach, training, technology transfer, support."),
]


ENTRY_MODES = [
    ("pv", "A lump sum in today's dollars",
    "Used exactly as entered, with no discounting."),
    ("annual", "A recurring amount every year",
        "A yearly amount that recurs for the whole horizon; each year is "
        "discounted and the years are summed." ),
    ("spread", "One lump sum spread over the horizon", 
     "One total for the whole horizon, divided by the number of years and "
     "then discounted year by year."),
]

MODE_LABEL = [m[1] for m in ENTRY_MODES]

def mode_from_label(label: str) -> str: 
    return next(m[0] for m in ENTRY_MODES if m[1] == label)

def amount_noun(mode: str) -> str: 
    return {
        "pv": "lump sum in today's dollars",
        "annual": "amount per year",
        "spread": "lump sum for the whole horizon"
    }[mode]

def describe_mode(mode: str, side: str) -> str:
    return {
        "pv": f"{side} are one-time lump sums, used as entered.",
        "annual": f"{side} are a yearly amount, discounted over the horizon.", 
        "spread": f"{side} are one lump sum spread across the horizon and discounted.",
    }[mode]

#PARAMETERS
with st.sidebar:
    st.header("Analysis parameters")

    b_choice = st.selectbox("Benefit totals are entered as:", MODE_LABEL, index=0)
    benefit_mode = mode_from_label(b_choice)

    c_choice = st.selectbox(
        "Cost totals are entered as:", MODE_LABEL, index=0,
        help="Research and deployment money is usually spent up front, so this "
            "starts on the one-time lump sum. Change it only if cost really "
            "recurs or is spread across the horizon."
    )
    cost_mode = mode_from_label(c_choice)

    st.caption(describe_mode(benefit_mode, "Benefits") + " " + describe_mode(cost_mode, "Costs"))

    discount_rate = st.number_input(
        "Real discount rate", min_value=0.0, max_value=0.15, value=0.035, step=0.001, format="%.3f", 
        help="OMB Circular A-94 is 3.1 percent. OMB also reinstated a 7 "
            "percent rate in 2025; run both and state which governs.")

    horizon_years = st.slider("Analysis horizon (years)", 1, 20, 30, 
                              help="Used to discount annual amounts and to "
                                "express the annualized figure.")


def pv_benefit(value) -> float:
    return present_value(float(value or 0.0), float(discount_rate),
                         int(horizon_years), benefit_mode)

def pv_cost(value) -> float:
    return present_value(float(value or 0.0), float(discount_rate), 
                         int(horizon_years), cost_mode)


#Inputs in two columns
st.header("Benefits")
st.caption(f"One {amount_noun(benefit_mode)} per category. Leave a category at zero if it does not apply.")

benefit_values = {}
bcols = st.columns(2)
for i, (key, label, cat, helptext) in enumerate(BENEFIT_CATEGORIES):
    col = bcols[i % 2]
    default = {
        "maintenance": 8_000_000.0,
        "durability": 6_000_000.0,
        "safety": 3_000_000.0,
        "traffic": 2_000_000.0,
        "commercialization": 0.0,
    }.get(key, 0.0)

    benefit_values[key] = col.number_input(
        label, min_value=0.0, value=default, step=100_000.0,
        format="%.0f", help=helptext, key=f"ben_{key}"
    )



st.header("Costs")
st.caption(f"One {amount_noun(cost_mode)} per category.")
cost_values = {}
ccols = st.columns(2)
for i, (key, label, cat, helptext) in enumerate(COST_CATEGORIES):
    col = ccols[i % 2]
    default = {
        "rd": 5_000_000.0, "deployment": 2_000_000.0, 
    }.get(key, 0.0)
    
    # FIXED: Indented this so it runs inside the loop for every category!
    cost_values[key] = col.number_input(
        label, min_value=0.0, value=default, step=100_000.0, 
        format="%.0f", help=helptext, key=f"cost_{key}")

#CATEGORY TOTALS

def collect():
    benefits = [
        dict(value=float(benefit_values.get(key) or 0.0), category=cat)
        for (key, label, cat, _) in BENEFIT_CATEGORIES
    ] 

    costs = [
        dict(value=float(cost_values.get(key) or 0.0), category=cat)
        for (key, label, cat, _) in COST_CATEGORIES
    ]
    return benefits, costs

benefits, costs = collect()
result = run_categories(
    benefits, costs,
    rate=float(discount_rate), 
    years=int(horizon_years),
    benefit_mode=benefit_mode,
    cost_mode=cost_mode
)

#RESULTS
st.divider()
st.header("Results")

m1, m2 = st.columns(2)
m1.metric("Benefit-cost ratio", f"{result.bcr: .2f} to 1" if result.bcr is not None else "Undefined")
m2.metric("Net present value", f"${result.npv:,.0f}")

if result.bcr is None:
    st.warning("The ratio is undefined because total costs are zero. A ratio "
               "with no cost is not infinite.")

st.divider()

left, right = st.columns([1, 1])

with left: 
    st.subheader ("Benefits entered")
    brows = [
        (label, benefit_values[key], pv_benefit(benefit_values[key]))
        for key, label, _, _ in BENEFIT_CATEGORIES
    ]
    bdf = pd.DataFrame(brows, columns=["Benefit category", "Entered", "Present value"])
    tot_entered = bdf["Entered"].sum()
    tot_pv = bdf["Present value"].sum()
    bdf["Entered"] = bdf["Entered"].map(lambda v: f"${v:,.0f}")
    bdf["Present value"] = bdf["Present value"].map(lambda v: f"${v:,.0f}")
    bdf.loc[len(bdf)] = ["Total benefits", f"${tot_entered:,.0f}", f"${tot_pv:,.0f}"]
    st.dataframe(bdf, use_container_width=True, hide_index=True)
    st.caption(f"Present value of benefits: ${result.pv_benefits:,.0f}")

with right: 
    st.subheader("Costs entered")
    crows=[
        (label, cost_values[key], pv_cost(cost_values[key]))
        for key, label, _, _ in COST_CATEGORIES
    ]
    cdf = pd.DataFrame(crows, columns=["Cost category", "Entered", "Present value"])
    tot_entered = cdf["Entered"].sum()
    tot_pv = cdf["Present value"].sum()
    cdf["Entered"] = cdf["Entered"].map(lambda v: f"${v:,.0f}")
    cdf["Present value"] = cdf["Present value"].map(lambda v: f"${v:,.0f}")
    cdf.loc[len(cdf)] = ["Total costs", f"${tot_entered:,.0f}", f"${tot_pv:,.0f}"]
    st.dataframe(cdf, use_container_width=True, hide_index=True)
    st.caption(f"Present value of costs: ${result.pv_costs:,.0f}")

if result.schedule:
    st.divider()
    st.subheader("Value by year")

    n = int(horizon_years)
    entered_b = sum(benefit_values.values())
    entered_c = sum(cost_values.values())

    def side_note(mode, entered, label):
        if mode == "pv":
            return f"{label}: ${entered:,.0f} one-time, shown at year 0."
        if mode == "spread":
                return (f"{label}: ${entered:,.0f} spread over {n} years is "
                        f"${entered/max(1, n):,.0f} a year, discounted below.")
        return f"{label}: ${entered:,.0f} a year, discounted below."

    st.caption(side_note(benefit_mode, entered_b, "Benefits") + " " + side_note(cost_mode, entered_c, "Costs"))

    srows = [{
        "Year": row["year"],
        "Discount factor": f'{row["factor"]:.4f}',
        "Benefits (nominal)": f'${row["benefits_nominal"]:,.0f}',
        "Benefits (present value)": f'${row["benefits_pv"]:,.0f}',
        "Costs (nominal)": f'${row["costs_nominal"]:,.0f}',
        "Costs (present value)": f'${row["costs_pv"]:,.0f}',
    } for row in result.schedule]

    st.dataframe(pd.DataFrame(srows), use_container_width=True, hide_index=True)

    nom_b = sum(r["benefits_nominal"] for r in result.schedule)
    nom_c = sum(r["costs_nominal"] for r in result.schedule)
    st.caption(
        f"Nominal totals: ${nom_b:,.0f} of benefits and ${nom_c:,.0f} of "
        f"costs. Discounted, these are the present values above: "
        f"${result.pv_benefits:,.0f} and ${result.pv_costs:,.0f}."
    )

#VISUALS

NAVY="#1F3864"; BLUE="#2E75B6"; GREEN="#1E6B3C"; RED="#C0392B"; ORANGE="#C0560B"; GREY="#8C8C8C"; LIGHTISH="#D9E2EC"
BASE=dict(font=dict(family="Arial, sans-serif", size=13, color="#31333F"), 
          plot_bgcolor="white", paper_bgcolor="white")

st.divider()
st.subheader("Visuals")


vt1, vt2, vt3, vt4 = st.tabs(
    ["Ratio gauge", 
     "Benefits vs Costs",
     "Payback year",
     "Waterfall"]
)

#VISUAL gauge
with vt1: 
    if result.bcr is not None:
        g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=result.bcr,
            number=dict(suffix=" to 1", font=dict(size=44, color=NAVY)),
            gauge=dict(
                axis=dict(range=[0, max(8, result.bcr * 1.25)],
                    tickwidth=1, tickcolor=GREY),
                bar=dict(color=NAVY, thickness=0.75),
                steps=[dict(range=[0, 1], color="#F5B7B1"),
                       dict(range=[1,3], color="#FCF3CF"), 
                       dict(range=[3, max(8, result.bcr * 1.25)], color="#D5F5E3"),
                       ],
                       threshold=dict(line=dict(color=RED, width=4),
                                      thickness=0.85, value=1.0))))    
        g.update_layout(**BASE, height=340,
                        title=dict(text="Benefit-Cost ratio against break-even", 
                                    font=dict(size=16, color=NAVY)))
        st.plotly_chart(g, use_container_width=True)
        verdict = ("below break-even: the program returns less than it cost"
                   if result.bcr < 1 else
                   "above break-even: the program returns more than it cost")
        st.caption(f"The needle is the ratio; the red line is break-even at 1.0. "
                   f"Red below 1, amber from 1 to 3, green above 3. "
                   f"This result is {verdict}.")
    else:
        st.warning("The ratio is undefined because total costs are zero, so"
                   "there is nothing for the gauge to show. Enter a cost to get a ratio.")

#Benefits vs Costs stacked
with vt2:
    ben_rows = [
        (label, pv_benefit(benefit_values[key]))
            for key, label, _, _ in BENEFIT_CATEGORIES if benefit_values[key] > 0]
    cost_rows = [(label, pv_cost (cost_values[key]))
            for key, label, _, _ in COST_CATEGORIES if cost_values[key] > 0]

    fig = go.Figure()
    for label, val in ben_rows:
        fig.add_trace(go.Bar(name=label, x=["Benefits"], y=[val]))
    for label, val in cost_rows:
        fig.add_trace(go.Bar(name=label, x=["Costs"], y=[val]))

    fig.update_layout(BASE)


    fig.update_layout(
            barmode="stack", 
            height=440,
            title=dict(text="Benefits and costs, by component."),
            font=dict(size=16, color=NAVY),
            yaxis=dict(title="Present value (dollars)", gridcolor=LIGHTISH),
            legend=dict(orientation="v", x=1.02, y=1))
      
    st.plotly_chart(fig, use_container_width=True, theme=None)
    tot_b = result.pv_benefits
    tot_c = result.pv_costs
    st.caption(f"Two stacked columns to the same scale: ${tot_b:,.0f} of "
               f"benefits against ${tot_c:,.0f} of costs. The height "
               f"difference is the net present value.")

"""EXTRA VISUALS WE CAN USE OR NOT USE DEPENDING"""
#--- PAYBACK TAB (vt3) ---
with vt3:
    """
    Cumulative attributed benefit against total cost, with the crossover marked.

    The year the benefit line passes the cost line is the payback year, and it
    is a figure people grasp immediately even when a ratio leaves them cold.
    """
    FIRST_YEAR = None

    def _payback_year(res):
        total_cost = res.pv_costs
        if total_cost <= 0:
            return None
        if not res.schedule:
            return 0 if res.pv_benefits >= total_cost else None
        
        cum_b = 0.0
        for row in res.schedule:
            cum_b += row["benefits_pv"]
            if cum_b >= total_cost:
                return row["year"]
        return None

    py = _payback_year(result)
    
    if py is None:
        shown = "Not within horizon"
    elif FIRST_YEAR is not None:
        shown = str(FIRST_YEAR + max(0, py - 1))
    else:
        shown = f"Year {py}"
    st.metric("Payback year", shown)

    if result.schedule:
        years = [r["year"] for r in result.schedule]
        cum_b, running = [], 0.0
        for r in result.schedule:
            running += r["benefits_pv"] * multiplier
            cum_b.append(running)
            
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years, y=cum_b, mode="lines", 
            line=dict(color=GREEN, width=3),        
            name="Cumulative benefits"
        ))
        fig.add_hline(y=result.pv_costs, line=dict(color=ORANGE, width=2, dash="dot"))
        
        if py is not None and py >= 1:
            fig.add_vline(x=py, line=dict(color=NAVY, width=2, dash="dash"))
            
        fig.update_layout(
            **BASE, height=380, showlegend=False, 
            title=dict(
                text="Payback: cumulative benefit vs total cost", 
                font=dict(size=16, color=NAVY)
            ), 
            xaxis=dict(title="Year", gridcolor=LIGHTISH), 
            yaxis=dict(title="Cumulative present value of benefits (dollars)", gridcolor=LIGHTISH)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            f"The green line is cumulative discounted benefit. The dotted orange line is total "
            f"cost (${result.pv_costs:,.0f}). Payback is the year the green line rises past it."
        )
    else: 
        st.caption(
            "Payback needs benefits that arrive over time. In lump-sum mode everything lands at "
            "year 0, so there is no year-by-year payback to trace. Set benefits to a recurring or " 
            "spread mode to see it."
        )

#---WATERFALL TAB (vt4) ---
with vt4:
        b = result.pv_benefits
        c = result.pv_costs
        fig = go.Figure(go.Waterfall(
            orientation="v", 
            measure=["absolute", "relative", "totals"],
            x=["Present value<br>of benefits", "Less: costs", "Net present<br>value"],
            y=[b, -c, None],
            text=[f"${b:,.0f}", f"-${c:,.0f}", f"${b - c:,.0f}"],
            textposition="outside", 
            connector=dict(line=dict(color=GREY, width=1)),
            increasing=dict(marker=dict(color=BLUE)),
            decreasing=dict(marker=dict(color=ORANGE)),
            totals=dict(marker=dict(color=GREEN))))
        fig.update_layout(**BASE, height=400, showlegend=FALSE, 
                          title=dict(text="How the result is built",
    font=dict(size=16, color=NAVY)),
                        yaxis=dict(title="Present value (dollars)",
                                   gridcolor=LIGHTISH))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"The benefit total, the cost total taken out of it, and the net present value that "
                   f"remains. ${b:,.0f} minus ${c:,.0f} is ${b - c:,.0f}.") 




