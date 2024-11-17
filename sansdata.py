import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.optimize import curve_fit
from math import pi as pi
import re


def plot_I(I, plot_centre_cross = True):
    """
    Plot the 2D intensity data.
    """
    norm = mcolors.LogNorm(vmin=np.min(I[I > 0]), vmax=np.max(I))
    plt.figure()

    extent = [0, 1024, 0, 1024]
    plt.imshow(
        I, cmap="viridis", extent=extent, norm=norm, aspect="auto"
    )  # cmap defines the color map (optional)
    plt.colorbar(label="I")
    plt.xlabel("Pixel X")
    plt.ylabel("Pixel Y")
    if plot_centre_cross:
        plt.axvline(512, linestyle="--", color="red")
        plt.axhline(512, linestyle="--", color="red")
    plt.show()

def plot_projections(I):
    """
    Plot combined integrated intensities along both X and Y axes with both pixel and distance representations.
    """
    fig, axes = plt.subplots(
        2, 1, figsize=(12, 12)
    )  # Arrange plots in 2 rows, 1 column

    # Plot integrated intensity along X-axis (summed over Y) in pixels
    integrated_intensity_x = np.sum(I, axis=0)
    integrated_intensity_y = np.sum(I, axis=1)

    ax = axes[0]
    x_values_pixels = np.arange(integrated_intensity_x.size)
    ax.plot(x_values_pixels, integrated_intensity_x)

    ax.set_title("Intensity integrated over y-axis")
    ax.set_xlabel("$x$ (pixels)")
    ax.set_ylabel(r"$I(x)$")
    ax.legend()

    ax = axes[1]
    y_values_pixels = np.arange(integrated_intensity_y.size)
    ax.plot(y_values_pixels, integrated_intensity_y)

    ax.set_title("Intensity integrated over x-axis")
    ax.set_xlabel(r"$y$ (pixels)")
    ax.set_ylabel(r"$I(y)$")
    ax.legend()

    plt.tight_layout()
    plt.show()


# The numbers represent FZZ in the 4 sample positions
# This is needed because FZZ is not always present in the .mpa files
# Why do you ask? I wish I knew
FZZ_map = {
    'Q1': 9742.34272,
    'Q2': 7427.9968,
    'Q3': 3422.98528,
    'Q4': 1432.00036
}

rpm = np.array(
    [25450, 23100, 21200, 14150, 12700, 11550, 10600, 9750, 9100]
)  # from the test data
wavelengths = np.array([5.0, 5.5, 6.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0])
sorted_indices = np.argsort(rpm)
sorted_wavelengths = wavelengths[sorted_indices]
sorted_rpm = rpm[sorted_indices]


# Fits the mapping from RPM to wavelength
def rpm_to_lambda0(x, a, b):
    return a / x + b

popt, _ = curve_fit(rpm_to_lambda0, sorted_rpm, sorted_wavelengths)

rpm_converter = lambda rpm: rpm_to_lambda0(rpm, *popt)

active_w = 0.15 # m
active_h = 0.15 # m

class Beamstop:
    def __init__(self, large_x, small_x, y):
        self.large = abs(large_x) <= abs(small_x)
        if self.large:
            w_pixels = 62  # pixels
            h_pixels = 62  # pixels

            # TODO: substitute actual value when detector specifications arrive
            pixel_size = 0.000275  # m
            self.w = w_pixels * pixel_size  # m
            self.h = h_pixels * pixel_size  # m

            # TODO: get actual values that map x, y to BS centre
            # (and relevant geometry for actual calculation of projection on detector)
            self.x = large_x + self.w  # m
            self.y = y - self.h / 6  # m
        else:
            pass
            # raise (NotImplementedError("Size of small beam stop is unknown"))


