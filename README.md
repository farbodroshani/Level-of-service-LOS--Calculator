# Highway Level of Service Calculator

A desktop application for calculating Level of Service (LOS) for highway facilities based on the **Highway Capacity Manual, 7th Edition (HCM 7)**. This tool provides detailed step-by-step calculations for basic freeway segments, multilane highway segments, and two-lane highway segments.

## Features

- **Three Facility Types Supported:**
  - Basic freeway segments (HCM 7 Chapter 12)
  - Multilane highway segments (HCM 7 Chapter 12)
  - Two-lane highway segments: Passing Constrained, Passing Zone, and Passing Lane (HCM 7 Chapter 15)

- **Two Analysis Modes:**
  - **Calculate LOS**: Determine the level of service for existing or proposed facilities
  - **Design for Target LOS**: Find the minimum number of lanes required to achieve a target LOS (Freeway and Multilane only)

- **Comprehensive Calculations:**
  - Free-flow speed (FFS) estimation or measured FFS input
  - Capacity, demand-to-capacity check, and LOS F identification
  - Heavy vehicle PCEs for general terrain and for specific grades (with SUT/TT truck mixes)
  - Continuous speed–flow curves (Equation 12-1) with speed and capacity adjustment factors
  - Two-lane average speed, percent followers, and follower density, including horizontal curves, passing lane midpoint performance, and downstream passing lane effects
  - Detailed step-by-step solution breakdowns with equation and exhibit references

- **User-Friendly Interface:**
  - Clean GUI built with Tkinter
  - Scrollable input forms
  - Detailed results display
  - Step-by-step calculation viewer

## Requirements

- Python 3.7 or higher
- tkinter (usually included with Python)
- Standard Python libraries only (math, typing)

## Installation

1. Clone or download this repository
2. Ensure Python 3.7+ is installed on your system
3. No additional packages are required - the app uses only the Python standard library

## Usage

### Running the Application

```bash
python los_app.py
```

### Input Requirements

**All inputs must be in U.S. customary units:**
- Lengths: feet (ft) for widths, clearances and curve data; miles (mi) for segment and grade lengths
- Speeds: miles per hour (mi/h)
- Densities: per mile (e.g., ramps/mi, access points/mi)
- Volumes: vehicles per hour (veh/h)

### Basic Freeway Segment Analysis

**Inputs:**
- Demand volume (veh/h) - directional, or two-way with a directional split
- Peak hour factor (PHF)
- Number of lanes (directional) - for Calculate LOS mode
- Percentage of heavy vehicles (single-unit trucks + tractor-trailers; buses and RVs count as SUTs)
- Measured FFS (optional - leave blank to estimate it)
- Lane width (ft), right-side lateral clearance (ft), total ramp density (ramps/mi)
- Terrain: Level, Rolling, or Specific grade (grade %, grade length, and SUT/TT truck mix)
- Speed adjustment factor (SAF) and capacity adjustment factor (CAF) - 1.0 for base conditions

**Outputs:** FFS, adjusted FFS, capacity, ET, fHV, demand flow rate vp, v/c, speed, density, LOS

### Multilane Highway Segment Analysis

**Inputs:**
- Demand volume, PHF, number of lanes, percentage of heavy vehicles
- Measured FFS (optional) or base FFS (posted speed + 5 mi/h for limits ≥ 50 mi/h, + 7 mi/h below 50 mi/h)
- Lane width, right and left lateral clearance (ft), access points per mile
- Median type (Undivided, TWLTL, or Divided)
- Terrain: Level, Rolling, or Specific grade

**Outputs:** FFS, capacity, ET, fHV, vp, v/c, speed, density, LOS

### Two-Lane Highway Segment Analysis

**Inputs:**
- Analysis-direction volume (veh/h) and opposing-direction volume (Passing Zone segments only)
- Peak hour factor, percentage of heavy vehicles
- Segment type: Passing Constrained, Passing Zone, or Passing Lane
- Segment length (mi), percent grade (negative for downgrades), posted speed limit
- Measured FFS (optional), lane width, shoulder width, access points per mile
- Horizontal curves (optional), entered as `radius ft, superelevation %, length ft; ...`
- Upstream passing lane (optional): passing lane length, distance from the start of the passing lane to the end of the analyzed segment, percent followers and flow rate entering the passing lane

**Outputs:** vertical class, demand flow rate, capacity, d/c, FFS, average speed, percent followers, follower density, LOS (for passing lanes, the midpoint follower density and the follower density at the end of the lane)

## Level of Service Definitions

### Basic Freeway and Multilane Highway Segments (Exhibit 12-15)
| LOS | Density (pc/mi/ln) |
|-----|--------------------|
| A | ≤ 11 |
| B | > 11–18 |
| C | > 18–26 |
| D | > 26–35 |
| E | > 35–45 |
| F | Demand exceeds capacity or density > 45 |

### Two-Lane Highways (Exhibit 15-6) - follower density (followers/mi/ln)
| LOS | Posted speed ≥ 50 mi/h | Posted speed < 50 mi/h |
|-----|------------------------|------------------------|
| A | ≤ 2.0 | ≤ 2.5 |
| B | > 2.0–4.0 | > 2.5–5.0 |
| C | > 4.0–8.0 | > 5.0–10.0 |
| D | > 8.0–12.0 | > 10.0–15.0 |
| E | > 12.0 | > 15.0 |
| F | Demand exceeds capacity | Demand exceeds capacity |

