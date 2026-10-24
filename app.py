"""Interactive sales analysis dashboard for the supplied Excel workbook."""

from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from analysis import (
    calculate_kpis,
    customer_summary,
    format_inr,
    make_insights,
    monthly_summary,
    summary_by,
)
from data_cleaning import load_and_clean_data


st.set_page_config(
    page_title="Sales Analysis Dashboard",
    page_icon="📊",
    layout="wide",
)

PROJECT_FOLDER = Path(__file__).resolve().parent
DATASET_NAME = "Sales_Analysis_Minimal_Dataset_1000_Records.xlsx"
DATASET_PATHS = [
    PROJECT_FOLDER / DATASET_NAME,
    PROJECT_FOLDER / "data" / DATASET_NAME,
]
DATASET_PATH = next((path for path in DATASET_PATHS if path.exists()), None)

st.markdown(
    """
    <style>
    .stApp { background-color: #f5f7fb; }
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e5eaf2;
        border-radius: 12px;
        padding: 14px 16px;
    }
    h1, h2, h3 { color: #17324d; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Sales Analysis Dashboard")
st.caption(
    "Explore sales, profit, products, customers, and data quality using the supplied workbook."
)

if DATASET_PATH is None:
    expected_path = PROJECT_FOLDER / DATASET_NAME
    st.error(
        f"Dataset not found. Place the existing Excel file here: `{expected_path}` "
        "Do not rename or replace the original workbook."
    )
    st.stop()

try:
    sales_data, missing_summary, quality_summary = load_and_clean_data(DATASET_PATH)
except (OSError, ValueError, ImportError, KeyError) as error:
    st.error(f"The workbook could not be loaded or cleaned: {error}")
    st.stop()

all_dates = sales_data["Order Date"].dropna()
all_categories = sorted(sales_data["Category"].dropna().unique().tolist())
all_products = sorted(sales_data["Product"].dropna().unique().tolist())
all_customers = customer_summary(sales_data)
customer_names = {
    row["Customer ID"]: row["Customer Name"]
    for _, row in all_customers.iterrows()
}
customer_ids = sorted(customer_names)

geographic_columns = quality_summary["Geographic columns found"]
preferred_geo_names = ["Region", "State", "City", "Country", "Province", "Territory"]
geographic_column = next(
    (
        column
        for preferred_name in preferred_geo_names
        for column in geographic_columns
        if column.casefold() == preferred_name.casefold()
    ),
    geographic_columns[0] if geographic_columns else None,
)
all_locations = (
    sorted(sales_data[geographic_column].dropna().unique().tolist())
    if geographic_column
    else []
)

if "filter_reset_count" not in st.session_state:
    st.session_state["filter_reset_count"] = 0


def reset_filters():
    """Give the filter widgets fresh keys so they return to their defaults."""
    st.session_state["filter_reset_count"] += 1


st.sidebar.header("Filters")
st.sidebar.button("Reset filters", on_click=reset_filters, width="stretch")
filter_key_suffix = st.session_state["filter_reset_count"]
if not all_dates.empty:
    default_dates = (all_dates.min().date(), all_dates.max().date())
    selected_dates = st.sidebar.date_input(
        "Order date range",
        value=default_dates,
        min_value=default_dates[0],
        max_value=default_dates[1],
        key=f"date_filter_{filter_key_suffix}",
    )
else:
    selected_dates = ()
    st.sidebar.info("No valid order dates are available for date filtering.")

selected_categories = st.sidebar.multiselect(
    "Category",
    options=all_categories,
    default=all_categories,
    key=f"category_filter_{filter_key_suffix}",
)
selected_products = st.sidebar.multiselect(
    "Product",
    options=all_products,
    default=all_products,
    key=f"product_filter_{filter_key_suffix}",
)
selected_customer = st.sidebar.selectbox(
    "Customer",
    options=["All customers", *customer_ids],
    format_func=lambda customer_id: (
        "All customers"
        if customer_id == "All customers"
        else f"{customer_names[customer_id]} ({customer_id})"
    ),
    key=f"customer_filter_{filter_key_suffix}",
)

if geographic_column:
    selected_locations = st.sidebar.multiselect(
        geographic_column,
        options=all_locations,
        default=all_locations,
        key=f"geo_filter_{filter_key_suffix}",
    )
else:
    selected_locations = []

filtered_data = sales_data.copy()
if selected_dates:
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date = end_date = selected_dates
    filtered_data = filtered_data[
        filtered_data["Order Date"].dt.date.between(start_date, end_date)
    ]

filtered_data = filtered_data[
    filtered_data["Category"].isin(selected_categories)
    & filtered_data["Product"].isin(selected_products)
]

if selected_customer != "All customers":
    filtered_data = filtered_data[
        filtered_data["Customer ID"] == selected_customer
    ]

if geographic_column:
    filtered_data = filtered_data[
        filtered_data[geographic_column].isin(selected_locations)
    ]

st.caption(
    f"Showing {len(filtered_data):,} of {len(sales_data):,} cleaned transaction rows. "
    "The original Excel workbook is never modified."
)

if filtered_data.empty:
    st.warning(
        "No records match the selected filters. Change a filter or choose "
        "'Reset filters' to see the data again."
    )
else:
    kpis = calculate_kpis(filtered_data)
    metric_rows = [
        [
            ("Total Sales (₹)", format_inr(kpis["Total Sales"])),
            ("Total Profit (₹)", format_inr(kpis["Total Profit"])),
            ("Total Orders", f"{kpis['Total Orders']:,}"),
            ("Total Units Sold", f"{kpis['Total Units Sold']:,.0f}"),
        ],
        [
            ("Average Order Value (₹)", format_inr(kpis["Average Order Value"])),
            (
                "Profit Margin (%)",
                f"{kpis['Profit Margin']:.2f}%"
                if pd.notna(kpis["Profit Margin"])
                else "Not available",
            ),
            ("Total Customers", f"{kpis['Total Customers']:,}"),
        ],
    ]
    for metric_row in metric_rows:
        columns = st.columns(len(metric_row))
        for column, (label, value) in zip(columns, metric_row):
            column.metric(label, value)

    st.header("Sales trends")
    st.caption(
        "Monthly charts add the transaction sales and profit recorded in each calendar month."
    )
    monthly = monthly_summary(filtered_data)
    if monthly.empty:
        st.info("Monthly trends cannot be shown because no valid order dates are available.")
    else:
        sales_chart, profit_chart = st.columns(2)
        with sales_chart:
            figure = px.line(
                monthly,
                x="Month",
                y="Sales (INR)",
                markers=True,
                title="Monthly Sales Trend",
                labels={"Month": "Month", "Sales (INR)": "Sales (₹)"},
                color_discrete_sequence=["#1769aa"],
            )
            figure.update_layout(yaxis_tickprefix="₹", yaxis_tickformat=",.0f")
            st.plotly_chart(figure, width="stretch")
        with profit_chart:
            figure = px.line(
                monthly,
                x="Month",
                y="Profit (INR)",
                markers=True,
                title="Monthly Profit Trend",
                labels={"Month": "Month", "Profit (INR)": "Profit (₹)"},
                color_discrete_sequence=["#159477"],
            )
            figure.update_layout(yaxis_tickprefix="₹", yaxis_tickformat=",.0f")
            st.plotly_chart(figure, width="stretch")

        if monthly["Sales (INR)"].notna().any():
            best_month = monthly.loc[monthly["Sales (INR)"].idxmax()]
            lowest_month = monthly.loc[monthly["Sales (INR)"].idxmin()]
            best_column, lowest_column = st.columns(2)
            best_column.info(
                f"Best-performing month by sales: **{best_month['Month']:%B %Y}** "
                f"({format_inr(best_month['Sales (INR)'])})."
            )
            lowest_column.info(
                f"Lowest-performing month by sales: **{lowest_month['Month']:%B %Y}** "
                f"({format_inr(lowest_month['Sales (INR)'])})."
            )

        monthly["Year"] = monthly["Month"].dt.year
        yearly = monthly.groupby("Year", as_index=False)[
            ["Sales (INR)", "Profit (INR)"]
        ].sum(min_count=1)
        if len(yearly) > 1:
            yearly_chart = px.bar(
                yearly,
                x="Year",
                y=["Sales (INR)", "Profit (INR)"],
                barmode="group",
                title="Yearly Sales and Profit Comparison",
                labels={"value": "Amount (₹)", "variable": "Measure"},
                color_discrete_sequence=["#1769aa", "#159477"],
            )
            yearly_chart.update_layout(yaxis_tickprefix="₹", yaxis_tickformat=",.0f")
            st.plotly_chart(yearly_chart, width="stretch")

    st.header("Product and category analysis")
    st.caption(
        "Compare the total sales, profit, and units recorded for each product and category."
    )
    product_sales = summary_by(filtered_data, "Product", "Sales (INR)")
    product_profit = summary_by(filtered_data, "Product", "Profit (INR)")
    category_sales = summary_by(filtered_data, "Category", "Sales (INR)")
    category_profit = summary_by(filtered_data, "Category", "Profit (INR)")
    product_quantity = (
        filtered_data.dropna(subset=["Product", "Quantity"])
        .groupby("Product", as_index=False)["Quantity"]
        .sum(min_count=1)
        .sort_values("Quantity", ascending=False)
    )

    chart_sections = [
        (product_sales, "Product", "Sales (INR)", "Sales by Product", "#1769aa"),
        (product_profit, "Product", "Profit (INR)", "Profit by Product", "#159477"),
        (category_sales, "Category", "Sales (INR)", "Sales by Category", "#1769aa"),
        (category_profit, "Category", "Profit (INR)", "Profit by Category", "#159477"),
    ]
    for start in range(0, len(chart_sections), 2):
        chart_columns = st.columns(2)
        for column, section in zip(chart_columns, chart_sections[start : start + 2]):
            chart_data, group_column, metric, title, color = section
            with column:
                figure = px.bar(
                    chart_data,
                    x=metric,
                    y=group_column,
                    orientation="h",
                    title=title,
                    labels={metric: metric.replace("(INR)", "(₹)")},
                    color_discrete_sequence=[color],
                )
                figure.update_layout(
                    yaxis={"categoryorder": "total ascending"},
                    xaxis_tickprefix="₹",
                    xaxis_tickformat=",.0f",
                )
                st.plotly_chart(figure, width="stretch")

    quantity_figure = px.bar(
        product_quantity,
        x="Product",
        y="Quantity",
        title="Quantity Sold by Product",
        color_discrete_sequence=["#d17b0f"],
    )
    st.plotly_chart(quantity_figure, width="stretch")

    top_sales_column, top_profit_column = st.columns(2)
    top_sales_column.subheader("Top 5 products by sales")
    top_sales_column.dataframe(
        product_sales.head(5), hide_index=True, width="stretch"
    )
    top_profit_column.subheader("Top 5 products by profit")
    top_profit_column.dataframe(
        product_profit.head(5), hide_index=True, width="stretch"
    )

    st.header("Customer analysis")
    st.caption(
        "A repeat customer is a customer ID linked to more than one distinct order ID "
        "in the selected records."
    )
    customers = customer_summary(filtered_data)
    top_customers = customers.head(10)
    if not top_customers.empty:
        customer_figure = px.bar(
            top_customers.sort_values("Sales (INR)"),
            x="Sales (INR)",
            y="Customer Name",
            orientation="h",
            title="Top 10 Customers by Sales",
            labels={"Sales (INR)": "Sales (₹)"},
            color_discrete_sequence=["#1769aa"],
        )
        customer_figure.update_layout(xaxis_tickprefix="₹", xaxis_tickformat=",.0f")
        st.plotly_chart(customer_figure, width="stretch")
    repeat_customers = customers[customers["Orders"] > 1]
    repeat_column, customer_table_column = st.columns(2)
    repeat_column.metric("Repeat Customers", f"{len(repeat_customers):,}")
    repeat_column.dataframe(
        repeat_customers,
        hide_index=True,
        width="stretch",
    )
    customer_table_column.subheader("Sales by customer")
    customer_table_column.dataframe(
        customers,
        hide_index=True,
        width="stretch",
        height=350,
    )

    st.header("Regional analysis")
    if geographic_column:
        location_sales = summary_by(filtered_data, geographic_column, "Sales (INR)")
        location_profit = summary_by(filtered_data, geographic_column, "Profit (INR)")
        location_sales_column, location_profit_column = st.columns(2)
        for column, chart_data, metric, title in [
            (
                location_sales_column,
                location_sales,
                "Sales (INR)",
                f"Sales by {geographic_column}",
            ),
            (
                location_profit_column,
                location_profit,
                "Profit (INR)",
                f"Profit by {geographic_column}",
            ),
        ]:
            figure = px.bar(
                chart_data,
                x=geographic_column,
                y=metric,
                title=title,
                labels={metric: metric.replace("(INR)", "(₹)")},
                color_discrete_sequence=["#1769aa" if metric == "Sales (INR)" else "#159477"],
            )
            figure.update_layout(yaxis_tickprefix="₹", yaxis_tickformat=",.0f")
            column.plotly_chart(figure, width="stretch")
    else:
        st.info(
            "Regional analysis is not available: this workbook has no Region, City, "
            "State, or other recognized geographic column. No location data has been invented."
        )

    st.header("Business insights")
    insights = make_insights(
        filtered_data,
        monthly,
        product_sales,
        category_profit,
        customers,
    )
    if insights:
        for insight in insights:
            st.markdown(f"- {insight}")
    else:
        st.info("There is not enough valid data in the selected records to calculate insights.")

st.header("Data quality")
st.caption(
    "The quality report describes the full cleaned workbook. Missing values are kept as-is; "
    "the table below shows missing values in the currently selected rows."
)
quality_columns = st.columns(4)
quality_items = [
    ("Original rows", quality_summary["Original rows"]),
    ("Exact duplicate rows removed", quality_summary["Exact duplicate rows removed"]),
    ("Rows kept for analysis", quality_summary["Rows kept for analysis"]),
    ("Index columns removed", quality_summary["Unnecessary index columns removed"]),
]
for column, (label, value) in zip(quality_columns, quality_items):
    column.metric(label, f"{value:,}")

invalid_numeric_count = sum(
    quality_summary["Invalid numeric values by column"].values()
)
st.write(
    f"Unparseable dates: **{quality_summary['Unparseable dates']:,}** · "
    f"Invalid numeric values: **{invalid_numeric_count:,}** · "
    f"Location fields found: **"
    f"{', '.join(geographic_columns) if geographic_columns else 'None'}**"
)
filtered_missing_summary = (
    filtered_data.isna().sum().rename("Missing values").to_frame()
)
filtered_missing_summary.index.name = "Column"
st.dataframe(filtered_missing_summary, width="stretch")

st.header("Cleaned sales records")
st.caption(
    "These are the filtered cleaned records. The source workbook stays unchanged, "
    "and missing values remain blank."
)
st.dataframe(filtered_data, hide_index=True, width="stretch", height=400)

if not filtered_data.empty:
    csv_data = filtered_data.to_csv(index=False).encode("utf-8-sig")
    excel_buffer = BytesIO()
    filtered_data.to_excel(excel_buffer, index=False, engine="openpyxl")
    csv_column, excel_column = st.columns(2)
    csv_column.download_button(
        "Download filtered records as CSV",
        data=csv_data,
        file_name="filtered_sales_records.csv",
        mime="text/csv",
        width="stretch",
    )
    excel_column.download_button(
        "Download filtered records as Excel",
        data=excel_buffer.getvalue(),
        file_name="filtered_sales_records.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )
