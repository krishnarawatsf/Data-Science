import plotly.express as px
import pandas as pd

# Ducati-inspired palette
PALETTE = {
    "primary": "#D71A14",
    "dark": "#1a1a1a",
    "muted": "#6b6b6b",
    "accent": "#ffffff",
}


def plot_monthly_revenue(df: pd.DataFrame):
    if df.empty:
        return px.line()
    monthly = df.groupby('Month_Year', as_index=False)['Revenue'].sum()
    monthly = monthly.sort_values('Month_Year')
    fig = px.line(
        monthly,
        x='Month_Year',
        y='Revenue',
        markers=True,
        title='Monthly Revenue',
        color_discrete_sequence=[PALETTE['primary']],
    )
    fig.update_xaxes(tickangle=45)
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=PALETTE['accent'])
    return fig


def plot_top_products(df: pd.DataFrame, top_n=10):
    if df.empty or 'Product' not in df.columns:
        return px.bar()
    prod = df.groupby('Product', as_index=False)['Revenue'].sum().sort_values('Revenue', ascending=False).head(top_n)
    fig = px.bar(
        prod,
        x='Revenue',
        y='Product',
        orientation='h',
        title=f'Top {top_n} Products by Revenue',
        color_discrete_sequence=[PALETTE['primary']],
    )
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=PALETTE['accent'])
    return fig


def plot_revenue_by_country(df: pd.DataFrame):
    if df.empty or 'Country' not in df.columns:
        return px.bar()
    country = df.groupby('Country', as_index=False)['Revenue'].sum().sort_values('Revenue', ascending=False)
    fig = px.bar(
        country,
        x='Country',
        y='Revenue',
        title='Revenue by Country',
        color_discrete_sequence=[PALETTE['primary'], PALETTE['muted']],
    )
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=PALETTE['accent'])
    return fig


def plot_profit_box(df: pd.DataFrame):
    if df.empty or 'Product_Category' not in df.columns:
        return px.box()
    fig = px.box(
        df,
        x='Product_Category',
        y='Profit',
        title='Profit by Product Category',
        color_discrete_sequence=[PALETTE['primary']],
    )
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=PALETTE['accent'])
    return fig


def plot_category_heatmap(df: pd.DataFrame, agg_col='Revenue'):
    """Heatmap of categories vs month-year showing aggregated revenue (or other agg_col)."""
    if df.empty or 'Product_Category' not in df.columns or 'Month_Year' not in df.columns:
        return px.imshow([[0]], color_continuous_scale=[[0, PALETTE['dark']], [1, PALETTE['primary']]])
    pivot = df.pivot_table(index='Product_Category', columns='Month_Year', values=agg_col, aggfunc='sum', fill_value=0)
    # sort columns chronologically if possible
    try:
        pivot = pivot.reindex(sorted(pivot.columns, key=lambda x: pd.Period(x, freq='M')) , axis=1)
    except Exception:
        pivot = pivot.reindex(sorted(pivot.columns), axis=1)
    fig = px.imshow(pivot, aspect='auto', labels=dict(x='Month', y='Product Category', color=agg_col), title=f'{agg_col} Heatmap by Category and Month')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=PALETTE['accent'])
    return fig


def plot_treemap_top_products(df: pd.DataFrame, top_n=50):
    """Treemap showing revenue nested by Product_Category > Product for top N products by revenue."""
    if df.empty or 'Product' not in df.columns:
        return px.treemap()
    prod = df.groupby(['Product_Category', 'Product'], as_index=False)['Revenue'].sum()
    top = prod.groupby('Product', as_index=False)['Revenue'].sum().sort_values('Revenue', ascending=False).head(top_n)
    top_products = top['Product'].tolist()
    prod = prod[prod['Product'].isin(top_products)]
    fig = px.treemap(prod, path=['Product_Category', 'Product'], values='Revenue', title=f'Treemap of Top {top_n} Products by Revenue', color='Revenue', color_continuous_scale=[PALETTE['dark'], PALETTE['primary']])
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=PALETTE['accent'])
    return fig


def plot_country_choropleth(df: pd.DataFrame, agg_col='Revenue'):
    """Choropleth by country. Uses country names where available."""
    if df.empty or 'Country' not in df.columns:
        return px.choropleth()
    country = df.groupby('Country', as_index=False)[agg_col].sum().sort_values(agg_col, ascending=False)
    # try to create choropleth with country names
    try:
        fig = px.choropleth(country, locations='Country', locationmode='country names', color=agg_col, hover_name='Country', color_continuous_scale='Reds', title='Revenue by Country')
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=PALETTE['accent'])
        return fig
    except Exception:
        # fallback: return a bar chart if mapping fails
        fig = px.bar(country, x='Country', y=agg_col, title='Revenue by Country (fallback)')
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=PALETTE['accent'])
        return fig
