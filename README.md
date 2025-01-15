# ResearchDrive Utils

A collection of Python scripts to interact with the SURF Research Drive API, offering utilities for managing and reporting on project folders. Each script is designed to perform a specific function, such as generating reports, generating overview of access permissions, and creating new project folders following predefined naming conventions.

## Features

- **Generate Excel Table of Project Folders:** Retrieve all available project folders and save them as an Excel table.
- **Access Permissions Report:** Create an overview of folder and file permissions presented in an intuitive HTML table.
- **Create Project Folders:** Create new project folders following a predefined naming convention.

## Repository Structure

```
researchdrive-utils/
├── src/
|  ├── researchdrive.py                      # Python wrapper to interact with the SURF Research Drive API
|  ├── scripts/
|  |  ├── researchdrive_projectfolders.py       # Script to create an Excel table of project folders
|  |  ├── researchdrive_projectfolders.cfg.tmpl # Template config file for the project folders script
|  |  ├── researchdrive_report.py               # Script to generate an access permissions report
|  |  ├── researchdrive_create_projectfolder.py # Script to create a new project folder
|  |  ├── researchdrive_create_projectfolder.cfg.tmpl # Template config file for the create project folder script
```

## Development Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/researchdrive-utils.git
   cd researchdrive-utils
   ```

2. Install the package in editable mode from the current directory (including required dependencies):

   ```bash
   pip install -e .
   ```

3. Configure each script (except `researchdrive_report.py`) using the corresponding `.cfg.tmpl` template:
   - Rename the `.cfg.tmpl` file to `.cfg`.
   - obtain an API token and make sure `Reporting` is enabled in the SURF Research Drive Dashboard (see [SURF Research Drive wiki](https://servicedesk.surf.nl/wiki/display/WIKI/RD-Dashboard%3A+API))
   - Update the configuration with your credentials and desired settings.

## Usage

### 1. Generate Excel Table of Project Folders

```bash
python researchdrive_projectfolders.py -c researchdrive_projectfolders.cfg
```
- **Purpose:** Retrieves available project folders and saves an overview in an Excel table.
- **Configuration:** Ensure `researchdrive_projectfolders.cfg` is properly configured.

### 2. Create Access Permissions Report

```bash
python researchdrive_report.py -f "SURF Reporting.xlsx"
```
- **Purpose:** Generates a detailed HTML report of access permissions for folders and files per projectfolder.
- **Configuration:** Download an `SURF Reporting.xlsx` file from the Research Drive Reporting under `Projects` -> `Sharing`.

### 3. Create a New Project Folder

```bash
python researchdrive_create_projectfolder.py -c researchdrive_create_projectfolder.cfg
```
- **Purpose:** Creates a new project folder following a predefined naming convention.
- **Configuration:** Ensure `researchdrive_create_projectfolder.cfg` is properly configured.

## Configuration Files

Each script requires a configuration file in `.cfg` format to run. The repository provides `.cfg.tmpl` templates for each script. Follow these steps to use them:

1. Copy the template file and rename it (e.g., `researchdrive_projectfolders.cfg.tmpl` → `researchdrive_projectfolders.cfg`).
2. Edit the `.cfg` file to include the necessary settings, such as API tokens, folder paths, or other options.

## Building Executables with PyInstaller

To create standalone executable files for the scripts using **PyInstaller**, follow these instructions:

1. Install PyInstaller:
   
   ```bash
   pip install pyinstaller
   ```

2. Run the following command for each script to build a standalone executable:

   ```bash
   pyinstaller --onefile --icon=RDRIVE.png src/scripts/researchdrive_report.py
   ```

   Replace `src/scripts/researchdrive_report.py` with the relative path to the script you want to build.

   - **`--onefile`**: Creates a single, standalone executable file.
   - **`--icon=RDRIVE.png`**: Sets the icon for the executable file.

3. After running PyInstaller, the generated executable file will be available in the `dist/` directory.

### Example Commands:

To build executables for all scripts, run:

```bash
pyinstaller --onefile --icon=RDRIVE.png src/scripts/researchdrive_projectfolders.py
pyinstaller --onefile --icon=RDRIVE.png src/scripts/researchdrive_report.py
pyinstaller --onefile --icon=RDRIVE.png src/scripts/researchdrive_create_projectfolder.py
```

### Notes:

- Ensure that `RDRIVE.png` is in the main folder (same directory as `setup.py`).
- The resulting executable files will work independently of Python, making them easy to distribute.
- The resulting executable files only work on the platform they are build for.

## Usage with executables

### Example Commands Windows

```bash
researchdrive_projectfolders.exe -c researchdrive_projectfolders.cfg
researchdrive_report.exe -f "SURF Reporting.xlsx"
researchdrive_create_projectfolder.exe -c researchdrive_create_projectfolder.cfg
```

### Example Commands macOS

```bash
researchdrive_projectfolders -c researchdrive_projectfolders.cfg
researchdrive_report -f "SURF Reporting.xlsx"
researchdrive_create_projectfolder -c researchdrive_create_projectfolder.cfg
```

## Contributing

Contributions are welcome! If you have suggestions for improvements or additional features, feel free to open an issue or submit a pull request.

## License

This repository is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

