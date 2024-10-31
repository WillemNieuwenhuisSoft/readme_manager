# BioSpace readme file viewer

## Purpose

Control and simple management of metadata stored in `readme` text files.
`Readme` metadata files are meant to describe data files or documents.
The `readme` metadata files are located in the folder they describe or
where the data is located they describe.

## Features

- Use any folder with data/documents as root folder.
- User induced scan to find all `readme` files. This list is stored
  which is useful for large folder structures.
- A `readme` file is recognized as a metadata file when the name
  contains **readme** and the extension is **.txt**.
- Flat view of all `readme` files for easy access.
- Allow creation of new `readme` files anywhere in the tree; this can
  be an empty file or a file based on a template.
- Simple editing of `readme` file.
- List of recently opened projects/folders.

## Installation

The app is a python application and can be installed with pip:

```shell
pip install "git+https://github.com/WillemNieuwenhuisSoft/readme_manager.git"
```

This will also install all dependencies (pandas, xlsxwriter, openpyxl and scipy).

## Usage

```
usage: bioview

This app present a GUI allowing to find, view and edit `readme` text files in a directory tree.


```
