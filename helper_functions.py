"""Helper functions for the Bass diffusion model."""

import numpy as np
from scipy.optimize import brentq, curve_fit


def bass_cumulative_share(t, p, q):
    """F(t): share of the market potential that has adopted by time t."""
    e = np.exp(-(p + q) * np.asarray(t, dtype=float))
    return (1 - e) / (1 + (q / p) * e)


def bass_density(t, p, q):
    """f(t): instantaneous adoption rate (continuous Bass density)."""
    e = np.exp(-(p + q) * np.asarray(t, dtype=float))
    return ((p + q) ** 2 / p) * e / (1 + (q / p) * e) ** 2


def bass_period_adopters(t, p, q, M):
    """New adopters in period t, i.e. M * [F(t) - F(t-1)], with t = 1, 2, ..."""
    t = np.asarray(t, dtype=float)
    return M * (bass_cumulative_share(t, p, q) - bass_cumulative_share(t - 1, p, q))


def fit_bass_nls(sales, p0=0.03, q0=0.38, m0=None):
    """Estimate p, q, M by non-linear least squares (Srinivasan & Mason, 1986).

    Returns (params, standard_errors) as dicts.
    """
    sales = np.asarray(sales, dtype=float)
    t = np.arange(1, len(sales) + 1)
    total = sales.sum()
    if m0 is None:
        m0 = 1.2 * total
    popt, pcov = curve_fit(
        bass_period_adopters,
        t,
        sales,
        p0=[p0, q0, m0],
        bounds=([1e-6, 1e-6, total], [1.0, 3.0, 10 * total]),
        maxfev=20000,
    )
    se = np.sqrt(np.diag(pcov))
    keys = ("p", "q", "M")
    return dict(zip(keys, popt)), dict(zip(keys, se))


def fit_bass_ols(sales):
    """Estimate p, q, M with the original discrete regression of Bass (1969).

    S_t = a + b * N_{t-1} + c * N_{t-1}^2, where N is cumulative sales.
    """
    sales = np.asarray(sales, dtype=float)
    n_prev = np.concatenate([[0.0], np.cumsum(sales)[:-1]])
    X = np.column_stack([np.ones_like(n_prev), n_prev, n_prev**2])
    a, b, c = np.linalg.lstsq(X, sales, rcond=None)[0]
    roots = np.roots([c, b, a])
    roots = roots[np.isreal(roots)].real
    M = roots[roots > 0].max()
    p = a / M
    q = -c * M
    return {"p": p, "q": q, "M": M}


def r_squared(actual, fitted):
    actual = np.asarray(actual, dtype=float)
    fitted = np.asarray(fitted, dtype=float)
    ss_res = np.sum((actual - fitted) ** 2)
    ss_tot = np.sum((actual - actual.mean()) ** 2)
    return 1 - ss_res / ss_tot


def peak_time(p, q):
    """Time of peak adoption, t* = ln(q/p) / (p + q)."""
    return np.log(q / p) / (p + q)


def calibrate_p(first_period_adopters, q, M):
    """Find p such that the model reproduces the adopters observed in period 1."""
    target = first_period_adopters / M
    return brentq(lambda p: bass_cumulative_share(1, p, q) - target, 1e-6, 0.99)
