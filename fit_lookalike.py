"""Estimate Bass model parameters for the look-alike innovation (BMW i3, 2013-2022).

Outputs:
    data/bass_parameters.csv
    data/i3_fitted_values.csv
    img/i3_bass_fit.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from helper_functions import (
    bass_period_adopters,
    fit_bass_nls,
    fit_bass_ols,
    peak_time,
    r_squared,
)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
IMG = ROOT / "img"


def main():
    i3 = pd.read_csv(DATA / "bmw_i3_sales.csv")
    years = i3["year"].to_numpy()
    t = np.arange(1, len(years) + 1)

    rows = []
    fitted = {"year": years}
    for scope, col in [("Europe", "europe_units"), ("Global", "global_units")]:
        sales = i3[col].to_numpy(dtype=float)

        nls, se = fit_bass_nls(sales)
        pred = bass_period_adopters(t, nls["p"], nls["q"], nls["M"])
        rows.append(
            {
                "scope": scope,
                "method": "NLS",
                "p": nls["p"],
                "q": nls["q"],
                "M": nls["M"],
                "se_p": se["p"],
                "se_q": se["q"],
                "se_M": se["M"],
                "r2": r_squared(sales, pred),
                "peak_year": years[0] - 1 + peak_time(nls["p"], nls["q"]),
            }
        )
        fitted[f"{scope.lower()}_actual"] = sales
        fitted[f"{scope.lower()}_nls"] = pred.round(0)

        ols = fit_bass_ols(sales)
        pred_ols = bass_period_adopters(t, ols["p"], ols["q"], ols["M"])
        rows.append(
            {
                "scope": scope,
                "method": "OLS (Bass 1969)",
                "p": ols["p"],
                "q": ols["q"],
                "M": ols["M"],
                "r2": r_squared(sales, pred_ols),
                "peak_year": years[0] - 1 + peak_time(ols["p"], ols["q"]),
            }
        )

    params = pd.DataFrame(rows)
    params.to_csv(DATA / "bass_parameters.csv", index=False, float_format="%.5f")
    pd.DataFrame(fitted).to_csv(DATA / "i3_fitted_values.csv", index=False)
    print(params.to_string(index=False))

    eu = params[(params.scope == "Europe") & (params.method == "NLS")].iloc[0]
    t_fine = np.linspace(0, len(years) + 6, 300)
    smooth = bass_period_adopters(t_fine + 1, eu.p, eu.q, eu.M)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(years, i3["europe_units"], color="#9fb8d6", label="Actual sales, Europe")
    ax.bar(years[-1], i3["europe_units"].iloc[-1], color="#d9d9d9", hatch="//",
           label="2022 (estimated)")
    ax.plot(years[0] + t_fine, smooth, color="#1c4e80", lw=2.2,
            label=f"Bass fit: p={eu.p:.4f}, q={eu.q:.3f}, M={eu.M:,.0f}")
    ax.set_title("BMW i3 annual sales in Europe and fitted Bass curve")
    ax.set_xlabel("Year")
    ax.set_ylabel("Units sold per year")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_xlim(years[0] - 0.7, years[-1] + 4)
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMG / "i3_bass_fit.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
