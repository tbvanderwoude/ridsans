import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.optimize import curve_fit
from math import pi as pi
import re


class SansData:
    def __init__(self, filename):
        # Initialization with detector settings and file loading
        self.filename = filename
        self.setup_detector_geometry()
        self.load_data(filename)
        self.process_data()
        self.velocity_selector_speed = self.load_velocity_selector()
        self.L0 = self.calculate_lambda_from_velocity(
            self.velocity_selector_speed
        )  # Calculate lambda from velocity
        print(f"lambda_0: {self.L0}")

        # Define the ranges and beam stop information here
        # self.x_ranges = [(400, 450), (450, 600)]
        # self.y_ranges = [(200, 250), (250, 300)]
        # self.beam_stop_range_x = (430, 480)
        # self.beam_stop_range_y = (230, 260)
        # -> Beam stop appears to have w x h of 50 x 30 (at least projected onto detector)

        # Initialize the attributes with default values
        self.delta_omega = 1.0  # Example value
        self.d_sample = 0.05  # Example value
        self.i0_lambda = 1.0  # Example value
        self.transmission_lambda = 1.0  # Example value
        # Define the distances based on the provided geometry (in mm)
        self.distances = {
            "D_to_DS": 1320 + 0,  # Distance from diaphragm to sample, + PosFzz
            "DS_to_S": 1320,  # Distance from DS to Sample
            "DS_to_KB3": 2802,  # Distance from Sample to KB3
            "DS_to_KB2": 4793,  # Distance from KB3 to KB2
            "DS_to_KB1": 8798,  # Distance from KB2 to KB1
            "DS_to_PB1": 11606,  # Distance from KB1 to P01
        }
        # Define the apertures sizes (in mm) for each diaphragm
        self.apertures = {
            "D": 10,  # Aperture size for diaphragm D
            "DS": 10,  # Aperture size for DS
            "S": 10,  # Aperture size for Sample
            "KB3": 10,  # Aperture size for KB3
            "KB2": 10,  # Aperture size for KB2
            "KB1": 10,  # Aperture size for KB1
            "PB1": 10,  # Aperture size for P01
        }

    def load_data(self, filename):
        with open(filename) as f:
            lines = list(f)
        self.filename = filename

        # https://stackoverflow.com/questions/2361426/get-the-first-item-from-an-iterable-that-matches-a-condition
        header_end = next((x[0] for x in enumerate(lines) if x[1].startswith('[MCS8A A]')), None)

        print(header_end)
        self.header_params = {}
        for i in range(header_end):
            split_line = lines[i].split("=")
            name, value = split_line[0], split_line[1].strip()
            self.header_params[name] = value

        self.d = (self.load_distance() + 1320) / 1e3  # [m] 1320 is the offset
        
        self.sample = ""
        if "Sample" in self.header_params:
            self.sample = self.header_params["Sample"]
        print(f"Sample: {self.sample}")

        # Measurement data sequences look like [CDAT2,1048576] (regular expression: \[.DAT.,\d* \])
        r = re.compile("\[.DAT.,\d* \]")
        sequence_headers = list(filter(lambda x: r.match(x[1]), enumerate(lines)))
        # The CDAT2 count sequence is used to read 1024 x 1024 values
        CDAT2_offset = -1
        CDAT2_length = 1048576  # 1024 x 1024
        for line, sequence_header in sequence_headers:
            (id, length) = re.findall(r"\[([0-9a-zA-Z]+),(\d+) \]", sequence_header)[0]
            if id == "CDAT2":
                CDAT2_offset = line
                assert int(length) == CDAT2_length
        cdat2 = np.array(
            lines[CDAT2_offset + 1 : CDAT2_offset + 1 + CDAT2_length]
        ).astype(int)
        # Reshape 1D 1048576 array to 2D 1024 x 1024
        cdat2_2d = np.reshape(cdat2, (1024, 1024))
        # Transpose it to switch axes (I assume because it was column-major and needs to be row-major)
        self.raw_intensity = np.transpose(cdat2_2d)
        print(f"{self.xmin}:{self.xmax}, {self.ymin}:{self.ymax}")
        self.intensity = np.transpose(
            cdat2_2d[self.xmin : self.xmax, self.ymin : self.ymax]
        )
        print(f"self.intensity shape: {self.intensity.shape}")

    def process_data(self):
        self.i_s = np.sum(self.intensity, axis=0)
        # Any additional data processing
        pass

    def setup_detector_geometry(self):
        # Detector geometry setup

        # Boundaries for detector (TODO: figure out why these are the specific numbers)
        self.xmin = 275
        self.xmax = 750
        self.ymin = 50
        self.ymax = 1024 - 50

        self.y = 1024 - 100
        self.y_pixel_size = 0.5 / self.y  # ypixel size [m]
        self.x = 1024 - 275 - 274  # number of x pixels #changed from 225 to 275
        self.x_pixel_size = 0.5 / self.x  # xpixel size [m]
        self.n_sectors = 6
        # Sample to detector distance is FZZ +1320
        print(
            f"Pixel size X: {self.x_pixel_size} m, Pixel size Y: {self.y_pixel_size} m"
        )

    def load_float_with_default(self, name, default):
        if name in self.header_params:
            return float(self.header_params[name])
        else:
            print(f"Warning: parameter {name} not found, using default value of {default}")
            return default
        
    def load_distance(self):
        return self.load_float_with_default('FZZ', 3400)
    
    def load_velocity_selector(self):
        return self.load_float_with_default('SpeedVS', 21506)

    def calculate_lambda_from_velocity(self, velocity):
        rpm = np.array(
            [25450, 23100, 21200, 14150, 12700, 11550, 10600, 9750, 9100]
        )  # from the test data
        wavelengths = np.array([5.0, 5.5, 6.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0])
        sorted_indices = np.argsort(rpm)
        sorted_wavelengths = wavelengths[sorted_indices]
        sorted_rpm = rpm[sorted_indices]

        # Fits the mapping from RPM to wavelength
        def fit_func(x, a, b):
            return a / x + b

        # Perform linear fit
        popt, _ = curve_fit(fit_func, sorted_rpm, sorted_wavelengths)
        interpolated_lambda = fit_func(velocity, *popt)
        # print(f"Interpolated lambda: {interpolated_lambda} Å for velocity {velocity} RPM")
        return interpolated_lambda

    def plot_integrated_intensity(
        self, data=None, axis=0, title="Integrated Intensity", filename=None
    ):
        """
        Plot combined integrated intensities along both X and Y axes with both pixel and distance representations.
        """
        fig, axes = plt.subplots(
            2, 1, figsize=(12, 12)
        )  # Arrange plots in 2 rows, 1 column

        # Plot integrated intensity along X-axis (summed over Y) in pixels
        data = self.raw_intensity
        integrated_intensity_x = np.sum(data, axis=0)
        integrated_intensity_y = np.sum(data, axis=1)

        ax = axes[0]
        x_values_pixels = np.arange(integrated_intensity_x.size)
        ax.plot(x_values_pixels, integrated_intensity_x)

        # ax.set_xlim(200, 300)
        ax.set_title("Integrated Intensity over X-axis (Summed over Y)")
        ax.set_xlabel("X (pixels)")
        ax.set_ylabel("Integrated Intensity")
        ax.legend()

        # Plot integrated intensity along Y-axis (summed over X) in pixels
        ax = axes[1]
        y_values_pixels = np.arange(integrated_intensity_y.size)
        ax.plot(y_values_pixels, integrated_intensity_y)

        # ax.set_xlim(300, 600)
        ax.set_title("Integrated Intensity over Y-axis (Summed over X)")
        ax.set_xlabel("Y (pixels)")
        ax.set_ylabel("Integrated Intensity")
        ax.legend()

        plt.tight_layout()
        plt.show()

    def plot_2d(self):
        """
        Plot the 2D intensity data.
        """
        data = self.raw_intensity
        norm = mcolors.LogNorm(
            vmin=np.min(data[data > 0]), vmax=np.max(data)
        )
        plt.figure()
        plt.pcolormesh(data, norm=norm, shading="gouraud")
        plt.colorbar(label="Intensity")
        plt.xlabel("Pixel X")
        plt.ylabel("Pixel Y")
        plt.show()
        plt.figure()
        plt.pcolormesh(data, norm=norm, shading="gouraud")
        plt.colorbar(label="Intensity")
        plt.xlabel("Pixel X")
        plt.ylabel("Pixel Y")
        plt.xlim(200, 300)
        plt.ylim(350, 600)
        plt.show()


if __name__ == "__main__":
    sample = SansData("data/sans000422.mpa")
