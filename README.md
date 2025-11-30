# Highway Level of Service Calculator

A comprehensive desktop application for calculating Level of Service (LOS) for highway facilities based on the **Highway Capacity Manual (HCM 2010)** methodology. This tool provides detailed step-by-step calculations for Freeways, Multilane Highways, and Two-Lane Highways.

## Features

- **Three Facility Types Supported:**
  - Freeway segments
  - Multilane highways
  - Two-lane highways (Class I, II, and III)

- **Two Analysis Modes:**
  - **Calculate LOS**: Determine the level of service for existing or proposed facilities
  - **Design for Target LOS**: Find the minimum number of lanes required to achieve a target LOS (Freeway and Multilane only)

- **Comprehensive Calculations:**
  - Free-flow speed (FFS) adjustments
  - Passenger car equivalent (PCE) adjustments for heavy vehicles
  - Speed-flow relationships
  - Density calculations
  - Detailed step-by-step solution breakdowns

- **User-Friendly Interface:**
  - Clean, modern GUI built with Tkinter
  - Scrollable input forms
  - Detailed results display
  - Step-by-step calculation viewer

## Requirements

- Python 3.7 or higher
- tkinter (usually included with Python)
- Standard Python libraries (math, typing)

## Installation

1. Clone or download this repository
2. Ensure Python 3.7+ is installed on your system
3. No additional packages are required - the app uses only Python standard library

## Usage

### Running the Application

```bash
python los_app.py
```

### Input Requirements

**All inputs must be in Imperial units:**
- Lengths: feet (ft)
- Speeds: miles per hour (mi/h)
- Densities: per mile (e.g., ramps/mi, access points/mi)
- Volumes: vehicles per hour (veh/h)

### Freeway Analysis

**Required Inputs:**
- Demand volume (veh/h) - directional or two-way
- Peak hour factor (PHF)
- Number of lanes (directional) - for Calculate LOS mode
- Driver population factor (typically 1.0 for commuters)
- Percentage of trucks (%)
- Percentage of RVs (%)
- Lane width (ft)
- Right lateral clearance (ft)
- Total ramp density (ramps/mi)
- Terrain type (Level, Rolling, or Mountainous)

**Outputs:**
- Free-flow speed (FFS)
- Passenger car equivalent flow rate (vp, pc/h/ln)
- Mean speed (mi/h)
- Density (pc/mi/ln)
- Level of Service (A through F)

### Multilane Highway Analysis

**Required Inputs:**
- Demand volume (veh/h) - directional or two-way
- Peak hour factor (PHF)
- Number of lanes (directional) - for Calculate LOS mode
- Base free-flow speed (mi/h)
- Driver population factor
- Percentage of trucks (%)
- Percentage of RVs (%)
- Lane width (ft)
- Right lateral clearance (ft)
- Left lateral clearance (ft)
- Access points per mile
- Median type (Undivided, TWLTL, or Divided)
- Terrain type (Level, Rolling, or Mountainous)

**Outputs:**
- Free-flow speed (FFS)
- Passenger car equivalent flow rate (vp, pc/h/ln)
- Mean speed (mi/h)
- Density (pc/mi/ln)
- Level of Service (A through F)

### Two-Lane Highway Analysis

**Required Inputs:**
- Two-way volume (veh/h)
- Directional split (%)
- Peak hour factor (PHF)
- Percentage of trucks (%)
- Percentage of RVs (%)
- Base free-flow speed (mi/h)
- Lane width (ft)
- Shoulder width (ft)
- Access points per mile
- Percentage of no-passing zones (%)
- Terrain type (Level or Rolling)
- Highway class (Class I, Class II, or Class III)

**Outputs:**
- Free-flow speed (FFS)
- Average travel speed (ATS, mi/h)
- Percent time spent following (PTSF, %)
- Percent of free-flow speed (PFFS, %)
- Level of Service (A through F)

**Note:** Two-lane highways only support Level and Rolling terrain types per HCM 2010 methodology.

## Level of Service Definitions

