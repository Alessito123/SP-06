"""Aproximación normal para pérdidas pareadas y escenarios de dependencia."""
from math import ceil
from statistics import NormalDist


def design(delta=0.10, sigma=0.35, rho_country=0.15, rho_time=0.30,
           origins=12, loss=0.15, power=0.80):
    normal = NormalDist()
    n_eff = ((normal.inv_cdf(0.975) + normal.inv_cdf(power)) * sigma / delta) ** 2
    temporal = 1 + 2 * sum((1 - k / origins) * rho_time ** k for k in range(1, origins))
    # ICC residual entre países en un mismo origen. Correlación separable.
    information = n_eff * temporal / (origins * (1 - loss))
    denominator = 1 - information * rho_country
    countries = None if denominator <= 0 else ceil(information * (1 - rho_country) / denominator)
    return n_eff, countries


if __name__ == "__main__":
    for origins in [8, 12, 16, 20]:
        for icc in [0, 0.05, 0.15]:
            n, countries = design(origins=origins, rho_country=icc)
            print(f"orígenes={origins:2} ICC={icc:.2f} n_efectivo={ceil(n)} países={countries or 'inviable'}")
