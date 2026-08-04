"""Orbital-mirror targeting geometry tests (real data, no mocks)."""

from __future__ import annotations

import numpy as np
import pytest

from die_another_day import orbital_mirror as om

# Config-matched orbital elements (see manuscript/config.yaml).
SMA = 7200e3
LAT = 60.0
LON = 15.0

# A pass geometry known to yield a feasible window (verified at build time).
MA = 320.0
RAAN = 0.0
JD = 2461300.5


def test_gmst_in_range_and_varies() -> None:
    g1 = om.gmst_radians(2461000.5)
    g2 = om.gmst_radians(2461001.5)
    assert 0.0 <= g1 < 2 * np.pi
    assert g1 != pytest.approx(g2)


def test_lwlatlon_north_pole() -> None:
    ecef = om.lwlatlon_to_ecef(90.0, 0.0)
    assert ecef[0] == pytest.approx(0.0, abs=1.0)
    assert ecef[1] == pytest.approx(0.0, abs=1.0)
    assert ecef[2] == pytest.approx(om.earth_radius_m, rel=1e-6)


def test_ecef_to_eci_zero_gmst_is_identity() -> None:
    v = np.array([1000.0, 2000.0, 3000.0])
    assert np.allclose(om.ecef_to_eci(v, 0.0), v)


def test_propagate_circular_radius() -> None:
    pos = om.propagate_circular(
        semi_major_axis_m=SMA,
        inclination_deg=65.0,
        raan_deg=0.0,
        mean_anomaly_deg=MA,
        elapsed_s=300.0,
    )
    assert np.linalg.norm(pos) == pytest.approx(SMA, rel=1e-9)


def test_propagate_circular_validation() -> None:
    with pytest.raises(ValueError):
        om.propagate_circular(
            semi_major_axis_m=om.earth_radius_m,
            inclination_deg=65.0,
            raan_deg=0.0,
            mean_anomaly_deg=0.0,
            elapsed_s=0.0,
        )


def test_propagate_deterministic() -> None:
    a = om.propagate_circular(
        semi_major_axis_m=SMA, inclination_deg=65.0, raan_deg=0.0, mean_anomaly_deg=MA, elapsed_s=120.0
    )
    b = om.propagate_circular(
        semi_major_axis_m=SMA, inclination_deg=65.0, raan_deg=0.0, mean_anomaly_deg=MA, elapsed_s=120.0
    )
    assert np.array_equal(a, b)


def test_sun_unit_is_unit() -> None:
    s = om.sun_unit_eci(JD)
    assert np.linalg.norm(s) == pytest.approx(1.0, abs=1e-6)


def test_elevation_overhead() -> None:
    target = om.lwlatlon_to_ecef(LAT, LON)
    sat = 2.0 * target  # radially outward above the target
    assert om.elevation_deg(sat, target) == pytest.approx(90.0, abs=0.01)


def test_elevation_below_horizon() -> None:
    target = om.lwlatlon_to_ecef(LAT, LON)
    sat = -target  # on the opposite side of Earth
    assert om.elevation_deg(sat, target) < 0.0


def test_elevation_same_point_is_overhead() -> None:
    target = om.lwlatlon_to_ecef(LAT, LON)
    assert om.elevation_deg(target, target) == 90.0


def test_elevation_zero_target_raises() -> None:
    sat = om.lwlatlon_to_ecef(LAT, LON)
    with pytest.raises(ValueError):
        om.elevation_deg(sat, np.zeros(3))  # cannot normalize a zero target vector


def test_in_shadow() -> None:
    sun = om.sun_unit_eci(JD)
    # Satellite on the sunlit side: not in shadow.
    assert om.in_shadow(2.0 * sun, sun) is False
    # Satellite on the far side along the anti-sun axis near Earth: in shadow.
    assert om.in_shadow(-2.0 * sun, sun) is True


def test_point_mirror_returns_physics() -> None:
    gmst = om.gmst_radians(JD)
    target = om.ecef_to_eci(om.lwlatlon_to_ecef(LAT, LON), gmst)
    sat = om.propagate_circular(
        semi_major_axis_m=SMA,
        inclination_deg=65.0,
        raan_deg=RAAN,
        mean_anomaly_deg=MA,
        elapsed_s=1560.0,
    )
    sun = om.sun_unit_eci(JD)
    pt = om.point_mirror(sat, target, sun)
    assert pt.delivered_power_w > 0.0
    assert pt.spot_radius_m > 0.0
    assert len(pt.normal) == 3
    assert abs(np.linalg.norm(pt.normal) - 1.0) < 1e-6


def test_plan_pass_feasible_window() -> None:
    plan = om.plan_pass(
        semi_major_axis_m=SMA,
        inclination_deg=65.0,
        raan_deg=RAAN,
        mean_anomaly_deg=MA,
        target_lat_deg=LAT,
        target_lon_deg=LON,
        jd_start=JD,
        duration_s=3000.0,
        dt_s=60.0,
    )
    assert plan.feasible_seconds > 0.0
    assert plan.n_feasible > 0
    assert plan.best_index is not None
    assert plan.best_flux_w_m2 > 0.0
    assert len(plan.points) == 51


def test_plan_pass_validation() -> None:
    with pytest.raises(ValueError):
        om.plan_pass(
            semi_major_axis_m=SMA,
            inclination_deg=65.0,
            raan_deg=RAAN,
            mean_anomaly_deg=MA,
            target_lat_deg=LAT,
            target_lon_deg=LON,
            jd_start=JD,
            duration_s=0.0,
            dt_s=60.0,
        )
    with pytest.raises(ValueError):
        om.plan_pass(
            semi_major_axis_m=SMA,
            inclination_deg=65.0,
            raan_deg=RAAN,
            mean_anomaly_deg=MA,
            target_lat_deg=LAT,
            target_lon_deg=LON,
            jd_start=JD,
            duration_s=300.0,
            dt_s=0.0,
        )
