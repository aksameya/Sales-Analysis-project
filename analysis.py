"""Small analysis functions used by the Streamlit dashboard."""

import pandas as pd


def format_inr(value):
    """Format a number using Indian digit grouping, for example ₹12,34,567.00."""
    if pd.isna(value):
        return "Not available"

    number = f"{abs(float(value)):.2f}"
    whole_part, decimal_part = number.split(".")
    if len(whole_part) > 3:
        last_three = whole_part[-3:]
        remaining_digits = whole_part[:-3]
        groups = []
        while remaining_digits:
            groups.insert(0, remaining_digits[-2:])
            remaining_digits = remaining_digits[:-2]
        whole_part = ",".join(groups + [last_three])

    sign = "-" if float(value) < 0 else ""
    return f"{sign}₹{whole_part}.{decimal_part}"


def calculate_kpis(data):
    """Calculate dashboard KPIs from the currently selected transaction rows."""
    total_sales = data["Sales (INR)"].sum(min_count=1)
    total_profit = data["Profit (INR)"].sum(min_count=1)

    # Count distinct order IDs because an order may contain multiple product rows.
    total_orders = int(data["Order ID"].nunique())
    total_units = data["Quantity"].sum(min_count=1)
    average_order_value = (
        total_sales / total_orders
        if total_orders and pd.notna(total_sales)
        else float("nan")
    )
    # Profit margin is total profit divided by total sales, not an average of row margins.
    profit_margin = (
        total_profit / total_sales * 100
        if pd.notna(total_profit) and pd.notna(total_sales) and total_sales != 0
        else float("nan")
    )
    total_customers = int(data["Customer ID"].nunique())

    return {
        "Total Sales": total_sales,
        "Total Profit": total_profit,
        "Total Orders": total_orders,
        "Total Units Sold": total_units,
        "Average Order Value": average_order_value,
        "Profit Margin": profit_margin,
        "Total Customers": total_customers,
    }


def monthly_summary(data):
    """Return sales and profit grouped by calendar month."""
    dated_rows = data.dropna(subset=["Order Date"])
    if dated_rows.empty:
        return pd.DataFrame(columns=["Month", "Sales (INR)", "Profit (INR)"])

    monthly = (
        dated_rows.assign(Month=dated_rows["Order Date"].dt.to_period("M"))
        .groupby("Month", as_index=False)[["Sales (INR)", "Profit (INR)"]]
        .sum(min_count=1)
    )
    monthly["Month"] = monthly["Month"].dt.to_timestamp()
    return monthly.sort_values("Month")


def summary_by(data, column, metric):
    """Sum one measure by a category, product, customer, or location."""
    valid_rows = data.dropna(subset=[column, metric])
    if valid_rows.empty:
        return pd.DataFrame(columns=[column, metric])

    return (
        valid_rows.groupby(column, as_index=False)[metric]
        .sum(min_count=1)
        .sort_values(metric, ascending=False)
    )


def customer_summary(data):
    """Return one row per customer ID with their order count and sales."""
    valid_rows = data.dropna(subset=["Customer ID"])
    if valid_rows.empty:
        return pd.DataFrame(
            columns=["Customer ID", "Customer Name", "Orders", "Sales (INR)", "Profit (INR)"]
        )

    grouped_customers = valid_rows.groupby("Customer ID")
    summary = grouped_customers.agg(
        **{
            "Customer Name": ("Customer Name", "first"),
            "Orders": ("Order ID", "nunique"),
        }
    )
    summary["Sales (INR)"] = grouped_customers["Sales (INR)"].sum(min_count=1)
    summary["Profit (INR)"] = grouped_customers["Profit (INR)"].sum(min_count=1)
    return summary.reset_index().sort_values("Sales (INR)", ascending=False)


def make_insights(data, monthly, product_sales, category_profit, customers):
    """Build short insights only when the required data is available."""
    insights = []

    valid_months = monthly.dropna(subset=["Sales (INR)"])
    if not valid_months.empty:
        best_month = valid_months.loc[valid_months["Sales (INR)"].idxmax()]
        lowest_month = valid_months.loc[valid_months["Sales (INR)"].idxmin()]
        insights.append(
            f"Highest-sales month: {best_month['Month']:%B %Y} "
            f"({format_inr(best_month['Sales (INR)'])})."
        )
        insights.append(
            f"Lowest-sales month: {lowest_month['Month']:%B %Y} "
            f"({format_inr(lowest_month['Sales (INR)'])})."
        )

        if len(valid_months) >= 2:
            last_month = valid_months.iloc[-1]
            previous_month = valid_months.iloc[-2]
            previous_sales = previous_month["Sales (INR)"]
            if pd.notna(previous_sales) and previous_sales != 0:
                change = (
                    (last_month["Sales (INR)"] - previous_sales)
                    / previous_sales
                    * 100
                )
                direction = "increased" if change >= 0 else "decreased"
                insights.append(
                    f"Sales {direction} by {abs(change):.1f}% from "
                    f"{previous_month['Month']:%B %Y} to {last_month['Month']:%B %Y}."
                )

    if not product_sales.empty:
        best_product = product_sales.iloc[0]
        insights.append(
            f"Top product by sales: {best_product['Product']} "
            f"({format_inr(best_product['Sales (INR)'])})."
        )

    if not category_profit.empty:
        best_category = category_profit.iloc[0]
        insights.append(
            f"Top category by profit: {best_category['Category']} "
            f"({format_inr(best_category['Profit (INR)'])})."
        )

    if not customers.empty:
        top_customer = customers.iloc[0]
        insights.append(
            f"Top customer by sales: {top_customer['Customer Name']} "
            f"({format_inr(top_customer['Sales (INR)'])})."
        )

    repeat_customers = customers[customers["Orders"] > 1]
    if not customers.empty:
        insights.append(
            f"{len(repeat_customers)} of {len(customers)} customers placed more than one order "
            "in the selected records."
        )

    return insights
