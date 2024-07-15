# PythonWebScrape

PythonWebScrape - Mercedes-Benz WebParts Scraper

## Introduction

PythonWebScrape is a Python-based web scraper designed to extract detailed parts data from the Mercedes-Benz WebParts system. It automates the login process, navigates through various catalog options, and collects relevant parts data, saving the output to CSV files.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Dependencies](#dependencies)
- [Configuration](#configuration)
- [Function Builds](#function-builds)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributors](#contributors)
- [License](#license)

## Installation

To install PythonWebScrape, ensure you have Python 3.6+ installed and then follow these steps:

1. Clone the repository:
   ```sh
   git clone https://github.com/adamhale-exe/PythonWebScrape.git
   ```
2. Change into the project directory:
   ```sh
   cd PythonWebScrape
   ```
3. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

To use PythonWebScrape, you need to provide a list of model numbers and a group number within the Python code. Run the script as follows:

```sh
python pwscrape.py
```

The script will attempt to log in to the Mercedes-Benz WebParts system, navigate through the catalog, and scrape the required data for the provided model numbers.

## Features

- **Automated Login**: Bypasses manual login by using stored credentials.
- **Data Scraping**: Collects detailed parts data including model number, category, group, sub-group, part number, description, price, and quantity.
- **Error Handling**: Logs errors encountered during the scraping process and saves them to a CSV file.
- **CSV Output**: Outputs the scraped data and error logs to CSV files for easy analysis.

## Dependencies

PythonWebScrape relies on the following Python libraries:

- `beautifulsoup4`
- `pandas`
- `playwright`
- `re` (standard library)

Ensure these dependencies are installed by running the provided `requirements.txt`.

## Configuration

Before running the script, ensure that the `credentials.py` file contains the necessary login details:

```python
# credentials.py
loginurl = 'your_login_url'
homeurl = 'your_home_url'
username = 'your_username'
password = 'your_password'
locationdivision = 'your_location_division'
locationsubdivision = 'your_location_subdivision'
```

## Function Builds

To facilitate faster development and testing, individual functions were initially developed separately and stored in the "function builds" folder. These functions were later incorporated into the main script once they were fully tested and optimized. You can find the standalone versions of these functions in the "function builds" folder for reference or further modification.

## Examples

To run the script and scrape data for a set of model numbers:

```python
# Example usage in the script
main([120010, 120110, 121010], 'Grp1')
```

This will start the scraping process for the specified model numbers and save the results to CSV files named with the group number and model numbers.

## Troubleshooting

If you encounter issues while running the script, consider the following steps:

- Ensure that all dependencies are properly installed.
- Verify that the login credentials in `credentials.py` are correct.
- Check the error logs saved in the CSV files for any specific issues related to the scraping process.
- Increase the timeout settings if the website is slow to respond.

## Contributors

- Adam Hale - [Profile](https://github.com/adamhale-exe)

## License

This project is licensed under the MIT License. See the LICENSE file for details.
