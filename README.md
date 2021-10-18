# Lego Price Scraper
This is a real simple scraper designed to take in a list of lego sets and return a pricing sheet.

## Format and Usage
Run the script from command line as such:
```bash
python scraper.py <input file>
```

The input file should be formatted as such:
\<SET NUMBER\> \<SET NAME\>

The returned pricing sheet is a formatted CSV with the following headers:

Set Number, Set Name, Used Value, Used Value Range, Retail Price
