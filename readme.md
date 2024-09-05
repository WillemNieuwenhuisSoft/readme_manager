# BioSpace readme file viewer

## Installation
The app is a python application and can be installed with pip:

```shell
pip install anon_excel-1.0.0-py3-none-any.whl
```
This will also install all dependencies (pandas and scipy).

## Usage

```
usage: anonex [-h] [-a] [-c] [-o] [-s] [-t] [-x] folder

This app scans multiple sets of surveys. It offers an option to clean and store the survey data, and also an option to perform and store a T-test analysis. The T-test is only possible when both pre- and post- survey is available.
Optionally personal information is removed.

positional arguments:
  folder           Specify the folder with the excel report(s)

options:
  -h, --help       show this help message and exit
  -a, --anonymize  Anonymize personal data (default = No)
  -c, --color      Add colors in excel file with clean ranked data (default = No)
  -o, --overwrite  Overwrite existing excel outputs (default = No)
  -s, --strip      Strip leading s-char from s-number (default = No)
  -t, --ttest      Perform T-test calculation (default = No)
  -x, --clean      Save cleaned data (default = No)
```

