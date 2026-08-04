"""Orbital-mirror (ICARUS) targeting geometry.

ICARUS / *Die Another Day* (2002) concept. An orbital solar mirror is a
sun-synchronous satellite reflector that concentrates sunlight onto a ground
target. This module models the real targeting geometry:

* :func:`propagate_circular` propagates a circular orbit (Keplerian mean
  anomaly) into an Earth-centered inertial (ECI) position.
* :func:`lwlatlon_to_ecef` / :func:`ecef_to_eci` place the ground target in
  the same frame, using Greenwich sidereal time for the Earth rotation.
* :func:`sun_unit_eci` gives a low-precision solar unit vector.
* :func:`elevation_deg` computes the satellite's elevation above the target's
  horizon, and :func:`in_shadow` decides whether the mirror is eclipsed by
  the Earth.
* :func:`point_mirror` solves the reflection law — the mirror normal bisects
  the angle between the incoming solar ray and the re-pointed target ray —
  and returns the delivered power and focused flux using physical solar,
  reflectivity, and beam-spread parameters.
* :func:`plan_pass` marches the orbit through a window and reports the
  feasible targeting windows plus the best-illumination moment.

All functions are pure and deterministic: given the same orbital elements and
time they reproduce identical numbers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np

__all__ = [
    "MirrorPointing",
    "PassPlan",
    "PassPoint",
    "earth_radius_m",
    "elevation_deg",
    "gmst_radians",
    "in_shadow",
    "lwlatlon_to_ecef",
    "plan_pass",
    "point_mirror",
    "propagate_circular",
    "sun_unit_eci",
]

#: Solar constant (W / m^2).
SOLAR_CONSTANT_W_M2 = 1361.0
#: Standard gravitational parameter of Earth (m^3 / s^2).
MU_EARTH = 3.986004418e14
#: Mean Earth radius (m).
earth_radius_m = 6.371e6


@dataclass(frozen=True)
class MirrorPointing:
    """Optimal mirror orientation and delivered energy for one instant."""

    feasible: bool
    sunlit: bool
    elevation_deg: float
    distance_m: float
    incidence_deg: float
    normal: tuple[float, float, float]
    delivered_power_w: float
    spot_radius_m: float
    target_flux_w_m2: float


@dataclass(frozen=True)
class PassPoint:
    """A single sampled instant along an orbital pass."""

    time_s: float
    elevation_deg: float
    sunlit: bool
    feasible: bool
    delivered_power_w: float
    target_flux_w_m2: float


@dataclass(frozen=True)
class PassPlan:
    """Aggregated analysis of a mirror pass over a ground target."""

    points: tuple[PassPoint, ...]
    dt_s: float
    feasible_seconds: float
    n_feasible: int
    best_index: int | None
    best_flux_w_m2: float


def gmst_radians(jd: float) -> float:
    """Greenwich mean sidereal time (radians) for a Julian date."""
    days = jd - 2451545.0
    gmst_deg = 280.46061837 + 360.98564736629 * days
    return float(np.deg2rad(gmst_deg % 360.0))


def lwlatlon_to_ecef(lat_deg: float, lon_deg: float, alt_m: float = 0.0) -> np.ndarray:
    """Earth-centered Earth-fixed position of a latitude/longitude target."""
    lat = np.deg2rad(lat_deg)
    lon = np.deg2rad(lon_deg)
    r = earth_radius_m + alt_m
    x = r * np.cos(lat) * np.cos(lon)
    y = r * np.cos(lat) * np.sin(lon)
    z = r * np.sin(lat)
    return np.array([x, y, z])


def ecef_to_eci(pos_ecef: np.ndarray, gmst: float) -> np.ndarray:
    """Rotate an ECEF vector into ECI using sidereal time ``gmst``."""
    c, s = np.cos(gmst), np.sin(gmst)
    rot = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
    result: object = rot @ np.asarray(pos_ecef, dtype=float)
    return cast(np.ndarray, result)


def propagate_circular(
    *,
    semi_major_axis_m: float,
    inclination_deg: float,
    raan_deg: float,
    mean_anomaly_deg: float,
    elapsed_s: float,
) -> np.ndarray:
    """ECI position of a body on a circular orbit at ``elapsed_s`` after epoch."""
    if semi_major_axis_m <= earth_radius_m:
        raise ValueError("semi_major_axis_m must be above Earth's surface")
    inc = np.deg2rad(inclination_deg)
    raan = np.deg2rad(raan_deg)
    n = float(np.sqrt(MU_EARTH / semi_major_axis_m**3))
    m = np.deg2rad(mean_anomaly_deg) + n * elapsed_s
    a = semi_major_axis_m
    x_pe = a * np.cos(m)
    y_pe = a * np.sin(m)
    # Perifocal -> ECI: Rz(-raan) Rx(-inc) Rz of argument of latitude.
    x = x_pe * np.cos(raan) - y_pe * np.cos(inc) * np.sin(raan)
    y = x_pe * np.sin(raan) + y_pe * np.cos(inc) * np.cos(raan)
    z = y_pe * np.sin(inc)
    return np.array([float(x), float(y), float(z)])


def sun_unit_eci(jd: float) -> np.ndarray:
    """Low-precision solar unit vector in ECI for a Julian date."""
    n = jd - 2451545.0
    mean_longitude = np.deg2rad((280.460 + 0.9856474 * n) % 360.0)
    mean_anomaly = np.deg2rad((357.528 + 0.9856003 * n) % 360.0)
    ecliptic_longitude = mean_longitude + np.deg2rad(1.915) * np.sin(mean_anomaly)
    obliquity = np.deg2rad(23.439)
    x = np.cos(ecliptic_longitude)
    y = np.cos(obliquity) * np.sin(ecliptic_longitude)
    z = np.sin(obliquity) * np.sin(ecliptic_longitude)
    v = np.array([float(x), float(y), float(z)])
    return v / float(np.linalg.norm(v))


def _unit(v: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    if norm == 0.0:
        raise ValueError("cannot normalize a zero vector")
    return v / norm


def elevation_deg(sat_eci: np.ndarray, target_eci: np.ndarray) -> float:
    """Elevation angle (degrees) of the satellite above the target's horizon."""
    up = _unit(target_eci)
    los = np.asarray(sat_eci, dtype=float) - np.asarray(target_eci, dtype=float)
    dist = float(np.linalg.norm(los))
    if dist == 0.0:
        return 90.0
    sin_elev = float(np.dot(los, up) / dist)
    return float(np.rad2deg(np.arcsin(np.clip(sin_elev, -1.0, 1.0))))


