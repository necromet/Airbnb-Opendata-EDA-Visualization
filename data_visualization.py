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
st.write("""
# From airbnb data, these are the columns that are available:

## Categorical Variable
- host_identity_verified: Flag whether host is verified or not
- neighbourhood_group: Groupings of neighbourhood
- instant_bookable: Flag whether the airbnb is bookable instantly
- cancellation_policy: 3 Categories of cancellation policy (moderate, strict, and flexible)
- room_type: Categories of room type
- construction_year: Year of construction of the airbnb place
          
## Numerical Variable
- minimum_nights: The minimum nights needed to book the airbnb place
- number_of_reviews: The number of reviews left by users for the airbnb place
- reviews_per_month: The average number of reviews per month left by users
- review_rate_number: The ratings of review
- calculated_host_listings_count: The number of listings the host has in the current scrape, in the city/region geography.
- availability_365: The availability of the listing x days in the future as determined by the calendar. Note a listing may not be available because it has been booked by a guest or blocked by the host.
""")
st.markdown("---")

st.write("""
# Dashboard
## Overview / KPIs
""")

# Get KPI data
total_listings = conn.execute("SELECT COUNT(*) as count FROM airbnb_data").fetchone()[0]
total_hosts = conn.execute("SELECT COUNT(DISTINCT host_id) as count FROM airbnb_data").fetchone()[0]
avg_reviews_per_month = conn.execute("SELECT AVG(reviews_per_month) as avg_reviews_per_month FROM airbnb_data").fetchone()[0]
avg_rating = conn.execute("SELECT AVG(review_rate_number) as avg_rating FROM airbnb_data").fetchone()[0]

count_instant_bookable = conn.execute("SELECT count(*) as count FROM airbnb_data where instant_bookable = true").fetchone()[0]
percentage_instant_bookable = count_instant_bookable/total_listings*100

count_verified_hosts = conn.execute("SELECT count(*) as count FROM airbnb_data where host_identity_verified = 'verified'").fetchone()[0]
percentage_verified_hosts = count_verified_hosts/total_hosts*100

# Read CSS from external file
with open('data_viz.css', 'r') as f:
    css = f.read()

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Create 4 colored large number cards
col1, col2, col3, col4 = st.columns(4)
col5, col6 = st.columns(2)

with col1:
    st.markdown(f'''<div class="metric-card">
        <div class="metric-label">Total Listings</div>
        <div class="metric-value">{total_listings:,}</div>
    </div>''', unsafe_allow_html=True)

with col2:
    st.markdown(f'''<div class="metric-card">
        <div class="metric-label">Total Hosts</div>
        <div class="metric-value">{total_hosts:,}</div>
    </div>''', unsafe_allow_html=True)

with col3:
    st.markdown(f'''<div class="metric-card">
        <div class="metric-label">Average Reviews per month</div>
        <div class="metric-value">{avg_reviews_per_month:.2f}</div>
    </div>''', unsafe_allow_html=True)

with col4:
    st.markdown(f'''<div class="metric-card">
        <div class="metric-label">Average Review Rating</div>
        <div class="metric-value">{avg_rating:.2f}/5.00</div>
    </div>''', unsafe_allow_html=True)

with col5:
    st.markdown(f'''<div class="metric-card">
        <div class="metric-label">Percent of Instant Bookable AirBnb</div>
        <div class="metric-value">{percentage_instant_bookable:.2f}%</div>
    </div>''', unsafe_allow_html=True)

with col6:
    st.markdown(f'''<div class="metric-card">
        <div class="metric-label">Percent of Verified Hosts</div>
        <div class="metric-value">{percentage_verified_hosts:.2f}%</div>
    </div>''', unsafe_allow_html=True)

st.write("""
## Listings & Supply
""")

# Bar Chart — neighbourhood_group vs count of listings
neighbourhood_data = conn.execute("SELECT neighbourhood_group, COUNT(*) as count FROM airbnb_data GROUP BY neighbourhood_group ORDER BY count DESC").fetchall()
neighbourhood_df = pd.DataFrame(neighbourhood_data, columns=['neighbourhood_group', 'count'])
fig_neighbourhood = px.bar(neighbourhood_df, x='neighbourhood_group', y='count', title='Neighbourhood Group Distribution')

