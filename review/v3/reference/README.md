# Marlin v3.0: per-shot reference clips

Two kinds of file, all 24 fps, no sound, no review slate:

- `*_plate.mp4` (1280x720): the **clean Blender render** of a 3D shot. No graphics. Use these as the camera-move and
  blocking reference for the video model.
- `*_comp.mp4` (1920x1080): the shot **as it appears in the animatic** (overlays and supers included).

| Shot | Time | Plate(s) | What the camera does |
|---|---|---|---|
| 01 The boat | 0:00-0:04 | `shot01_the-boat_plate` | Tracks tight with the go-fast at 30 kt, low on the water; slides from off the bow, down the bales, to the three men at the console. Handheld. |
| 03 Infrared ID | 0:07-0:10 | `shot03_infrared-id_thermal_plate` | Aircraft sensor, long lens, 38 degrees down. Slews onto the boat with a small overshoot, then holds. White-hot. |
| 06 Loiter | 0:20-0:23 | `shot06_loiter_plate` | Low, wide, slow push toward a hull-borne Marlin riding the swell; moon and glitter path. Sensor bar turning. |
| 07 Lift | 0:23-0:28 | `shot07_lift_plate` | Locked off at the waterline. Pans with the Marlin as it spools up and climbs onto the foil, then lets it leave frame. |
| 09 The run | 0:34-0:40 | `shot09_the-run_plate` | Drone alongside at 100 kt; slides from the bow quarter to the beam and rises slightly while the sea builds. |
| 10 Eyes on | 0:40-0:46 | `shot10_eyes-on_thermal_plate`, `shot10_eyes-on_standoff_plate` | Thermal: Marlin's mast sensor on the go-fast. Standoff: tracking wide shot, slow pull-out, as the Marlin turns in, comes off the foil and settles hull-borne; second Marlin beyond. (Standoff plate starts 1.375 s into the shot.) |

Shots 02, 04, 05, 08, 11 and 12 are graphics (radar, tactical display, end card): only `_comp` clips.

The scenes behind the plates are in `blender/scenes/*.blend` (camera, vessels and ocean are keyed per frame).
These are blockout models: proportions and motion are the reference, not surface detail.
