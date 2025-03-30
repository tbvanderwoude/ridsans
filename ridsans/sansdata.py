import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from math import pi as pi
import re
from pathlib import Path

active_w_pixels = 552
cropped_extent = [235, 235 + active_w_pixels, 239, 239 + active_w_pixels]
crop_y_start, crop_y_end, crop_x_start, crop_x_end = cropped_extent

# The numbers represent FZZ in the 4 sample positions
# This is needed because FZZ is not always present in the .mpa files
FZZ_map = {"Q1": 9742.34272, "Q2": 7427.9968, "Q3": 3422.98528, "Q4": 1432.00036}

# From velocity selector characterization
a_fit = 1.27085576e05  # AA / RPM
b_fit = 3.34615760e-03  # AA


def rpm_to_lambda(x, a, b):
    return a / x + b


rpm_converter = lambda rpm: rpm_to_lambda(rpm, a_fit, b_fit)

def rebin2d(arr,n):
    rows, cols = arr.shape
    if rows % n != 0 or cols % n != 0:
        print(f"Array dimensions are not divisible by {n}, trimming remainder")
        x_lim = (rows//n) * n
        y_lim = (cols//n) * n
        arr = arr[:x_lim,:y_lim]
    return arr.reshape(rows//n, n, cols//n, n).sum(axis=(1,3))

def get_closest_Q_range(uncorrected_distance, tolerance=5):
    """Determines what the Q range is of the measurement"""
    # Find the key-value pair with the smallest absolute difference
    closest_key, closest_value = min(
        FZZ_map.items(), key=lambda item: abs(uncorrected_distance - item[1])
    )
    error = abs(uncorrected_distance - closest_value)

    if error > tolerance:
        raise ValueError(
            f"Measured distance {uncorrected_distance} mm is off by {error:.2f} mm, "
            f"which exceeds the allowed tolerance of {tolerance} mm."
        )

    return closest_key, error


active_w = 0.6  # m
active_h = 0.6  # m


def plot_I(I, plot_centre_cross=True, extent=cropped_extent):
    """
    Plot the 2D intensity data.
    """
    norm = mcolors.LogNorm(vmin=np.min(I[I > 0]), vmax=np.max(I))
    plt.figure()

    # extent = [233, 233 + active_w_pixels, 233, 233 + active_w_pixels]

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


def plot_projections(I, extent=cropped_extent):
    """
    Plot combined integrated intensities along both X and Y axes with both pixel and distance representations.
    """
    fig, axes = plt.subplots(
        2, 1, figsize=(12, 12)
    )  # Arrange plots in 2 rows, 1 column
    print(extent)
    # Plot integrated intensity along X-axis (summed over Y) in pixels
    integrated_intensity_x = np.sum(I, axis=0)
    integrated_intensity_y = np.sum(I, axis=1)

    ax = axes[0]
    x_values_pixels = np.arange(integrated_intensity_x.size) + extent[0]
    ax.plot(x_values_pixels, integrated_intensity_x)
    ax.set_xlim(extent[0], extent[1])

    ax.set_title("Intensity integrated over y-axis")
    ax.set_xlabel("$x$ (pixels)")
    ax.set_ylabel(r"$I(x)$")
    ax.legend()

    ax = axes[1]
    y_values_pixels = np.arange(integrated_intensity_y.size) + extent[2]
    ax.plot(y_values_pixels, integrated_intensity_y)
    ax.set_xlim(extent[2], extent[3])
    ax.set_title("Intensity integrated over x-axis")
    ax.set_xlabel(r"$y$ (pixels)")
    ax.set_ylabel(r"$I(y)$")
    ax.legend()

    plt.tight_layout()
    plt.show()


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
    def __init__(
        self, filename, log_process=False, keep_all_counts=False, rebin = True, image_code="CDAT2"
    ):
        self.monitor_value = None
        self.log_process = log_process
        self.keep_all_counts = keep_all_counts
        self.image_code = image_code
        self.rebin = rebin
        self.log(f"=== Loading RIDSANS measurement file: {filename} ===")
        self.filename = filename
        self.name = Path(filename).stem
        if keep_all_counts:
            self.pixel_count = 1024 * 1024
        else:
            if self.rebin:
                self.pixel_count = active_w_pixels * active_w_pixels//16
            else:
                self.pixel_count = active_w_pixels * active_w_pixels
        self.load_data(filename)

        self.log(f"Pixel count: {self.pixel_count}")

        # Define the distances based on the provided geometry (in mm)
        self.distances = {
            "D_to_DS": 1320 + 0,  # Distance from diaphragm to sample, + PosFzz
            "DS_to_S": 1320,  # Distance from DS to Sample
            "DS_to_KB3": 2802,  # Distance from Sample to KB3
            "DS_to_KB2": 4793,  # Distance from KB3 to KB2
            "DS_to_KB1": 8798,  # Distance from KB2 to KB1
            "DS_to_PB1": 11606,  # Distance from KB1 to P01
        }

    def log(self, s):
        if self.log_process:
            # This could instead be written to a file
            print(s)

    def load_data(self, filename):
        with open(filename) as f:
            lines = list(f)
        self.filename = filename
        self.load_scaler_a(lines)

        # https://stackoverflow.com/questions/2361426/get-the-first-item-from-an-iterable-that-matches-a-condition
        header_end = next(
            (x[0] for x in enumerate(lines) if x[1].startswith("[MCS8A A]")), None
        )
        if header_end == 0:
            self.log("No header was found, assuming this is a background measurement")
            for key in FZZ_map.keys():
                if key in self.filename:
                    self.d = (FZZ_map[key] + 1320) / 1e3
                    self.Q_range_index = key[1:]
        else:
            self.header_params = {}
            for i in range(header_end):
                split_line = lines[i].split("=")
                name, value = split_line[0], split_line[1].strip()
                self.header_params[name] = value
            uncorrected_distance = self.load_distance()  # mm
            # Finds the key matching the Q range (Q1 - Q4)
            closest_key, _ = get_closest_Q_range(uncorrected_distance)
            # Extracts the Q range (value from 1 - 4)
            self.Q_range_index = closest_key[1:]
            self.d = (uncorrected_distance + 1320) / 1e3  # [m] 1320 is the offset
            self.log("Detector to sample distance: {:.4g} m".format(self.d))

            self.velocity_selector_speed = self.load_velocity_selector()  # RPM
            if self.velocity_selector_speed == 0:
                self.log(
                    "Velocity selector RPM appears to be 0, is this a background measurement?"
                )
                self.L0 = None
            else:
                self.L0 = rpm_converter(self.velocity_selector_speed)
                self.log("lambda_0: {:.4g} Å".format(self.L0))
            # Create beamstop
            bs_large_x = float(self.header_params["BSXL"]) / 1e3  # m
            bs_small_x = float(self.header_params["BSXS"]) / 1e3  # m
            bs_y = float(self.header_params["BSY"]) / 1e3  # m
            self.beamstop = Beamstop(bs_large_x, bs_small_x, bs_y)

            self.sample = ""
            if "Sample" in self.header_params:
                self.sample = self.header_params["Sample"]
            self.log(f"Sample: {self.sample}")

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
            if id == self.image_code:
                CDAT2_offset = line
                assert int(length) == CDAT2_length
        cdat2 = np.array(
            lines[CDAT2_offset + 1 : CDAT2_offset + 1 + CDAT2_length], dtype=np.int16
        )
        # Reshape 1D 1048576 array to 2D 1024 x 1024
        cdat_2d = np.reshape(cdat2, (1024, 1024))
        # Transpose it to switch axes (I assume because it was column-major and needs to be row-major)
        # self.raw_intensity = np.transpose(cdat2_2d)
        if self.keep_all_counts:
            self.raw_intensity = np.flip(cdat_2d, axis=0)
        else:
            # Selects only active detector region pixels (a 552 x 552 region)
            self.raw_intensity = np.flip(
                cdat_2d[crop_y_start:crop_y_end, crop_x_start:crop_x_end],
                axis=0,
            )
            if self.rebin:
                self.raw_intensity = rebin2d(self.raw_intensity, 4)
            rows, cols = self.raw_intensity.shape
            self.log(f"Dimension of clipped counts: {rows} x {cols}")
            assert self.pixel_count == len(self.raw_intensity.flatten())

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
                self.log("\tMeasurement time: {:.4g} s".format(self.measurement_time))
                self.log("\tTotal counts: {}".format(self.measurement_count))
                if self.monitor_value is not None:
                    self.log("\tMonitor counts: {}".format(self.monitor_value))
                    self.log(
                        "\tMonitor intensity: {:.4g} n/s".format(
                            self.monitor_value / self.measurement_time
                        )
                    )

                    self.count_ratio = self.measurement_count / self.monitor_value
                    self.log(
                        "\tDetector/monitor ratio: {:.4g}".format(self.count_ratio)
                    )

                if self.monitor_value is not None:
                    self.I_0 = self.monitor_value / self.measurement_time
                else:
                    self.I_0 = self.measurement_count / self.measurement_time
                self.log(
                    "\tAverage detector intensity: {:.4g} n/s".format(
                        self.measurement_count / self.measurement_time
                    )
                )

        self.I = self.raw_intensity / self.measurement_time
        # Use Poisson statistics for each pixel
        self.dI = np.sqrt(self.raw_intensity) / self.measurement_time

    def load_scaler_a(self, lines):
        # Locate the [SCALER A] header in the file
        scaler_a_index = next(
            (i for i, line in enumerate(lines) if line.strip() == "[SCALER A]"), None
        )
        if scaler_a_index is None:
            self.log("No [SCALER A] header found.")
            return

        # Initialize dictionary to store the scaler parameters
        # Currenty only sc#01 is used but this could change in the future
        scaler_a_params = {}

        for line in lines[scaler_a_index + 1 :]:
            line = line.strip()
            if not line or line.startswith("["):
                break
            if "=" in line:
                key, value = line.split("=", 1)
                value = value.split(";")[0].strip()
                scaler_a_params[key.strip()] = value

        # Store the extracted scaler data in an instance attribute
        self.scaler_a_data = scaler_a_params

        # Extract the most important value, sc#01, converting to integer if possible
        if "sc#01" in scaler_a_params:
            try:
                monitor_reading = int(scaler_a_params["sc#01"])
                if monitor_reading != 0:
                    self.monitor_value = monitor_reading
                else:
                    self.log("sc#01 = 0, ignoring")
            except ValueError:
                raise ValueError(
                    "Could not convert sc#01 to number, check the value in the file for irregularities"
                )
        else:
            self.log("Could not find sc#01")

    def load_float_with_default(self, name, default):
        if name in self.header_params:
            return float(self.header_params[name])
        else:
            self.log(
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
        extent = cropped_extent
        if self.keep_all_counts:
            extent = [0, 1024, 0, 1024]
        plot_projections(self.I, extent)

    def plot_2d(self, plot_centre_cross=True):
        extent = cropped_extent
        if self.keep_all_counts:
            extent = [0, 1024, 0, 1024]
        plot_I(self.I, plot_centre_cross, extent)


if __name__ == "__main__":
    for i in range(1, 5):
        print(f"\n\n============= Q = {i} =============")
        sample = SansData(
            f"test-data/empty_beam_no_sample_Q{i}.mpa",
            log_process=True,
        )
        sample = SansData(
            f"test-data/transmission_0_25mm_glassy_C_Q{i}.mpa",
            log_process=True,
        )
        sample = SansData(
            f"test-data/scattering_0_25mm_glassy_C_Q{i}.mpa", log_process=True
        )
