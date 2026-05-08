import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px

st.set_page_config(page_title="Airbnb A/B Test Analysis", layout="wide")

conn = duckdb.connect('airbnb.db')
try:
    conn.execute("SELECT 1 FROM airbnb_data LIMIT 1")
except duckdb.Error:
    conn.execute("CREATE TABLE airbnb_data AS SELECT * FROM read_csv_auto('Airbnb_Open_Data2.csv')")

# Get table name
tables = conn.execute("SHOW TABLES").fetchall()
table_name = tables[0][0] if tables else "airbnb_data"

st.title("Airbnb Data Visualization and Explanations")
st.write("### Average Price by Room Type")
avg_price = pd.read_sql("""
    SELECT room_type, AVG(price) as avg_price, COUNT(*) as count
    FROM airbnb_data
    WHERE price IS NOT NULL
    GROUP BY room_type
    ORDER BY avg_price DESC
""", conn)

fig_bar = px.bar(
    avg_price,
    x="room_type",
    y="avg_price",
    title="Average Price by Room Type",
    labels={"room_type": "Room Type", "avg_price": "Average Price ($)"},
    text="avg_price"
)
fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

st.write("### Review Trends Over Time")
review_data = pd.read_sql("""
    SELECT last_review, COUNT(*) as reviews
    FROM airbnb_data
    WHERE last_review IS NOT NULL
    GROUP BY last_review
    ORDER BY last_review
    LIMIT 100
""", conn)

fig_reviews = px.line(
    review_data,
    x="last_review",
    y="reviews",
    title="Number of Reviews Over Time",
    labels={"last_review": "Date", "reviews": "Number of Reviews"}
)
st.plotly_chart(fig_reviews, use_container_width=True)

st.write("### Service Fee vs Price Correlation")
fee_data = pd.read_sql("""
    SELECT price, service_fee, room_type
    FROM airbnb_data
    WHERE price IS NOT NULL AND service_fee IS NOT NULL
    LIMIT 500
""", conn)

fig_scatter = px.scatter(
    fee_data,
    x="price",
    y="service_fee",
    color="room_type",
    title="Service Fee vs Price",
    labels={"price": "Price ($)", "service_fee": "Service Fee ($)", "room_type": "Room Type"}
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

st.write("### Listings by Neighborhood")
neighborhood_data = pd.read_sql("""
    SELECT neighbourhood, COUNT(*) as count
    FROM airbnb_data
    GROUP BY neighbourhood
    ORDER BY count DESC
    LIMIT 20
""", conn)

fig_neigh = px.bar(
    neighborhood_data,
    x="count",
    y="neighbourhood",
    orientation='h',
    title="Top 20 Neighborhoods by Listing Count",
    labels={"neighbourhood": "Neighborhood", "count": "Number of Listings"}
)
st.plotly_chart(fig_neigh, use_container_width=True)

st.write("### Price Distribution by Neighborhood (Top 10)")
top_neighborhoods = neighborhood_data["neighbourhood"].head(10).tolist()
price_neigh = pd.read_sql(f"""
    SELECT neighbourhood, price
    FROM airbnb_data
    WHERE neighbourhood IN ({','.join(["'" + n.replace("'", "''") + "'" for n in top_neighborhoods])})
    AND price IS NOT NULL
    LIMIT 1000
""", conn)

fig_box = px.box(
    price_neigh,
    x="neighbourhood",
    y="price",
    title="Price Distribution by Top 10 Neighborhoods",
    labels={"neighbourhood": "Neighborhood", "price": "Price ($)"}
)
fig_box.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': top_neighborhoods})
st.plotly_chart(fig_box, use_container_width=True)

conn.close()