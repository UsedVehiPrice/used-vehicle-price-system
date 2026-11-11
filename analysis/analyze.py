"""Price analysis on top of the database."""
import pandas as pd

from database.db import get_connection


def load_vehicles(path=None):
    with get_connection(path) as conn:
        return pd.read_sql_query("SELECT * FROM vehicles", conn)


def average_price_by_model_year(df):
    return (
        df.groupby(["brand", "model", "year"])["price"]
        .agg(avg_price="mean", listings="count")
        .round(0)
        .reset_index()
    )


def flag_good_deals(df, threshold=0.15, min_group=3):
    """Mark listings priced at least `threshold` below the average of
    similar vehicles (same brand, model, year, fuel). Groups smaller than
    `min_group` are not judged."""
    df = df.copy()
    keys = ["brand", "model", "year", "fuel_type"]
    grp = df.groupby(keys, dropna=False)["price"]
    df["group_avg"] = grp.transform("mean")
    df["group_size"] = grp.transform("count")
    df["pct_below_avg"] = ((df["group_avg"] - df["price"]) / df["group_avg"]).round(3)
    df["good_deal"] = (df["group_size"] >= min_group) & (df["pct_below_avg"] >= threshold)
    return df


if __name__ == "__main__":
    data = load_vehicles()
    print(average_price_by_model_year(data).head(15))
    deals = flag_good_deals(data)
    print(f"\nGood deals found: {int(deals['good_deal'].sum())} of {len(deals)}")
