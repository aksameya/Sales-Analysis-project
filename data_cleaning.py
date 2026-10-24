"""Load the workbook and prepare a separate, cleaned copy for analysis."""

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "Order ID",
    "Order Date",
    "Customer ID",
    "Customer Name",
    "Product",
    "Category",
    "Quantity",
    "Unit Price (INR)",
    "Discount (%)",
    "Sales (INR)",
    "Profit (INR)",
]

NUMERIC_COLUMNS = [
    "Quantity",
    "Unit Price (INR)",
    "Discount (%)",
    "Sales (INR)",
    "Profit (INR)",
]

COLUMN_NAMES = {
    "order id": "Order ID",
    "order date": "Order Date",
    "customer id": "Customer ID",
    "customer name": "Customer Name",
    "product": "Product",
    "category": "Category",
    "quantity": "Quantity",
    "unit price": "Unit Price (INR)",
    "unit price inr": "Unit Price (INR)",
    "unit price (inr)": "Unit Price (INR)",
    "discount": "Discount (%)",
    "discount (%)": "Discount (%)",
    "sales": "Sales (INR)",
    "sales inr": "Sales (INR)",
    "sales (inr)": "Sales (INR)",
    "profit": "Profit (INR)",
    "profit inr": "Profit (INR)",
    "profit (inr)": "Profit (INR)",
}

GEOGRAPHIC_COLUMN_NAMES = {
    "city",
    "country",
    "location",
    "postal code",
    "province",
    "region",
    "state",
    "territory",
    "zip code",
}


def _normalize_column_name(column_name):
    """Trim and standardize a header, using familiar names for known columns."""
    cleaned_name = " ".join(str(column_name).strip().split())
    lookup_name = cleaned_name.casefold()
    return COLUMN_NAMES.get(lookup_name, cleaned_name)


def _clean_date_column(date_values):
    """Read Excel date serial numbers as well as ordinary date text."""
    numeric_dates = pd.to_numeric(date_values, errors="coerce")
    excel_serial_mask = numeric_dates.between(1, 100000)

    cleaned_dates = pd.to_datetime(date_values, errors="coerce")
    if excel_serial_mask.any():
        cleaned_dates.loc[excel_serial_mask] = pd.to_datetime(
            numeric_dates.loc[excel_serial_mask],
            unit="D",
            origin="1899-12-30",
            errors="coerce",
        )
    return cleaned_dates


def _clean_numeric_column(values):
    """Convert numbers stored as text, including rupees and comma separators."""
    cleaned_values = (
        values.astype("string")
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip()
    )
    return pd.to_numeric(cleaned_values, errors="coerce")


def load_and_clean_data(file_path, sheet_name="Raw_Sales_Data"):
    """Load the original worksheet and return a cleaned copy and quality report.

    Only completely identical transaction rows are removed. Missing values are
    kept as missing so the dashboard can show and explain them.
    """
    file_path = Path(file_path)
    raw_data = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        engine="openpyxl",
    )
    cleaned_data = raw_data.copy()
    original_row_count = len(cleaned_data)

    index_columns = [
        column
        for column in cleaned_data.columns
        if str(column).strip().casefold().startswith("unnamed:")
        or str(column).strip().casefold() in {"index", "level_0"}
    ]
    cleaned_data = cleaned_data.drop(columns=index_columns)
    cleaned_data.columns = [_normalize_column_name(column) for column in cleaned_data.columns]

    missing_required_columns = [
        column for column in REQUIRED_COLUMNS if column not in cleaned_data.columns
    ]
    if missing_required_columns:
        missing_names = ", ".join(missing_required_columns)
        raise ValueError(f"The worksheet is missing required columns: {missing_names}")

    for column in cleaned_data.select_dtypes(include=["object", "string"]).columns:
        cleaned_data[column] = (
            cleaned_data[column]
            .astype("string")
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

    for column in ["Order ID", "Customer ID"]:
        cleaned_data[column] = cleaned_data[column].str.upper()

    for column in ["Customer Name", "Product", "Category"]:
        cleaned_data[column] = cleaned_data[column].str.title()

    geographic_columns = [
        column
        for column in cleaned_data.columns
        if column.casefold() in GEOGRAPHIC_COLUMN_NAMES
    ]
    for column in geographic_columns:
        cleaned_data[column] = (
            cleaned_data[column].astype("string").str.title()
        )

    cleaned_data["Order Date"] = _clean_date_column(cleaned_data["Order Date"])

    invalid_numeric_values = {}
    for column in NUMERIC_COLUMNS:
        original_values = cleaned_data[column]
        converted_values = _clean_numeric_column(original_values)
        invalid_numeric_values[column] = int(
            (original_values.notna() & converted_values.isna()).sum()
        )
        cleaned_data[column] = converted_values

    duplicate_rows_removed = int(cleaned_data.duplicated().sum())
    cleaned_data = cleaned_data.drop_duplicates().reset_index(drop=True)

    missing_values = cleaned_data.isna().sum().rename("Missing values").to_frame()
    missing_values.index.name = "Column"

    quality_summary = {
        "Original rows": original_row_count,
        "Exact duplicate rows removed": duplicate_rows_removed,
        "Rows kept for analysis": len(cleaned_data),
        "Unnecessary index columns removed": len(index_columns),
        "Unparseable dates": int(cleaned_data["Order Date"].isna().sum()),
        "Invalid numeric values by column": invalid_numeric_values,
        "Geographic columns found": geographic_columns,
    }

    return cleaned_data, missing_values, quality_summary
