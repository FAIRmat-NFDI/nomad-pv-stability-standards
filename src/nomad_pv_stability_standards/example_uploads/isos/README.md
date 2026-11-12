# ISOS stability standards

The ISOS protocols for the stability of perovskite solar cells, one entry per protocol
and one per variant, as `StabilityStandard` entries:

- Khenkin, M. V., Katz, E. A., Abate, A. *et al.* "Consensus statement for stability
  assessment and reporting for perovskite photovoltaics based on ISOS procedures."
  *Nature Energy* **5**, 35–49 (2020). <https://doi.org/10.1038/s41560-019-0529-5>
- The ISOS procedures it builds on, which also describe the temperature cycles: Reese,
  M. O. *et al.* "Consensus stability testing protocols for organic photovoltaic
  materials and devices." *Solar Energy Materials and Solar Cells* **95**, 1253–1267
  (2011). <https://doi.org/10.1016/j.solmat.2011.01.036>

Page numbers, Table 1, Table 2 and Fig. 3 in the notes refer to Khenkin et al.

## What is here

| Family | What it stresses | Protocols |
|---|---|---|
| ISOS-D | Dark storage | D-1, D-2, D-3 |
| ISOS-V | Electrical bias in the dark | V-1, V-2, V-3 |
| ISOS-L | Light soaking under a solar simulator | L-1, L-2, L-3 |
| ISOS-O | Outdoor exposure to sunlight | O-1, O-2, O-3 |
| ISOS-T | Thermal cycling in the dark | T-1, T-2, T-3 |
| ISOS-LC | Light–dark cycling | LC-1, LC-2, LC-3 |
| ISOS-LT | Solar-thermal cycling | LT-1, LT-2, LT-3 |
| ISOS-I | The protocols of Table 2 in an inert atmosphere | D-1I, D-2I, V-1I, V-2I, L-1I, L-2I, T-1I, T-2I, T-3I, LC-1I, LC-2I, LC-3I |

The files are in one folder per family and one per protocol, e.g.
`ISOS-L/ISOS-L-2/`; the inert protocols are in `ISOS-I/`. Every protocol has one entry
without a variant, e.g. `ISOS-L-2`. It holds the
conditions all its variants share and lists the options in its notes. Where the
protocol offers options, such as 65 °C or 85 °C, each combination is a variant of its
own, e.g. `ISOS-L-2 (65 °C, MPP)`. Search for the name of a protocol to find all its
variants.

## How the entries are written

- **Only what the standard states.** A value the paper does not state stays empty, e.g.
  the interval of the J–V scans or the oxygen limit of an inert atmosphere. The notes
  quote the paper where it is read.
- **Channels.** Each entry lists its conditions in three channels: thermal,
  opto-electrical (light and electrical state together) and atmosphere. Each variable
  says how it is fixed (`control`) and whether it is recorded (`monitored`).
- **ISOS-LC-3 is provisional.** The paper gives its humidity as "< 50%" (Table 1) and as
  "held at 50%" (p. 39); both readings are variants until this is settled.
- **ISOS-I** entries are the protocols they are based on, in an inert atmosphere, with
  no oxygen or water limit, since the paper states none.

## Using the catalogue

An administrator creates this example upload once and publishes it, so that everyone
references the same entries. Copies created by other users stay unpublished unless they
publish them. A corrected or extended catalogue is published as a new upload; references
to the old one keep pointing to the entries they were made with.
