# Beginner-Friendly Sales Analysis Project

## What this project does

This project reads the existing `Sales_Analysis_Minimal_Dataset_1000_Records.xlsx`
workbook and displays an interactive sales dashboard in a web browser. You can
filter the records, compare sales and profit, review customer activity, check
data quality, and download the filtered records.

The dashboard reads the `Raw_Sales_Data` worksheet. It does not change or
replace the original Excel workbook. Put the workbook in the project folder
beside `app.py`, as it is now. The app also checks the optional `data` folder.
If the workbook is missing, the app displays the expected location.

The workbook says its records are synthetic sample data for learning, not real
customer information. No reference PDF was present in the project folder.

## Why sales analysis is useful

Sales analysis helps a business understand when sales happen, which products
and categories earn revenue or profit, and which customers return to buy again.
These results can help people ask better business questions. A chart shows a
pattern in the supplied data; it does not by itself prove why that pattern
happened.

## Project files

- `app.py` — Streamlit dashboard, filters, charts, tables, and downloads.
- `data_cleaning.py` — loads the source worksheet and prepares a cleaned copy.
- `analysis.py` — contains the KPI and summary calculations.
- `requirements.txt` — the four Python libraries used by the project.
- `Sales_Analysis_Minimal_Dataset_1000_Records.xlsx` — the existing source file;
  keep it beside `app.py`.

## Dataset columns

| Column | Meaning |
| --- | --- |
| Order ID | Identifier for an order. It is used to count distinct orders. |
| Order Date | Date on which the order was recorded. |
| Customer ID | Identifier used to count and compare customers. |
| Customer Name | Name associated with the customer ID. |
| Product | Product recorded on the transaction row. |
| Category | Product group, such as Clothing or Electronics. |
| Quantity | Number of units recorded on the row. |
| Unit Price (INR) | Price per unit, in Indian rupees. |
| Discount (%) | Discount percentage recorded for the row. |
| Sales (INR) | Sales amount recorded for the row, in Indian rupees. |
| Profit (INR) | Profit amount recorded for the row, in Indian rupees. |

This workbook does not contain a Region, City, State, or other location column,
so regional comparisons cannot be calculated.

## How the data is cleaned

The app reads `Raw_Sales_Data` into memory and works on a separate copy. It
standardizes column names, removes columns clearly marked as spreadsheet
indexes, trims extra spaces, standardizes the capitalization of names,
products, and categories, converts dates (including Excel date numbers), and
converts numeric text such as rupees with commas into numbers.

Only completely identical rows are removed; the first copy is kept. Missing
values are counted and displayed, not filled in. In particular, a missing
discount is never changed to zero. Rows are not removed just because a value
is missing. The original workbook is never written to by this application.

In the supplied workbook, the raw worksheet has 1,000 transaction rows. The
cleaning check found one exact duplicate row and six blank Discount values.
The dashboard reports its cleaning counts and missing-value summary when it
runs. Those discount values stay blank in the table and downloads.

## KPI definitions

All KPI cards use the records selected by the sidebar filters.

| KPI | Calculation |
| --- | --- |
| Total Sales | Sum of the `Sales (INR)` values in the selected rows. |
| Total Profit | Sum of the available `Profit (INR)` values in the selected rows. Missing profit values, if any, remain missing and are not invented. |
| Total Orders | Number of distinct, non-empty Order IDs. This avoids counting a multi-row order more than once. |
| Total Units Sold | Sum of the `Quantity` values in the selected rows. |
| Average Order Value | Total sales divided by the number of distinct selected Order IDs. |
| Profit Margin | Total profit divided by total sales, multiplied by 100. It is not an average of row-level margins. |
| Total Customers | Number of distinct, non-empty Customer IDs in the selected rows. |

## Dashboard charts and analysis

- **Monthly sales trend** adds sales by calendar month.
- **Monthly profit trend** adds available profit by calendar month.
- **Best- and lowest-performing months** are the months with the highest and
  lowest recorded sales in the selected data.
- **Yearly comparison** appears only when the selected dates include more than
  one calendar year.
- **Sales/profit by product and category** sums the corresponding amounts for
  each product or category.
- **Top 5 products** ranks products separately by total sales and total profit.
- **Quantity sold by product** sums recorded units for each product.
- **Top 10 customers by sales** ranks customers by sales amount.
- **Repeat-customer analysis** counts distinct Order IDs per Customer ID. A
  customer with more than one selected order is counted as a repeat customer.
- **Regional analysis** is shown only if the workbook has a recognized
  geographic column. The supplied workbook has none, so the dashboard explains
  why this comparison is unavailable.
- **Business insights** are calculated from the filtered records. They are
  not hardcoded examples or unsupported predictions.

The date, category, product, and customer filters, and a location filter when
geographic data exists, update the KPI cards, charts, analysis tables,
insights, cleaned-record table, and downloads. Use **Reset filters** to return
to all records. A message appears if the filters select no rows.

## Libraries in beginner-friendly terms

- **Python** runs the project.
- **Pandas** reads the worksheet, cleans columns, and groups data for analysis.
- **Streamlit** turns the Python code into a dashboard with filters and tables.
- **Plotly** creates charts that can be explored in the browser.
- **OpenPyXL** lets Pandas read and create Excel workbooks.

## Limitations

- The workbook is a synthetic learning dataset, not evidence about a real
  business.
- No geographic columns are available, so regional comparisons are not
  possible.
- Six Discount values in the supplied raw worksheet are blank. They remain
  blank; they are not changed to zero or estimated.
- The dashboard describes the values recorded in this workbook. It cannot
  explain causes or predict future sales.

## Run on Windows in VS Code

Open this project folder in VS Code, then open **Terminal → New Terminal**.
Run these commands **one at a time**. If a command fails, fix it before moving
to the next one.

1. Create a private Python environment for this project:

   ```powershell
   python -m venv .venv
   ```

2. Activate that environment in the current VS Code terminal:

   ```powershell
   .venv\Scripts\activate
   ```

3. Install the libraries listed for this project:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Start the dashboard:

   ```powershell
   python -m streamlit run app.py
   ```

Streamlit prints a local web address in the terminal. Open that address in
your browser. To stop the dashboard, focus the terminal and press `Ctrl+C`.