### Freeway and Multilane Highway LOS:
- **LOS A**: Free flow, density ≤ 11 pc/mi/ln
- **LOS B**: Reasonably free flow, density ≤ 18 pc/mi/ln
- **LOS C**: Stable flow, density ≤ 26 pc/mi/ln
- **LOS D**: Approaching unstable flow, density ≤ 35 pc/mi/ln
- **LOS E**: Unstable flow, density ≤ 45 pc/mi/ln (varies for multilane)
- **LOS F**: Forced flow, density > 45 pc/mi/ln

### Two-Lane Highway LOS:
- **Class I**: Based on worst of ATS and PTSF
- **Class II**: Based on PTSF only
- **Class III**: Based on PFFS only

## Step-by-Step Calculations

The application provides detailed step-by-step calculations for all facility types. Click the "View Step-by-Step Calculations" button in the results panel to see:
- All intermediate values
- Equations used
- Table lookups and interpolations
- Final calculations

## Design Mode

For Freeway and Multilane facilities, you can use the "Design for Target LOS" mode to:
1. Enter your traffic and geometric conditions
2. Select a target LOS (A through E)
3. The application will determine the minimum number of lanes required

## Examples

### Example 1: Freeway LOS Calculation
- Volume: 4000 veh/h (directional)
- PHF: 0.92
- Lanes: 3 per direction
- Trucks: 6%, RVs: 0%
- Lane width: 12 ft
- Lateral clearance: 6 ft
- Ramp density: 1.5 ramps/mi
- Terrain: Level

**Result:** LOS C with density of 20.9 pc/mi/ln

### Example 2: Multilane Highway Design
- Volume: 3600 veh/h (directional)
- PHF: 0.94
- Target LOS: C
- Base FFS: 55 mi/h
- Lane width: 11 ft
- Access points: 12 per mile
- Terrain: Rolling

**Result:** 3 lanes per direction required

## Methodology

This application is based on:
- **Highway Capacity Manual (HCM 2010)**, Transportation Research Board
- **Traffic and Highway Engineering (2020)** by Hoel, Garber & Sarkar

All calculations follow the procedures outlined in Chapter 9 of HCM 2010 for:
- Basic freeway segments
- Multilane highways
- Two-lane highways

## Limitations

1. **Two-Lane Highways:** Only Level and Rolling terrain types are supported (per HCM 2010 methodology)
2. **Design Mode:** Not available for Two-Lane Highways
3. **Specific Grades:** The application uses general terrain PCEs. For specific upgrade/downgrade analysis, refer to HCM 2010 Chapter 9 for detailed procedures
4. **Units:** All inputs must be in Imperial units (feet, miles, mi/h)

## Troubleshooting

### Common Issues:

1. **"ValueError" or calculation errors:**
   - Ensure all numeric fields are filled
   - Check that percentages are reasonable (0-100)
   - Verify PHF is between 0 and 1

2. **Unexpected LOS results:**
   - Review input values for accuracy
   - Check that geometric data matches actual conditions
   - Verify terrain classification

3. **Design mode not finding solution:**
   - Try a lower target LOS
   - Check if volume is extremely high (may require more than 8 lanes)


## License

© 2025 Farbod Roshani. All rights reserved.

## References

1. Highway Capacity Manual (HCM 2010). Transportation Research Board, National Research Council, Washington, D.C., 2010.

2. Hoel, L.A., Garber, N.J., & Sarkar, R. (2020). Traffic and Highway Engineering. Cengage Learning.

## Support

For questions or issues, please refer to the HCM 2010 manual or the Traffic and Highway Engineering textbook for detailed methodology explanations.

## Version History

- **v1.0** - Initial release
  - Freeway analysis
  - Multilane highway analysis
  - Two-lane highway analysis
  - Step-by-step calculations
  - Design mode for freeways and multilane highways
  - Imperial units only

---

**Note:** This application is intended for educational and professional use in highway capacity analysis. Always verify results with official HCM 2010 procedures for critical design decisions.

