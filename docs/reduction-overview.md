# Reduction overview
Basic steps for SANS data reduction. Derivative of [Graphical reduction and analysis small-angle
neutron scattering program: GRASP](https://doi.org/10.1107/S1600576723007379)

1. Load data into workspaces: scattering data, empty cell $I_s$, blocked beam $I_{bck}$ (background). It is important to also have quantities like sample thickness $t$, counting time etc.
2. Deadtime correction of detector using Poisson statistics (can be skipped at first, requires specific detector information)
3. Normalization and data scaling using acquisition time or beam monitor counts (and potential attenuator effect if used)
4. Masking of unwanted regions
5. Transmission calculations for sample and empty beam
6. Direct-beam intensity: Compute beam centre of mass from $I_0$ (empty-beam measurement)
7. Correction for backgrounds and absorption
8. Calibration to units of differential cross section. This translates $I(x,y)$ on each point of the detector to $d\sigma/d\Omega$. There are many corrections possible here, for instance for fluctuations in detector efficiency 

## Background
Transmission measurements are for the purpose of determining the total fraction of beam intensity that is transmitted. This makes it possible to derive $I(q)$ in true units, as this scales the integral of $I(q)$.  

ROI stands for region of interest