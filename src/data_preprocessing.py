import pandas as pd


def preprocess_sales(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Normalize column names (strip and unify common variants)
    df.columns = [c.strip() for c in df.columns]
    cols_lower = {c.lower(): c for c in df.columns}
    # map common variations to canonical names
    rename_map = {}
    if 'date' in cols_lower:
        rename_map[cols_lower['date']] = 'Date'
    if 'day' in cols_lower:
        rename_map[cols_lower['day']] = 'Day'
    if 'month' in cols_lower:
        rename_map[cols_lower['month']] = 'Month'
    if 'year' in cols_lower:
        rename_map[cols_lower['year']] = 'Year'
    # Map age-related columns precisely
    for candidate in ['customer_age', 'age']:
        if candidate in cols_lower:
            rename_map[cols_lower[candidate]] = 'Customer_Age'
    if 'age_group' in cols_lower:
        rename_map[cols_lower['age_group']] = 'Age_Group'
    for candidate in ['customer_gender', 'gender']:
        if candidate in cols_lower:
            rename_map[cols_lower[candidate]] = 'Customer_Gender'
    for candidate in ['product_category', 'category']:
        if candidate in cols_lower:
            rename_map[cols_lower[candidate]] = 'Product_Category'
    for candidate in ['sub_category','subcategory']:
        if candidate in cols_lower:
            rename_map[cols_lower[candidate]] = 'Sub_Category'
    for candidate in ['product','product_name']:
        if candidate in cols_lower:
            rename_map[cols_lower[candidate]] = 'Product'
    for candidate in ['order_quantity','quantity','order_qty']:
        if candidate in cols_lower:
            rename_map[cols_lower[candidate]] = 'Order_Quantity'
    for candidate in ['unit_cost','cost_per_unit']:
        if candidate in cols_lower:
            rename_map[cols_lower[candidate]] = 'Unit_Cost'
    for candidate in ['unit_price','price_per_unit']:
        if candidate in cols_lower:
            rename_map[cols_lower[candidate]] = 'Unit_Price'
    for candidate in ['profit_total','profit']:
        if candidate in cols_lower:
            rename_map[cols_lower[candidate]] = 'Profit'
    for candidate in ['cost_total','cost']:
        if candidate in cols_lower:
            rename_map[cols_lower[candidate]] = 'Cost'
    for candidate in ['revenue_total','revenue']:
        if candidate in cols_lower:
            rename_map[cols_lower[candidate]] = 'Revenue'
    if rename_map:
        df = df.rename(columns=rename_map)
    # Ensure Date
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    # Basic numeric conversions
    # Helper to clean currency-like strings
    def clean_numeric(series: pd.Series) -> pd.Series:
        if series.dtype == object:
            return pd.to_numeric(series.str.replace(r"[$,]", "", regex=True), errors='coerce')
        return pd.to_numeric(series, errors='coerce')

    for col in ['Order_Quantity', 'Unit_Cost', 'Unit_Price', 'Profit', 'Cost', 'Revenue']:
        if col in df.columns:
            df[col] = clean_numeric(df[col]).fillna(0)
    # Extract Year/Month/day
    if 'Date' in df.columns:
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['Month_Name'] = df['Date'].dt.month_name()
        df['Month_Year'] = df['Date'].dt.to_period('M').astype(str)
        df['DayOfWeek'] = df['Date'].dt.day_name()
    # Profit margin
    if 'Revenue' in df.columns and 'Profit' in df.columns:
        df['Profit_Margin'] = df['Profit'] / df['Revenue'].replace({0: pd.NA})
        df['Profit_Margin'] = df['Profit_Margin'].fillna(0)
    # Age grouping fallback: ensure Customer_Age is a 1-D numeric Series
    if 'Customer_Age' in df.columns and 'Age_Group' not in df.columns:
        col = df['Customer_Age']
        # If column is accidentally a DataFrame (duplicate column names), take first column
        if hasattr(col, 'ndim') and getattr(col, 'ndim', 1) != 1:
            try:
                col = col.iloc[:, 0]
            except Exception:
                col = col.squeeze()
        col = pd.to_numeric(col.astype(str).str.replace(r"[^0-9\.\-]", "", regex=True), errors='coerce')
        df['Customer_Age'] = col.fillna(0)
        bins = [0, 24, 34, 54, 120]
        labels = ['Youth', 'Young Adults', 'Adults', 'Seniors']
        df['Age_Group'] = pd.cut(df['Customer_Age'], bins=bins, labels=labels, right=True)
    return df
