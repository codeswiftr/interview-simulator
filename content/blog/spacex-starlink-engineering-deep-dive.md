# SpaceX Starlink Engineering Deep Dive: Low-Earth Orbit Internet Infrastructure

Starlink is the largest satellite constellation ever deployed, with over 6,000 operational satellites as of early 2026 and a target of 42,000 under FCC license. It delivers sub-20ms latency internet to rural areas, ships, aircraft, and conflict zones—performance that was physically impossible from geostationary orbit. If you are interviewing for an embedded, systems, or infrastructure role at SpaceX, understanding the engineering tradeoffs that make this possible is essential preparation.

## Constellation Architecture: Why 550km Changes Everything

Geostationary satellites orbit at 35,786km. A signal traveling from ground to satellite and back must cover roughly 72,000km, imposing a minimum round-trip latency of ~240ms (speed of light: 299,792 km/s). At 550km, Starlink's Shell 1 satellites cut that propagation distance by 65x, yielding a theoretical minimum single-hop latency of ~3.6ms—and real-world measured latencies of 15–25ms, competitive with terrestrial broadband.

The tradeoff is coverage and satellite count. A geostationary satellite covers roughly one-third of Earth's surface; a 550km satellite has a line-of-sight footprint of only ~1,500km diameter. Providing continuous global coverage requires hundreds of satellites per orbital shell, coordinated so that at least one satellite is always within the user terminal's elevation mask (typically 25°+ above the horizon).

Coverage gaps at polar latitudes (above ~70°N/S) were an early limitation of the inclined 53° orbital shells. Starlink addressed this with dedicated polar shells at 97.6° inclination (sun-synchronous), providing coverage at the expense of higher launch complexity and slightly different orbital decay dynamics.

## Ground Station Network and Inter-Satellite Laser Links

Initial Starlink deployments required a dense ground station (gateway) network: user terminals talked to overhead satellites, which bent the signal down to the nearest gateway for terrestrial internet hand-off. This created coverage gaps over oceans and remote areas without nearby gateways.

Generation 2 satellites introduced inter-satellite laser links (ISLLs)—optical crosslinks operating in the 1550nm band that allow packets to hop between satellites before descending to a gateway. An ISL link supports ~100 Gbps at ranges up to ~5,000km, with pointing-and-tracking achieved by fine-steering mirrors on each satellite.

The routing implications are significant. With ISLLs, the constellation forms a dynamic mesh network where topology changes every few seconds as satellites move at ~7.5 km/s. Starlink uses a modified distance-vector routing protocol optimized for predictable topology changes (orbital mechanics are deterministic) rather than the reactive flooding used in terrestrial ad-hoc networks. Pre-computed routing tables based on orbital propagation can be uplinked in advance, reducing the control overhead compared to purely reactive protocols.

Packets flowing from a user in the middle of the Pacific Ocean might traverse 4–6 ISL hops before reaching a gateway, adding ~2–3ms per hop. For latency-sensitive applications, the routing algorithm must balance hop count against link quality (each ISL link has a noise floor that increases with pointing angle error).

## The Starlink User Terminal: Phased Array Engineering

The Starlink dish—internally called "Dishy McFlatface"—is a flat-panel phased array antenna. Understanding how it works is a common systems interview topic.

A phased array steers its beam electronically by adjusting the phase of the signal fed to each antenna element. If each element is fed with a phase shift proportional to its position, the radiated wavefronts constructively interfere in a specific direction, forming a narrow beam without any mechanical movement:

```python
import numpy as np

def compute_phase_shifts(
    element_positions: np.ndarray,  # (N, 2) array of (x, y) element positions in meters
    target_azimuth_deg: float,
    target_elevation_deg: float,
    frequency_hz: float = 14.5e9  # Ku-band uplink
) -> np.ndarray:
    """
    Compute per-element phase shifts to steer beam toward
    (azimuth, elevation) in spherical coordinates.
    Returns phase shifts in radians.
    """
    wavelength = 3e8 / frequency_hz  # ~20.7mm at 14.5 GHz
    k = 2 * np.pi / wavelength       # wave number

    az = np.radians(target_azimuth_deg)
    el = np.radians(target_elevation_deg)

    # Unit vector toward target in Cartesian (x=East, y=North, z=Up)
    target_vec = np.array([
        np.cos(el) * np.sin(az),
        np.cos(el) * np.cos(az),
        np.sin(el)
    ])

    # Phase shift = k * (element_position · target_unit_vector)
    # element_positions are in the x-y plane (z=0 for flat array)
    phase_shifts = k * (
        element_positions[:, 0] * target_vec[0] +
        element_positions[:, 1] * target_vec[1]
    )

    return phase_shifts % (2 * np.pi)  # wrap to [0, 2π]


def example_array():
    # 16x16 element array, 15mm element spacing (half-wavelength at ~10 GHz)
    spacing = 0.015
    xs, ys = np.meshgrid(np.arange(16) * spacing, np.arange(16) * spacing)
    positions = np.stack([xs.ravel(), ys.ravel()], axis=1)

    phases = compute_phase_shifts(positions, target_azimuth_deg=45.0, target_elevation_deg=40.0)
    print(f"Phase shifts for 256 elements: min={phases.min():.3f} max={phases.max():.3f} rad")
    return phases
```

The Starlink Gen 2 dish contains approximately 1,280 dual-polarization antenna elements. The beam can be steered across its full field of view in microseconds—far faster than any mechanical gimbal—allowing it to track a satellite moving at 7.5 km/s while simultaneously preparing for handoff to the next satellite.

