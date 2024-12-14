# Applying SANS theory for expressing measurements in real units
Here an overview is provided to have relevant theoretical en Mantid (i.e. numerical) information in one place.
# Theory
According to [1], with each $I$ representing counts normalized by measurement time (and scaled to com pensate any relative difference in attenuation),

$$I_c = \frac{1}{T_sT_c}(I_{sample}-I_{background})-\frac{1}{T_c}(I_{can} - I_{background})$$
Here $T_s, T_c$ represent transmission factors.

It furthermore states that 
$$\dfrac{d\sigma}{d\Omega} = \frac{I_c}{I_0}\frac{1}{t}\dfrac{1}{d\Omega}$$
where $I_0$ represents the integrated intensity of the direct (empty) beam measurement. 

# Mantid
[2] indicates that the unit of the output workspace of the Q1D (and Qxy) algorithm is 1/cm, so that it represents a macroscopic cross section. 

[1]: 'Graphical reduction and analysis small-angle
neutron scattering program: GRASP'

[2]: Q1D description https://docs.mantidproject.org/nightly/algorithms/Q1D-v2.html

# Mantid
