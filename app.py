import streamlit as st
import pandas as pd
import plotly.express as px

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

def process_data(df):
    # Convert percentage strings to floats
    df['Open Rate'] = df['Open Rate'].str.rstrip('%').astype('float') / 100.0

    # Apply the categorization function to create a new column
    df["Campaign Group"] = df["Campaign Name"].apply(categorize_campaign)

    # Group by the new category and calculate mean open rate
    grouped = df.groupby("Campaign Group").agg({'Open Rate': 'mean'}).reset_index()
    
    # Sort the grouped data by Open Rate in descending order
    grouped = grouped.sort_values('Open Rate', ascending=False)
    
    return df, grouped

def main():
    st.title("Campaign Analysis App")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        df, grouped = process_data(df)

        st.header("Raw Data")
        st.dataframe(df)

        st.header("Grouped Data")
        st.dataframe(grouped)

        # Create a bar chart of average open rates by campaign group, sorted by open rate
        fig = px.bar(grouped, x='Campaign Group', y='Open Rate', 
                     title='Average Open Rate by Campaign Group',
                     category_orders={"Campaign Group": grouped['Campaign Group'].tolist()})
        fig.update_layout(xaxis_title="Campaign Group", yaxis_title="Average Open Rate")
        st.plotly_chart(fig)

        # Create a box plot of open rates by campaign group, sorted by median open rate
        df_sorted = df.sort_values('Open Rate', ascending=False)
        order = df_sorted.groupby('Campaign Group')['Open Rate'].median().sort_values(ascending=False).index
        fig2 = px.box(df, x='Campaign Group', y='Open Rate', 
                      title='Distribution of Open Rates by Campaign Group',
                      category_orders={"Campaign Group": order})
        fig2.update_layout(xaxis_title="Campaign Group", yaxis_title="Open Rate")
        st.plotly_chart(fig2)

if __name__ == "__main__":
    main()