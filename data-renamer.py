import os
import argparse


def rename_files_in_directory(directory):
    for filename in os.listdir(directory):
        # Build the full path to the file
        file_path = os.path.join(directory, filename)

        # Only process files (skip directories)
        if os.path.isfile(file_path):
            with open(file_path, "r") as file:
                for line in file:
                    if line.startswith("Sample="):
                        # Extract the sample name
                        sample_name = line.split("=", 1)[1].strip()
                        break
                else:
                    # If no 'Sample=' line is found, skip renaming
                    print(f"'Sample=' not found in {filename}. Skipping.")
                    continue

            # TODO: harden this properly to avoid future problems with special characters
            # Generate the new filename
            new_filename = f"{sample_name.replace('.', '_')}.mpa".replace(" ", "_")

            new_file_path = os.path.join(directory, new_filename)

            # Rename the file
            os.rename(file_path, new_file_path)
            print(f"Renamed '{filename}' to '{new_filename}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Rename files in a directory to their 'Sample=' name with .mpa extension."
    )
    parser.add_argument(
        "directory", type=str, help="Path to the directory containing files to rename."
    )

    args = parser.parse_args()

    # Call the function with the provided directory
    rename_files_in_directory(args.directory)
