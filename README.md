# DS 223 Homework 1: Bass Model - BMW iX3 (Neue Klasse)

Innovation diffusion analysis of the **BMW iX3**, chosen from
[TIME's Best Inventions of 2025](https://time.com/collections/best-inventions-2025/7318539/bmw-ix3/).
The look-alike innovation is the **BMW i3** (2013-2022). Its sales history is used to estimate the Bass model parameters, which are then applied to forecast iX3 adoption in **Europe (EU + EFTA + UK)**.

The full report is in [`report/report.pdf`](report/report.pdf) (source: [`report/report_source.md`](report/report_source.md)).

## Key results

| | Value |
|---|---|
| Look-alike fit (BMW i3, Europe, NLS) | p = 0.0170, q = 0.471, M = 225,827, R² = 0.92 |
| iX3 market potential in Europe (Fermi, base) | M ≈ 677,500 (range 444,700-948,500) |
| Forecast (p calibrated on 100,000 first-year orders, q from i3) | peak ≈ 126,000 adopters in 2028; ≈ 651,000 cumulative by 2033 |

## Project structure

```
.
├── README.md
├── requirements.txt
├── helper_functions.py      # Bass model functions: F(t), f(t), NLS and OLS estimation, calibration
├── fit_lookalike.py         # Estimates p, q, M on BMW i3 sales (Europe and global)
├── forecast_ix3.py          # Fermi estimate of M and iX3 forecast scenarios + charts
├── build_report.py          # Builds report/report.html and report/report.pdf from the markdown source
├── data/
│   ├── bmw_i3_sales.csv                 # BMW i3 annual sales 2013-2022, global and Europe, with sources
│   ├── electric_car_sales_iea_owid.csv  # IEA Global EV Outlook electric car sales by region (via Our World in Data)
│   ├── fermi_inputs.csv                 # Inputs for the market potential, each with its source
│   ├── bass_parameters.csv              # Output: estimated p, q, M (NLS and OLS, Europe and global)
│   ├── i3_fitted_values.csv             # Output: actual vs fitted i3 sales
│   ├── ix3_market_potential.csv         # Output: low / base / high market potential
│   ├── ix3_scenarios.csv                # Output: parameters of each forecast scenario
│   └── ix3_forecast.csv                 # Output: new and cumulative adopters per year, 2026-2035
├── img/
│   ├── europe_ev_market.png             # European electric car sales 2010-2025
│   ├── i3_bass_fit.png                  # BMW i3 sales in Europe with the fitted Bass curve
│   ├── ix3_forecast_annual.png          # iX3 forecast: new adopters per year
│   └── ix3_forecast_cumulative.png      # iX3 forecast: cumulative adopters
└── report/
    ├── report_source.md                 # Report source (markdown)
    ├── report.html                      # Intermediate HTML
    └── report.pdf                       # Final report
```

## Setup and usage

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python fit_lookalike.py    # step 4: parameter estimation
python forecast_ix3.py     # steps 5-7: market potential, forecast, adopters by period
python build_report.py     # optional: rebuild the PDF (needs Google Chrome)
```

## Data sources

All numbers used in the analysis are referenced. The row-level sources are in the `source` columns of the CSV files in `data/`, and the full reference list (31 entries, including the academic papers on the Bass model) is at the end of the report.

## Use of AI tools

This project was prepared with the help of an AI coding assistant, used for data collection, code and drafting the report.