## Satellite Handoff State Machine

With satellites continuously moving across the sky, user terminals must seamlessly hand off between satellites every 2–5 minutes. Managing this handoff without dropped connections requires careful state machine design:

```python
from enum import Enum, auto
import time

class HandoffState(Enum):
    TRACKING_PRIMARY = auto()
    SCANNING_SECONDARY = auto()
    DUAL_LINK = auto()
    SWITCHING = auto()
    TRACKING_NEW_PRIMARY = auto()
    DEGRADED = auto()

class SatelliteHandoffController:
    ELEVATION_HANDOFF_THRESHOLD = 30.0  # degrees — begin scanning for next sat
    DUAL_LINK_OVERLAP_SEC = 2.0        # seconds of simultaneous connection
    SWITCH_TIMEOUT_SEC = 5.0

    def __init__(self):
        self.state = HandoffState.TRACKING_PRIMARY
        self.primary_sat_id: str | None = None
        self.secondary_sat_id: str | None = None
        self.dual_link_start: float | None = None

    def tick(self, primary_elevation: float, secondary_available: bool, secondary_sat_id: str | None):
        match self.state:
            case HandoffState.TRACKING_PRIMARY:
                if primary_elevation < self.ELEVATION_HANDOFF_THRESHOLD:
                    self.state = HandoffState.SCANNING_SECONDARY

            case HandoffState.SCANNING_SECONDARY:
                if secondary_available and secondary_sat_id:
                    self.secondary_sat_id = secondary_sat_id
                    self.dual_link_start = time.monotonic()
                    self.state = HandoffState.DUAL_LINK
                elif primary_elevation < 10.0:
                    self.state = HandoffState.DEGRADED

            case HandoffState.DUAL_LINK:
                elapsed = time.monotonic() - (self.dual_link_start or 0)
                if elapsed >= self.DUAL_LINK_OVERLAP_SEC:
                    self.state = HandoffState.SWITCHING

            case HandoffState.SWITCHING:
                # Commit: secondary becomes primary
                self.primary_sat_id = self.secondary_sat_id
                self.secondary_sat_id = None
                self.dual_link_start = None
                self.state = HandoffState.TRACKING_NEW_PRIMARY

            case HandoffState.TRACKING_NEW_PRIMARY:
                # Alias back to normal tracking after confirming link
                self.state = HandoffState.TRACKING_PRIMARY

            case HandoffState.DEGRADED:
                if secondary_available:
                    self.secondary_sat_id = secondary_sat_id
                    self.state = HandoffState.SWITCHING

        return self.state
```

The real implementation handles TCP session continuity (using sequence number caching to avoid retransmission bursts during handoff), MIMO beamforming weight transfer between satellites, and regulatory constraints (some countries require the terminal to drop connectivity rather than hand off to a satellite licensed in a different jurisdiction).

## Network Operations: Managing 6,000+ Satellites

Starlink's network operations center (NOC) faces a fleet management challenge at a scale no terrestrial ISP encounters. Key systems include:

- **Telemetry ingestion**: each satellite transmits health data (power, thermal, attitude, propellant) on every ground station pass. At 6,000 satellites, this is millions of telemetry points per minute.
- **Collision avoidance**: Starlink runs automated conjunction analysis against the LeoLabs and Space-Track catalog. When a predicted conjunction exceeds a probability-of-collision threshold (~1 in 10,000), an autonomous maneuver plan is uplinked and executed without human-in-the-loop approval.
- **Orbital decay management**: at 550km, atmospheric drag is non-negligible (the atmosphere extends to ~1,000km at low density). Each satellite carries a Hall-effect ion thruster that periodically boosts orbit, consuming krypton propellant. The NOC schedules these burns to maintain the orbital shell within ±5km of the target altitude.
- **Deorbit sequencing**: at end-of-life, satellites are commanded to a disposal orbit that ensures reentry within 5 years (the FCC's current deorbit standard). Starlink targets reentry within 1 year from nominal altitude.

## Interview Implications for Embedded and Systems Engineers

Starlink interviews for embedded and systems roles typically probe:

- **RF and antenna fundamentals**: can you explain how a phased array works? What is beam squint, and why does it matter at Ku-band?
- **Real-time OS and latency**: the user terminal runs a custom RTOS that must meet hard latency deadlines for beam steering. Expect questions about priority inversion, interrupt latency budgets, and deterministic memory allocation.
- **Fault tolerance in space**: unlike a server in a data center, a satellite cannot be physically rebooted by an operator. How do you design a watchdog architecture that can recover from a processor lockup 550km above Earth?
- **Distributed systems at scale**: how would you design the telemetry ingestion pipeline for 6,000 satellites, each sending data every 30 seconds? (Hint: think Kafka for ingest, columnar storage for time-series queries, and downsampling for long-term retention.)

The most compelling candidates connect their prior experience—whether RTOS development, RF design, or distributed systems—to the specific constraints of the LEO environment: radiation hardening requirements, limited computational resources, communication windows measured in minutes, and the absolute prohibition on physical maintenance.

## Closing Thoughts

Starlink is not a satellite internet service built on existing technology—it is a vertically integrated system where SpaceX designed the rockets, satellites, ground stations, user terminals, and network stack. The engineering decisions at each layer have cascading implications for every other layer. Candidates who understand this vertical integration, and can reason about the tradeoffs it enables (tight hardware-software co-design) and imposes (less modularity, harder to swap suppliers), demonstrate the systems thinking that SpaceX looks for in senior engineers.
