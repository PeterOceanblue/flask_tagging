# Flask Tag Reporting

## Overview

The Flask Tag Reporting project is a web application designed to process CSV files, generate detailed PDF reports, and insert logos into PDFs. It utilises Flask for web server functionality and various Python libraries for data processing and visualisation.



## Installation

1. Clone the repository:

```bash
git clone <repository-url>
```

2. Install the required packages:

```bash
pip install -r requirements.txt
```
3. Ensure your db_init.py script is properly configured and run:

```bash
python3 db_population/db_init.py
```
This populates the database with the test_archive.csv file. 

To repopulate, delete instance/database.db and run command again.

Naming convention for the csv file needs to be test_archive.csv.

# Usage

```bash
python3 run.py
```

### Upload CSV File

Generates a CSV with the tagged test result run in the project root folder

#### How to use:

* Format must be in a csv
* First row of csv file is excluded in processing
* First column needs to contain the test IDs
* Second column needs to contain the the test verdicts


### Generate Test Results Overview PDF

Generates pdf report using tagged test run results.

#### How to use:

* Upload a CSV file containing the tagged test results from the previous Upload CSV File process.
* Fill in the project details including Test Plan, Project, Platform, Serial, Model, and Test Suite.
* Click 'Generate' to create the PDF.
* The PDF will be generated in the downloads folder.

### Insert Logo into PDF

#### How to use:

* Choose the PDF file you want to insert the logo into.
* Choose the logo file (PNG, JPG, JPEG) you want to insert.
* Click 'Insert Logo' to embed the logo into the PDF.

### Generate Tags Summary PDF

#### How to use:

* Upload a CSV file containing the tagged test results from the previous Upload CSV File process.
* Click 'Generate' to create the Tags Summary PDF in the root folder.