## Step-by-Step Calculations

Click the "View Step-by-Step Calculations" button in the results panel to see:
- All intermediate values
- Equations and exhibits used (numbered as in HCM 7)
- Table lookups and interpolations
- Final calculations

## Design Mode

For Freeway and Multilane facilities, you can use the "Design for Target LOS" mode to:
1. Enter your traffic and geometric conditions
2. Select a target LOS (A through E)
3. The application will determine the minimum number of lanes (2 to 8 per direction) required

## Examples

The calculations reproduce the HCM 7 example problems in Chapter 26.

### Example 1: Basic Freeway Segment (HCM 7 Ch. 26, Example Problem 1)
- Volume: 2,000 veh/h (directional), PHF 0.92, 2 lanes per direction
- Heavy vehicles: 5%, level terrain
- Lane width: 11 ft, right lateral clearance: 2 ft, ramp density: 4 ramps/mi

**Result:** FFS 60.8 mi/h, vp 1,141 pc/h/ln, density 18.8 pc/mi/ln → LOS C

### Example 2: Freeway Design (HCM 7 Ch. 26, Example Problem 2)
- Volume: 4,000 veh/h, PHF 0.85, 8% heavy vehicles, level terrain
- 12-ft lanes, 6-ft lateral clearance, 3 ramps/mi, target LOS D

**Result:** 3 lanes per direction required (density 25.9 pc/mi/ln, LOS C)

### Example 3: Two-Lane Highway (HCM 7 Ch. 26, Example Problem 1)
- Passing Constrained segment, 0.75 mi, level, posted speed 50 mi/h
- 752 veh/h, PHF 0.94, 5% heavy vehicles, 12-ft lanes, 6-ft shoulders, no access points

**Result:** average speed 53.7 mi/h, 67.7% followers, follower density 10.1 → LOS D

## Methodology

This application is based on the **Highway Capacity Manual, 7th Edition: A Guide for Multimodal Mobility Analysis** (Transportation Research Board, 2022):
- **Chapter 12** - Basic Freeway and Multilane Highway Segments (FFS, capacity, PCEs, speed–flow model, density-based LOS)
- **Chapter 15** - Two-Lane Highways (vertical/horizontal alignment, average speed, percent followers, follower-density-based LOS)

### Changes from the earlier HCM 2010 version of this app
- Speed is computed from the continuous speed–flow equation instead of picking the nearest 5-mi/h FFS curve
- Capacity and the v/c check are computed; demand above capacity is reported as LOS F
- The driver population factor fp is replaced by the speed and capacity adjustment factors (SAF/CAF)
- Heavy vehicles use a single PCE (ET = 2.0 level, 3.0 rolling); RVs are no longer a separate class. Mountainous terrain is replaced by specific-grade PCEs
- Right-side clearance is interpolated, and the multilane lateral clearance table depends on the number of lanes
- The two-lane highway method (ATS/PTSF with Class I/II/III) is replaced by the HCM 7 follower-density method

## Limitations

1. **Uncongested conditions only:** demand above capacity is reported as LOS F; queuing impacts require the Chapter 10 freeway facility method
2. **Two-lane highways** are analyzed one segment at a time; the multi-segment facility averaging of Step 11 is not included, and the effective length of an upstream passing lane is estimated from the entered passing lane data
3. **Mixed-flow models** for steep grades or very high truck percentages (Chapters 25 and 26) are not included; specific-grade PCEs are used instead
4. **Managed lanes and bicycle LOS** are not included
5. **Design Mode** is not available for Two-Lane Highways
6. **Units:** All inputs must be in U.S. customary units (ft, mi, mi/h)

## Troubleshooting

### Common Issues:

1. **"Please enter a valid number" errors:**
   - Ensure all required numeric fields are filled
   - Fields marked optional can be left blank
   - Verify PHF is between 0 and 1

2. **Unexpected LOS results:**
   - Review input values for accuracy
   - Check that geometric data matches actual conditions
   - Verify terrain or grade inputs and the two-lane segment type

3. **Design mode not finding solution:**
   - Try a lower target LOS
   - Check if volume is extremely high (may require more than 8 lanes)


## License

© 2025 Farbod Roshani. All rights reserved.

## References

1. Highway Capacity Manual, 7th Edition: A Guide for Multimodal Mobility Analysis. Transportation Research Board, Washington, D.C., 2022.

2. Hoel, L.A., Garber, N.J., & Sarkar, R. (2020). Traffic and Highway Engineering. Cengage Learning.

## Support

For questions or issues, please refer to the HCM 7th Edition (Chapters 12, 15 and the example problems in Chapter 26) for detailed methodology explanations.

## Version History

- **v2.0** - Updated to the Highway Capacity Manual, 7th Edition
  - Continuous speed–flow model with capacity, v/c, SAF and CAF
  - Specific-grade PCEs and revised heavy vehicle treatment
  - New two-lane highway method based on follower density
  - Horizontal curve, passing lane, and downstream passing lane effects

- **v1.0** - Initial release (HCM 2010)
  - Freeway analysis
  - Multilane highway analysis
  - Two-lane highway analysis
  - Step-by-step calculations
  - Design mode for freeways and multilane highways
  - Imperial units only

---

**Note:** This application is intended for educational and professional use in highway capacity analysis. Always verify results with official HCM 7th Edition procedures for critical design decisions.
