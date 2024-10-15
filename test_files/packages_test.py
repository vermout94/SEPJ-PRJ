# Method 1: Using pkg_resources and writing to a text file
import pkg_resources


def save_installed_packages_to_file(file_name="requirements.txt"):
    installed_packages = pkg_resources.working_set
    packages_list = sorted([f"{pkg.key}=={pkg.version}" for pkg in installed_packages])

    with open(file_name, 'w') as f:
        for package in packages_list:
            f.write(f"{package}\n")


if __name__ == "__main__":
    save_installed_packages_to_file()
    print("Packages saved to requirements.txt")
