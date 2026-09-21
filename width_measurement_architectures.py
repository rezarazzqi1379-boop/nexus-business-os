from width_measurement_physics import MeasurementArchitecture

# A1 - ultra low cost. Phone on a tripod, a scribed reference bar in frame,
# frames pulled by hand. Buildable in an afternoon for the cost of a tripod.
A1 = MeasurementArchitecture(
    "A1", "Phone camera + scribed reference bar",
    "Self-emission silhouette against a dark background; scale from a reference bar in frame.",
    field_of_view_mm=600, sensor_pixels=1920, bloom_pixels=4.0,
    mounting_angle_deg=6.0, vibration_blur_mm=1.2, calibration_drift_frac=0.004,
    sample_rate_hz=30, temp_uncertainty_k=150,
    cost_class="negligible", buildable_locally=True, reversible_install=True,
    notes="Angle is hand-set, so obliquity dominates. Temperature assumed, not measured.")

# A2 - two-camera thermal silhouette rig, locally built, with a fixed jig that
# guarantees perpendicularity, plus the pyrometer feeding hot-to-cold.
A2 = MeasurementArchitecture(
    "A2", "Two-camera silhouette rig on a fixed jig",
    "Two machine-vision cameras on a rigid perpendicular jig; median over many frames; "
    "pyrometer supplies the hot-to-cold correction.",
    field_of_view_mm=400, sensor_pixels=2448, bloom_pixels=2.5,
    mounting_angle_deg=1.5, vibration_blur_mm=0.4, calibration_drift_frac=0.001,
    sample_rate_hz=60, temp_uncertainty_k=30,
    cost_class="low", buildable_locally=True, reversible_install=True,
    notes="The jig is what buys the accuracy, not the cameras.")

# A3 - UNCONVENTIONAL but physically sound: modulated backlight + lock-in
# detection on a linear array. The workpiece glows, which defeats ordinary
# backlighting; modulating the source and demodulating at that frequency
# rejects the steady self-emission entirely.
A3 = MeasurementArchitecture(
    "A3", "Modulated backlight + lock-in linear array",
    "Collimated LED bar strobed at a few kHz behind the pass line; linear photodiode "
    "array demodulates at the strobe frequency, so the workpiece's own glow - which is "
    "steady - is rejected as DC. Turns the piece's self-emission from the main problem "
    "into an irrelevance.",
    field_of_view_mm=400, sensor_pixels=4096, bloom_pixels=0.8,
    mounting_angle_deg=1.0, vibration_blur_mm=0.3, calibration_drift_frac=0.0008,
    sample_rate_hz=1000, temp_uncertainty_k=30,
    cost_class="low-medium", buildable_locally=True, reversible_install=True,
    notes="UNCONVENTIONAL for a hot mill. No prior art check done on this specific "
          "combination. Optical path must survive scale and steam - the main risk.")

# A4 - portable hot profile scanner, bought. Cost is the only published figure
# found anywhere in the technology search.
A4 = MeasurementArchitecture(
    "A4", "Portable hot profile scanner (Hexagon CALIPRI RCx class)",
    "Laser line scanner, handheld, 10-20 s per profile. Gives full section, not just width.",
    field_of_view_mm=300, sensor_pixels=6000, bloom_pixels=0.5,
    mounting_angle_deg=0.5, vibration_blur_mm=0.1, calibration_drift_frac=0.0003,
    sample_rate_hz=0.07, temp_uncertainty_k=30,
    cost_class="USD 28-70k [Tier 5, distributor listing, unverified]",
    buildable_locally=False, reversible_install=True,
    notes="Sample rate is the problem: 10-20 s per profile cannot follow a live pass "
          "sequence. Fine for spot checks between passes if the piece is held.")

# A5 - fixed in-line laser triangulation profile gauge, bought.
A5 = MeasurementArchitecture(
    "A5", "Fixed in-line laser profile gauge (LIMAB BarProfiler class)",
    "Multi-head laser triangulation, permanently mounted, full cross-section per pass.",
    field_of_view_mm=600, sensor_pixels=12000, bloom_pixels=0.4,
    mounting_angle_deg=0.2, vibration_blur_mm=0.05, calibration_drift_frac=0.0002,
    sample_rate_hz=200, temp_uncertainty_k=20,
    cost_class="one to two orders above A4; no vendor publishes a price",
    buildable_locally=False, reversible_install=False,
    notes="Datasheet range 5-250 x 30-600 mm at 0-1200C covers our product. "
          "Not reversible - needs a permanent mount and integration.")

ALL = (A1, A2, A3, A4, A5)
