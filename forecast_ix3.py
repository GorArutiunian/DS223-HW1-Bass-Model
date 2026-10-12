"""Forecast the diffusion of the BMW iX3 (Neue Klasse) in Europe with the Bass model.

Uses p and q estimated on the BMW i3 (fit_lookalike.py) and a Fermi estimate of the
market potential M built from data/fermi_inputs.csv.

Outputs:
    data/ix3_market_potential.csv
    data/ix3_forecast.csv
    img/europe_ev_market.png
    img/ix3_forecast_annual.png
    img/ix3_forecast_cumulative.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from helper_functions import (
    bass_cumulative_share,
    bass_period_adopters,
    calibrate_p,
    peak_time,
)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
IMG = ROOT / "img"

LAUNCH_YEAR = 2026
HORIZON = 10  # 2026-2035


def market_potential(inputs):
    """Fermi estimate of lifetime iX3 adopters in Europe (low / base / high)."""
    bmw_europe = inputs["bmw_group_europe_deliveries_2025"]
    bev_share = inputs["bmw_group_europe_bev_share_2025"]
    ix3_share = inputs["ix3_share_of_bmw_bev_orders_europe"]
    life = inputs["model_life_cycle_years"]

    cases = {
        "low": dict(bev_share=bev_share, ix3_share=0.25, years=life - 1),
        "base": dict(bev_share=bev_share, ix3_share=ix3_share, years=life),
        "high": dict(bev_share=0.35, ix3_share=ix3_share, years=life),
    }
    rows = []
    for name, c in cases.items():
        annual = bmw_europe * c["bev_share"] * c["ix3_share"]
        rows.append(
            {
                "case": name,
                "bmw_group_europe_sales": bmw_europe,
                "bmw_bev_share": c["bev_share"],
                "ix3_share_of_bmw_bev": round(c["ix3_share"], 4),
                "ix3_annual_volume": round(annual),
                "life_cycle_years": c["years"],
                "M": round(annual * c["years"]),
            }
        )
    return pd.DataFrame(rows).set_index("case")


def plot_europe_ev_market():
    ev = pd.read_csv(DATA / "electric_car_sales_iea_owid.csv")
    eu = ev[ev["entity"] == "Europe"].sort_values("year")

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar(eu["year"], eu["ev_sales"] / 1e6, color="#7aa6c2")
    for year, label in [(2013, "BMW i3 launch"), (2025, "BMW iX3 premiere")]:
        val = eu.loc[eu["year"] == year, "ev_sales"].iloc[0] / 1e6
        ax.annotate(f"{label}\n{val * 1e6:,.0f} EVs sold", xy=(year, val),
                    xytext=(year - 0.2, val + 0.9), ha="center", fontsize=9,
                    arrowprops=dict(arrowstyle="->", color="#444"))
    ax.set_title("New electric car sales in Europe (BEV + PHEV), 2010-2025")
    ax.set_ylabel("Million cars")
    ax.set_ylim(0, 6)
    ax.grid(axis="y", alpha=0.3)
    fig.text(0.01, 0.01, "Source: IEA Global EV Outlook, via Our World in Data",
             fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(IMG / "europe_ev_market.png", dpi=200)
    plt.close(fig)
    return eu


def main():
    params = pd.read_csv(DATA / "bass_parameters.csv")
    eu = params[(params.scope == "Europe") & (params.method == "NLS")].iloc[0]
    p_analog, q = eu.p, eu.q

    inputs = pd.read_csv(DATA / "fermi_inputs.csv").set_index("parameter")["value"]
    M_table = market_potential(inputs)
    M_table.to_csv(DATA / "ix3_market_potential.csv")
    print(M_table.to_string(), "\n")

    first_year_orders = inputs["ix3_europe_orders_first_year"]
    capacity = inputs["debrecen_plant_capacity"]

    t = np.arange(1, HORIZON + 1)
    years = LAUNCH_YEAR - 1 + t
    forecast = pd.DataFrame({"year": years, "period": t})

    M_base = M_table.loc["base", "M"]
    forecast["A_analog_new"] = bass_period_adopters(t, p_analog, q, M_base)

    p_cal = {}
    for case in ["low", "base", "high"]:
        M = M_table.loc[case, "M"]
        p_cal[case] = calibrate_p(first_year_orders, q, M)
        forecast[f"B_{case}_new"] = bass_period_adopters(t, p_cal[case], q, M)

    for col in [c for c in forecast.columns if c.endswith("_new")]:
        forecast[col.replace("_new", "_cumulative")] = forecast[col].cumsum()
    forecast = forecast.round(0)
    forecast.to_csv(DATA / "ix3_forecast.csv", index=False)

    summary = pd.DataFrame(
        [
            {"scenario": "A: analog (i3 p, q)", "p": p_analog, "q": q, "M": M_base,
             "peak_year": LAUNCH_YEAR - 1 + peak_time(p_analog, q)},
            *[
                {"scenario": f"B: calibrated, M {case}", "p": p_cal[case], "q": q,
                 "M": M_table.loc[case, "M"],
                 "peak_year": LAUNCH_YEAR - 1 + max(peak_time(p_cal[case], q), 0)}
                for case in ["low", "base", "high"]
            ],
        ]
    )
    summary.to_csv(DATA / "ix3_scenarios.csv", index=False, float_format="%.4f")
    print(summary.to_string(index=False), "\n")
    print(forecast.to_string(index=False))

    plot_europe_ev_market()

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.fill_between(years, forecast["B_low_new"], forecast["B_high_new"],
                    color="#f4a259", alpha=0.25, label="Scenario B range (M low to high)")
    ax.plot(years, forecast["B_base_new"], "o-", color="#d1495b", lw=2,
            label="Scenario B: calibrated p, base M")
    ax.plot(years, forecast["A_analog_new"], "s--", color="#1c4e80", lw=2,
            label="Scenario A: i3 parameters, base M")
    ax.axhline(capacity, color="#555", ls=":", lw=1.3)
    ax.text(years[0], capacity * 1.02, "Debrecen plant capacity (all markets)",
            ha="left", va="bottom", fontsize=8, color="#555")
    ax.set_title("BMW iX3 in Europe: forecast new adopters per year")
    ax.set_xlabel("Year")
    ax.set_ylabel("New adopters (cars sold)")
    ax.set_xticks(years)
    ax.set_ylim(0, capacity * 1.15)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.legend(frameon=False, loc="upper right", bbox_to_anchor=(1, 0.86))
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMG / "ix3_forecast_annual.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.fill_between(years, forecast["B_low_cumulative"], forecast["B_high_cumulative"],
                    color="#f4a259", alpha=0.25, label="Scenario B range")
    ax.plot(years, forecast["B_base_cumulative"], "o-", color="#d1495b", lw=2,
            label="Scenario B: base")
    ax.plot(years, forecast["A_analog_cumulative"], "s--", color="#1c4e80", lw=2,
            label="Scenario A: base")
    ax.axhline(M_base, color="#555", ls=":", lw=1.3)
    ax.text(years[0], M_base * 1.02, f"Base market potential M = {M_base:,.0f}",
            fontsize=8, color="#555")
    ax.set_title("BMW iX3 in Europe: forecast cumulative adopters")
    ax.set_xlabel("Year")
    ax.set_ylabel("Cumulative adopters")
    ax.set_xticks(years)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMG / "ix3_forecast_cumulative.png", dpi=200)
    plt.close(fig)

    share_by_2033 = bass_cumulative_share(2033 - LAUNCH_YEAR + 1, p_cal["base"], q)
    print(f"\nScenario B base: {share_by_2033:.1%} of M adopted by end of 2033")


if __name__ == "__main__":
    main()