def in_shadow(sat_eci: np.ndarray, sun_unit: np.ndarray) -> bool:
    """True when the satellite is eclipsed by Earth's cylindrical shadow."""
    s = np.asarray(sat_eci, dtype=float)
    if float(np.dot(s, sun_unit)) > 0.0:
        return False  # on the sunlit side
    perpendicular = float(np.linalg.norm(s - float(np.dot(s, sun_unit)) * sun_unit))
    return perpendicular < earth_radius_m


def point_mirror(
    sat_eci: np.ndarray,
    target_eci: np.ndarray,
    sun_unit: np.ndarray,
    *,
    mirror_area_m2: float = 1e4,
    reflectivity: float = 0.90,
    beam_half_angle_deg: float = 0.02,
    atmosphere_rl: float = 0.85,
    min_elevation_deg: float = 10.0,
) -> MirrorPointing:
    """Compute the optimal mirror pointing and delivered energy at one instant.

    The mirror normal bisects the incoming solar ray and the ground re-point
    (reflection law), so ``normal = unit(sun_unit - sat_dir? ) + unit(target -
    sat)``; the incidence angle then drives how much projected mirror area
    intercepts the sunlight.
    """
    sat = np.asarray(sat_eci, dtype=float)
    target = np.asarray(target_eci, dtype=float)
    s_hat = _unit(np.asarray(sun_unit, dtype=float) - sat)  # mirror -> Sun
    r_hat = _unit(target - sat)  # mirror -> target
    normal = _unit(s_hat + r_hat)
    cos_inc = float(np.clip(np.abs(np.dot(normal, s_hat)), 0.0, 1.0))
    incidence_deg = float(np.rad2deg(np.arccos(cos_inc)))

    dist = float(np.linalg.norm(target - sat))
    elev = elevation_deg(sat, target)
    sunlit = not in_shadow(sat, np.asarray(sun_unit, dtype=float))

    # Focused beam: reflected power, then flux over the beam's footprint.
    # The beam half-angle adds the mirror's own apparent angular radius.
    delivered_power_w = SOLAR_CONSTANT_W_M2 * mirror_area_m2 * reflectivity * cos_inc * atmosphere_rl
    mirror_angular = np.arctan(np.sqrt(max(mirror_area_m2, 0.0) / np.pi) / max(dist, 1.0))
    half_angle = np.deg2rad(beam_half_angle_deg) + mirror_angular
    spot_radius_m = dist * np.tan(half_angle)
    spot_area = np.pi * spot_radius_m**2
    target_flux_w_m2 = delivered_power_w / spot_area if spot_area > 0.0 else 0.0

    feasible = bool(elev >= min_elevation_deg and sunlit and cos_inc > 0.0)
    return MirrorPointing(
        feasible=feasible,
        sunlit=sunlit,
        elevation_deg=elev,
        distance_m=dist,
        incidence_deg=incidence_deg,
        normal=(float(normal[0]), float(normal[1]), float(normal[2])),
        delivered_power_w=delivered_power_w,
        spot_radius_m=float(spot_radius_m),
        target_flux_w_m2=float(target_flux_w_m2),
    )


