# Emu-scripts
## A bunch of scripts to make uploads into EMu easier.

### date_extractor.py
Pulls all dates out of a column in an Excel workbook and reformats them to
UMA standards.

### digi_walk.py
Creates or amends an EMu upload sheet with multimedia items. Items for upload
must have a variant of the UMA identifier in the filename.

### exif_meta_embed.py
Crosswalks EMu metadata from an ODBC data source and embeds it as EXiF data into
images in a directory. Requires pyodbc and exiftool to be installed and on PATH.

### field_splitter.py
From a delimited spreadsheet, splits multi-valued table fields on a given delimiter
into separate columns so that EMu can ingest them correctly.

### upload_parse.py
Inspect a delimited upload sheet and optional location sheet for obvious
problems such as missing mandatory fields, incorrect date formats etc.
