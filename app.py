import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

SHOW_COLUMNS = [
    "Campaign Group",
    "Campaign Name",
    "Subject",
    "Open Rate",
    "Send Date",
    "Campaign URL",
]


def categorize_campaign(name):
    name = name.lower()
    if "wednesday" in name:
        return "Wednesday Campaign"
    elif "friday" in name:
        return "Friday Campaign"
    elif "monday" in name:
        return "Monday Campaign"
    elif "monthly" in name:
        return "Monthly Campaign"
    else:
        return "Other"


def create_campaign_url(campaign_id):
    return f"https://www.klaviyo.com/campaign/{campaign_id}/reports/overview"


def identify_outliers(df):
    Q1 = df["Open Rate"].quantile(0.25)
    Q3 = df["Open Rate"].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    df["Is Outlier"] = (df["Open Rate"] < lower_bound) | (df["Open Rate"] > upper_bound)
    return df


def process_data(df):
    # Convert Send Time to datetime
    # 2024-08-21 12:00:00

    df["Send Time"] = pd.to_datetime(df["Send Time"], format="%Y-%m-%d %H:%M:%S")
    df["Send Date"] = df["Send Time"].dt.date

    df["Open Rate"] = df["Open Rate"].str.rstrip("%").astype("float") / 100.0
    df["Campaign Group"] = df["Campaign Name"].apply(categorize_campaign)
    df["Campaign URL"] = df["Campaign ID"].apply(create_campaign_url)
    df = df.sort_values("Open Rate", ascending=False)[SHOW_COLUMNS]
    df = identify_outliers(df)
    # Group by mean, median, and count of open rate
    grouped = (
        df.groupby("Campaign Group")
        .agg({"Open Rate": ["mean", "median", "count"]})
        .reset_index()
    )
    # Flatten column names
    grouped.columns = [
        "Campaign Group",
        "Mean Open Rate",
        "Median Open Rate",
        "Campaign Count",
    ]
    grouped = grouped.sort_values("Mean Open Rate", ascending=False)
    return df, grouped


def display_raw_data(df):
    st.header("Raw Data")
    st.dataframe(df)


def display_grouped_data(grouped):
    st.header("Grouped Data")
    st.dataframe(grouped)


def plot_average_open_rates(grouped):
    fig = px.bar(
        grouped,
        x="Campaign Group",
        y="Mean Open Rate",
        title="Average Open Rate by Campaign Group",
        category_orders={"Campaign Group": grouped["Campaign Group"].tolist()},
    )
    fig.update_layout(xaxis_title="Campaign Group", yaxis_title="Average Open Rate")
    st.plotly_chart(fig)


def plot_open_rate_distribution(df):
    df_sorted = df.sort_values("Open Rate", ascending=False)
    order = (
        df_sorted.groupby("Campaign Group")["Open Rate"]
        .median()
        .sort_values(ascending=False)
        .index
    )
    fig = px.box(
        df,
        x="Campaign Group",
        y="Open Rate",
        title="Distribution of Open Rates by Campaign Group",
        category_orders={"Campaign Group": order},
    )
    fig.update_layout(xaxis_title="Campaign Group", yaxis_title="Open Rate")
    st.plotly_chart(fig)


def plot_open_rate_scatter(df):
    # Create a custom color scale with the specified colors
    color_scale = {False: "#72BEFA", True: "#E583B6"}

    # Create the main scatter plot
    fig = go.Figure()

    for is_outlier in [False, True]:
        subset = df[df["Is Outlier"] == is_outlier]
        fig.add_trace(
            go.Scatter(
                x=subset["Send Date"],
                y=subset["Open Rate"],
                mode="markers",
                name="Outlier" if is_outlier else "Regular",
                marker=dict(
                    color=color_scale[is_outlier],
                    size=12 if is_outlier else 8,
                    symbol="star" if is_outlier else "circle",
                    line=(
                        dict(width=2, color="DarkSlateGrey")
                        if is_outlier
                        else dict(width=0)
                    ),
                ),
                hovertemplate=(
                    "Send Date: %{x|%Y-%m-%d}<br>"
                    "Open Rate: %{y:.2%}<br>"
                    "Campaign Group: %{customdata[0]}<br>"
                    "Campaign Name: %{customdata[1]}<br>"
                    "Is Outlier: %{customdata[2]}"
                ),
                customdata=subset[["Campaign Group", "Campaign Name", "Is Outlier"]],
            )
        )

    fig.update_layout(
        title="Open Rate for All Campaigns (Outliers Highlighted)",
        xaxis_title="Send Date",
        yaxis_title="Open Rate",
        legend_title="Point Type",
        hovermode="closest",
    )

    # Format x-axis to show dates nicely
    fig.update_xaxes(
        type="date",
        tickformat="%Y-%m-%d",
        tickangle=45,
        dtick="D1",  # Show tick for each day
    )

    # Format y-axis as percentage
    fig.update_yaxes(tickformat=".0%")

    st.plotly_chart(fig)


def display_category_details(df):
    st.header("Campaign Category Details")
    categories = ["All"] + list(df["Campaign Group"].unique())
    selected_category = st.selectbox("Select a campaign category:", categories)

    if selected_category != "All":
        filtered_df = df[df["Campaign Group"] == selected_category]
    else:
        filtered_df = df

    filtered_df = filtered_df.sort_values("Open Rate", ascending=False)

    st.subheader(f"Data for {selected_category} Category")
    st.dataframe(filtered_df)

    st.subheader(f"Statistics for {selected_category} Category")
    stats = filtered_df["Open Rate"].describe()
    st.write(stats)


def main():
    st.title("Campaign Analysis App")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        df, grouped = process_data(df)

        display_raw_data(df)
        display_grouped_data(grouped)
        plot_average_open_rates(grouped)
        plot_open_rate_distribution(df)
        plot_open_rate_scatter(df)
        display_category_details(df)


if __name__ == "__main__":
    main()