def plan_pass(
    *,
    semi_major_axis_m: float,
    inclination_deg: float,
    raan_deg: float,
    mean_anomaly_deg: float,
    target_lat_deg: float,
    target_lon_deg: float,
    jd_start: float,
    duration_s: float = 1800.0,
    dt_s: float = 30.0,
    **point_kwargs: float,
) -> PassPlan:
    """Time-march an orbital mirror pass over a target and aggregate windows."""
    if duration_s <= 0.0 or dt_s <= 0.0:
        raise ValueError("duration_s and dt_s must be positive")
    n_steps = int(duration_s / dt_s) + 1
    target_ecef = lwlatlon_to_ecef(target_lat_deg, target_lon_deg)
    points: list[PassPoint] = []
    for step in range(n_steps):
        t = step * dt_s
        sat = propagate_circular(
            semi_major_axis_m=semi_major_axis_m,
            inclination_deg=inclination_deg,
            raan_deg=raan_deg,
            mean_anomaly_deg=mean_anomaly_deg,
            elapsed_s=t,
        )
        gmst = gmst_radians(jd_start + t / 86400.0)
        target = ecef_to_eci(target_ecef, gmst)
        sun = sun_unit_eci(jd_start + t / 86400.0)
        pt = point_mirror(sat, target, sun, **point_kwargs)
        points.append(
            PassPoint(
                time_s=t,
                elevation_deg=pt.elevation_deg,
                sunlit=pt.sunlit,
                feasible=pt.feasible,
                delivered_power_w=pt.delivered_power_w,
                target_flux_w_m2=pt.target_flux_w_m2,
            )
        )
    feasible_seconds = float(dt_s * sum(1 for p in points if p.feasible))
    n_feasible = sum(1 for p in points if p.feasible)
    best_index: int | None = None
    best_flux = 0.0
    for i, p in enumerate(points):
        if p.feasible and p.target_flux_w_m2 > best_flux:
            best_flux = p.target_flux_w_m2
            best_index = i
    return PassPlan(
        points=tuple(points),
        dt_s=dt_s,
        feasible_seconds=feasible_seconds,
        n_feasible=n_feasible,
        best_index=best_index,
        best_flux_w_m2=best_flux,
    )