# Pie / Donut Chart — room_type distribution
room_type_data = conn.execute("SELECT room_type, COUNT(*) as count FROM airbnb_data GROUP BY room_type ORDER BY count DESC").fetchall()
room_type_df = pd.DataFrame(room_type_data, columns=['room_type', 'count'])
fig_room_type = px.pie(room_type_df, values='count', names='room_type', title='Room Type Distribution')

col7, col8 = st.columns(2)
with col7:
    st.plotly_chart(fig_neighbourhood, use_container_width=True)

with col8:
    st.plotly_chart(fig_room_type, use_container_width=True)

# Histogram — construction_year
construction_data = conn.execute("SELECT construction_year, COUNT(*) as count FROM airbnb_data WHERE construction_year IS NOT NULL GROUP BY construction_year ORDER BY construction_year").fetchall()
construction_df = pd.DataFrame(construction_data, columns=['construction_year', 'count'])
fig_construction = px.histogram(construction_df, x='construction_year', y='count', title='Construction Year Distribution')
st.plotly_chart(fig_construction, use_container_width=True)

st.write("""
## Booking Behavior
""")

instant_book_data = conn.execute("""
    SELECT instant_bookable, reviews_per_month 
    FROM airbnb_data 
    WHERE reviews_per_month IS NOT NULL
""").fetchall()
instant_book_df = pd.DataFrame(instant_book_data, columns=['instant_bookable', 'reviews_per_month'])
fig_instant_book = px.box(instant_book_df, x='instant_bookable', y='reviews_per_month', 
                          title='Reviews per Month by Instant Bookable (A/B Hypothesis #1)')
st.plotly_chart(fig_instant_book, use_container_width=True)
# Box Plot — reviews_per_month grouped by cancellation_policy → A/B hypothesis #3
cancellation_data = conn.execute("""
    SELECT cancellation_policy, reviews_per_month 
    FROM airbnb_data 
    WHERE reviews_per_month IS NOT NULL AND cancellation_policy IS NOT NULL
""").fetchall()
cancellation_df = pd.DataFrame(cancellation_data, columns=['cancellation_policy', 'reviews_per_month'])
fig_cancellation = px.box(cancellation_df, x='cancellation_policy', y='reviews_per_month', 
                          title='Reviews per Month by Cancellation Policy (A/B Hypothesis #3)')
st.plotly_chart(fig_cancellation, use_container_width=True)
# Metric Cards — avg review_rate_number by neighbourhood_group
review_rate_data = conn.execute("""
    SELECT neighbourhood_group, AVG(review_rate_number) as avg_review_rate 
    FROM airbnb_data 
    WHERE review_rate_number IS NOT NULL AND neighbourhood_group IS NOT NULL
    GROUP BY neighbourhood_group
    ORDER BY avg_review_rate DESC
""").fetchall()
st.write("##### Average Review Rating by Neighbourhood Group")
card_cols = st.columns(len(review_rate_data))
for idx, row in enumerate(review_rate_data):
    with card_cols[idx]:
        st.markdown(f'''<div class="metric-card">
            <div class="metric-label">{row[0]}</div>
            <div class="metric-value">{row[1]:.2f}</div>
        </div>''', unsafe_allow_html=True)

# Scatter Plot — minimum_nights vs reviews_per_month
scatter_data = conn.execute("""
    SELECT minimum_nights, reviews_per_month 
    FROM airbnb_data 
    WHERE minimum_nights IS NOT NULL AND minimum_nights <= 31 AND reviews_per_month IS NOT NULL
""").fetchall()
scatter_df = pd.DataFrame(scatter_data, columns=['minimum_nights', 'reviews_per_month'])
fig_scatter = px.scatter(scatter_df, x='minimum_nights', y='reviews_per_month', 
                        title='Minimum Nights vs Reviews per Month (for minimum nights less than 31 days)',
                        labels={'minimum_nights': 'Minimum Nights', 'reviews_per_month': 'Reviews per Month'})
st.plotly_chart(fig_scatter, use_container_width=True)


conn.close()