class SansData:
    def __init__(self, filename):
        print(f"=== Loading RIDSANS measurement file: {filename} ===")
        self.filename = filename
        self.load_data(filename)

        # Define the distances based on the provided geometry (in mm)
        self.distances = {
            "D_to_DS": 1320 + 0,  # Distance from diaphragm to sample, + PosFzz
            "DS_to_S": 1320,  # Distance from DS to Sample
            "DS_to_KB3": 2802,  # Distance from Sample to KB3
            "DS_to_KB2": 4793,  # Distance from KB3 to KB2
            "DS_to_KB1": 8798,  # Distance from KB2 to KB1
            "DS_to_PB1": 11606,  # Distance from KB1 to P01
        }

    def load_data(self, filename):
        with open(filename) as f:
            lines = list(f)
        self.filename = filename

        # https://stackoverflow.com/questions/2361426/get-the-first-item-from-an-iterable-that-matches-a-condition
        header_end = next(
            (x[0] for x in enumerate(lines) if x[1].startswith("[MCS8A A]")), None
        )
        if header_end == 0:
            print("No header was found, assuming this is a background measurement")
            for key in FZZ_map.keys():
                if key in self.filename:
                    self.d = (FZZ_map[key] + 1320) / 1e3
        else:
            self.header_params = {}
            for i in range(header_end):
                split_line = lines[i].split("=")
                name, value = split_line[0], split_line[1].strip()
                self.header_params[name] = value

            self.d = (self.load_distance() + 1320) / 1e3  # [m] 1320 is the offset
            print("Detector to sample distance: {:.4g} m".format(self.d))

            self.velocity_selector_speed = self.load_velocity_selector()  # RPM
            self.L0 = rpm_converter(self.velocity_selector_speed)
            print("lambda_0: {:.4g} Å".format(self.L0))
            # Create beamstop
            bs_large_x = float(self.header_params["BSXL"]) / 1e3  # m
            bs_small_x = float(self.header_params["BSXS"]) / 1e3  # m
            bs_y = float(self.header_params["BSY"]) / 1e3  # m
            self.beamstop = Beamstop(bs_large_x, bs_small_x, bs_y)

            self.sample = ""
            if "Sample" in self.header_params:
                self.sample = self.header_params["Sample"]
            print(f"Sample: {self.sample}")

        # Extract CDAT2 array from remaining file as raw detector counts

        # Measurement data sequences look like [CDAT2,1048576] (regular expression: \[.DAT.,\d* \])
        r = re.compile("\[.DAT.,\d* \]")
        sequence_headers = list(filter(lambda x: r.match(x[1]), enumerate(lines)))
        # The CDAT2 count sequence is used to read 1024 x 1024 values
        data_start = None
        CDAT2_offset = None
        CDAT2_length = 1048576  # 1024 x 1024
        for line, sequence_header in sequence_headers:
            (id, length) = re.findall(r"\[([0-9a-zA-Z]+),(\d+) \]", sequence_header)[0]
            if id == "TDAT0":
                data_start = line
            if id == "CDAT2":
                CDAT2_offset = line
                assert int(length) == CDAT2_length
        cdat2 = np.array(
            lines[CDAT2_offset + 1 : CDAT2_offset + 1 + CDAT2_length], dtype=np.int16
        )
        # Reshape 1D 1048576 array to 2D 1024 x 1024
        cdat2_2d = np.reshape(cdat2, (1024, 1024))
        # Transpose it to switch axes (I assume because it was column-major and needs to be row-major)
        # self.raw_intensity = np.transpose(cdat2_2d)
        self.raw_intensity = np.flip(cdat2_2d,axis=0)
        

        # The following extracts the measurement time and total counts from under the [CHN2] header
        r = re.compile("\[CHN\d*\]")
        sequence_headers = list(
            filter(lambda x: r.match(x[1]), enumerate(lines[:data_start]))
        )
        for line, sequence_header in sequence_headers:
            id = re.findall(r"\[(CHN\d*)\]", sequence_header)[0]
            if id == "CHN2":
                report_str = "".join(lines[line + 2 : line + 6]).strip()
                numbers = re.findall(r"\d+\.\d+|\d+", report_str)
                self.measurement_time = float(numbers[0])
                self.measurement_count = int(numbers[1])
                print("\tMeasurement time: {:.4g} s".format(self.measurement_time))
                print("\tTotal counts: {}".format(self.measurement_count))
                self.I_0 = (
                    self.measurement_count / self.measurement_time
                )
                print(
                    "\tAverage detector intensity: {:.4g} counts/s".format(
                        self.I_0
                    )
                )
        
        self.I = self.raw_intensity / self.measurement_time
        # Use Poisson statistics for each pixel
        self.dI = np.sqrt(self.raw_intensity) / self.measurement_time

    def load_float_with_default(self, name, default):
        if name in self.header_params:
            return float(self.header_params[name])
        else:
            print(
                f"Warning: parameter {name} not found, using default value of {default}"
            )
            return default

    def load_distance(self):
        return self.load_float_with_default("FZZ", 3400)

    def load_velocity_selector(self):
        return self.load_float_with_default("SpeedVS", 21506)

    def plot_integrated_intensity(
        self, intensity=None, axis=0, title="Integrated Intensity", filename=None
    ):
        plot_projections(self.I)

    def plot_2d(self, plot_centre_cross = True):
        plot_I(self.I,plot_centre_cross)


if __name__ == "__main__":
    sample = SansData("data/memb_BS_Q1_6_0Ang.mpa")
    bg = SansData("data/08_07_24_backG_1202s_reactor_on.mpa")
