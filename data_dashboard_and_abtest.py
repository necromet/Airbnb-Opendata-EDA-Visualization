import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import scipy.stats as stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import numpy as np

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


st.title("Dashboard")
# Create tabs for sections
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Overview / KPIs", "Listings & Supply", "Booking Behavior", "Host Behavior", "Availability Analysis", "🧪 A/B Testing 1", "🧪 A/B Testing 2"])

# Tab 1: Overview / KPIs
with tab1:
    st.write("""
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

# Tab 2: Listings & Supply
with tab2:
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

# Tab 3: Booking Behavior
with tab3:
    st.write("""
    ## Booking Behavior
    """)
    
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
            
    # Describe table — reviews_per_month grouped by instant_bookable → A/B hypothesis #1
    instant_book_data = conn.execute("""
        SELECT instant_bookable, reviews_per_month 
        FROM airbnb_data 
        WHERE reviews_per_month IS NOT NULL
    """).fetchall()
    instant_book_df = pd.DataFrame(instant_book_data, columns=['instant_bookable', 'reviews_per_month'])
    instant_book_stats = instant_book_df.groupby('instant_bookable')['reviews_per_month'].describe()
    st.write("### Reviews per Month by Instant Bookable") # (A/B Hypothesis #1)
    st.dataframe(instant_book_stats)
    
    # Describe table — reviews_per_month grouped by cancellation_policy → A/B hypothesis #3
    cancellation_data = conn.execute("""
        SELECT cancellation_policy, reviews_per_month 
        FROM airbnb_data 
        WHERE reviews_per_month IS NOT NULL AND cancellation_policy IS NOT NULL
    """).fetchall()
    cancellation_df = pd.DataFrame(cancellation_data, columns=['cancellation_policy', 'reviews_per_month'])
    cancellation_stats = cancellation_df.groupby('cancellation_policy')['reviews_per_month'].describe()
    st.write("### Reviews per Month by Cancellation Policy") # (A/B Hypothesis #3)
    st.dataframe(cancellation_stats)
    
    col9, col10 = st.columns(2)
    # Scatter Plot — minimum_nights vs reviews_per_month
    scatter_data_below_30 = conn.execute("""
        SELECT minimum_nights, reviews_per_month 
        FROM airbnb_data 
        WHERE minimum_nights IS NOT NULL AND minimum_nights <= 31 AND reviews_per_month IS NOT NULL
    """).fetchall()
    scatter_df_below_30 = pd.DataFrame(scatter_data_below_30, columns=['minimum_nights', 'reviews_per_month'])
    fig_scatter_below_30 = px.scatter(scatter_df_below_30, x='minimum_nights', y='reviews_per_month', 
                            title='Minimum Nights vs Reviews per Month (for minimum nights <= 31 days)',
                            labels={'minimum_nights': 'Minimum Nights', 'reviews_per_month': 'Reviews per Month'})
    
    
    # Scatter Plot — minimum_nights vs reviews_per_month
    scatter_data_above_30 = conn.execute("""
        SELECT minimum_nights, reviews_per_month 
        FROM airbnb_data 
        WHERE minimum_nights IS NOT NULL 
        AND minimum_nights > 31
        AND minimum_nights < 600             
        AND reviews_per_month IS NOT NULL
    """).fetchall()
    scatter_df_above_30 = pd.DataFrame(scatter_data_above_30, columns=['minimum_nights', 'reviews_per_month'])
    fig_scatter_above_30 = px.scatter(scatter_df_above_30, x='minimum_nights', y='reviews_per_month', 
                            title='Minimum Nights vs Reviews per Month (for minimum nights > 31 days)',
                            labels={'minimum_nights': 'Minimum Nights', 'reviews_per_month': 'Reviews per Month'})
    
    with col9:
        st.plotly_chart(fig_scatter_below_30, use_container_width=True)
    
    with col10:
        st.plotly_chart(fig_scatter_above_30, use_container_width=True)

# Tab 4: Host Behavior
with tab4:
    st.write("""
    ## Host Behavior
    """)
    
    # Metric Cards — avg review_rate_number by host_identity_verified
    review_rate_verified_data = conn.execute("""
        SELECT host_identity_verified, AVG(review_rate_number) as avg_review_rate 
        FROM airbnb_data 
        WHERE review_rate_number IS NOT NULL AND host_identity_verified IS NOT NULL
        GROUP BY host_identity_verified
    """).fetchall()
    
    # Create 2 large number cards for review rates
    col1, col2 = st.columns(2)
    for row in review_rate_verified_data:
        with col1 if row[0] == 'verified' else col2:
            st.markdown(f'''<div class="metric-card">
                <div class="metric-label">Average Review Rating ({row[0]})</div>
                <div class="metric-value">{row[1]:.2f}/5.00</div>
            </div>''', unsafe_allow_html=True)
    
    # Bar Chart - buckets calculated_host_listings_count as Individuals or Multi-listers
    calculated_host_data = conn.execute("""
        SELECT calculated_host_listings_count, COUNT(*) as count 
        FROM airbnb_data 
        WHERE calculated_host_listings_count IS NOT NULL
        GROUP BY calculated_host_listings_count
        ORDER BY calculated_host_listings_count
    """).fetchall()
    calculated_host_df = pd.DataFrame(calculated_host_data, columns=['calculated_host_listings_count', 'count'])
    
    # Create buckets: Individuals (1), Multi-listers (2-5), Power hosts (6+)
    calculated_host_df['bucket'] = calculated_host_df['calculated_host_listings_count'].apply(
        lambda x: 'Individuals' if x == 1 else ('Multi-listers' if 2 <= x <= 5 else 'Power hosts')
    )
    bucket_data = calculated_host_df.groupby('bucket')['count'].sum().reset_index()
    
    # Display host distribution and review rate in same row
    col3, col4 = st.columns(2)
    with col3:
        fig_host_buckets = px.bar(bucket_data, x='bucket', y='count', 
                                  title='Host Listings Distribution')
        st.plotly_chart(fig_host_buckets, use_container_width=True)
    
    with col4:
        # Box Plot — review_rate_number grouped by calculated_host_listings_count buckets (1, 2–5, 6+) → do power hosts perform better?
        calculated_host_review_data = conn.execute("""
            SELECT calculated_host_listings_count, review_rate_number 
            FROM airbnb_data 
            WHERE review_rate_number IS NOT NULL AND calculated_host_listings_count IS NOT NULL
        """).fetchall()
        calculated_host_review_df = pd.DataFrame(calculated_host_review_data, columns=['calculated_host_listings_count', 'review_rate_number'])
        
        # Create buckets for review_rate_number analysis
        calculated_host_review_df['bucket'] = calculated_host_review_df['calculated_host_listings_count'].apply(
            lambda x: 'Individuals' if x == 1 else ('Multi-listers' if 2 <= x <= 5 else 'Power hosts')
        )
        
        # Remove any rows where bucket is null
        calculated_host_review_df = calculated_host_review_df.dropna(subset=['bucket'])
        
        fig_host_review_rate = px.box(calculated_host_review_df, x='bucket', y='review_rate_number', 
                                      title='Review Rate Number by Host Listings Category')
        st.plotly_chart(fig_host_review_rate, use_container_width=True)

# Tab 5: Availability Analysis
with tab5:
    st.write("""
    ## Availability Analysis
    """)
    
    # 1. Bar chart: from average availability_365 by neighbourhood group
    availability_by_neighbourhood = conn.execute("""
        SELECT neighbourhood_group, AVG(availability_365) as avg_availability 
        FROM airbnb_data 
        WHERE availability_365 IS NOT NULL AND neighbourhood_group IS NOT NULL
        GROUP BY neighbourhood_group
        ORDER BY avg_availability DESC
    """).fetchall()
    availability_df = pd.DataFrame(availability_by_neighbourhood, columns=['neighbourhood_group', 'avg_availability'])
    fig_availability_neighbourhood = px.bar(availability_df, x='neighbourhood_group', y='avg_availability', 
                                             title='Average Availability by Neighbourhood Group')
    
    # 2. Heatmap of neighbourhood_group and room_type
    heatmap_data = conn.execute("""
        SELECT neighbourhood_group, room_type, COUNT(*) as count 
        FROM airbnb_data 
        WHERE neighbourhood_group IS NOT NULL AND room_type IS NOT NULL
        GROUP BY neighbourhood_group, room_type
        ORDER BY neighbourhood_group, room_type
    """).fetchall()
    heatmap_df = pd.DataFrame(heatmap_data, columns=['neighbourhood_group', 'room_type', 'count'])
    heatmap_pivot = heatmap_df.pivot(index='neighbourhood_group', columns='room_type', values='count').fillna(0)
    fig_heatmap = px.imshow(heatmap_pivot, labels=dict(x="Room Type", y="Neighbourhood Group", color="Count"),
                            title='Neighbourhood Group vs Room Type Distribution')
    
    # 3. Histogram distribution of availability_365
    availability_histogram_data = conn.execute("""
        SELECT availability_365 
        FROM airbnb_data 
        WHERE availability_365 IS NOT NULL
    """).fetchall()
    availability_hist_df = pd.DataFrame(availability_histogram_data, columns=['availability_365'])
    fig_histogram = px.histogram(availability_hist_df, x='availability_365', 
                                 title='Distribution of Availability (Days)')
    
    # Display the charts
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_availability_neighbourhood, use_container_width=True)
    with col2:
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    st.plotly_chart(fig_histogram, use_container_width=True)

with tab6:
    st.write("""
    ## 🧪 A/B Testing 1: Does Cancellation Policy Affect Bookings?
    """)
    # st.write("""
    # There are 2 sample business problems that I would like to address:
    # 1. Airbnb wants to increase booking frequency. **Does offering a cancellation policy lead to more guest engagement compared to stricter policy?**
    # 2. **Does instant bookable have significantly higher reviews per month than non-instant listings?**
    # """)

    # Section 1 - Business Context
    st.markdown("### 🎯 Business Problem")
    st.write("Airbnb wants to increase booking frequency. Does offering a flexible cancellation policy lead to more guest engagement compared to strict policies?")

    # Section 2 - Hypothesis
    st.markdown("### 💡 Hypothesis")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("$H_0:$ There is no difference in reviews_per_month across cancellation policy groups")
    
    with col2:
        st.markdown("$H_1:$ At least one cancellation policy group has a significantly different mean reviews_per_month")
    # H0 in col1, H1 in col2

    # Section 3 - Test Results
    st.markdown("### 🔬 Methodology")
    st.write("Since we're comparing 3 groups (flexible, moderate, strict), a one-way ANOVA is used instead of a simple t-test. If significant, Tukey's post-hoc test identifies which specific pairs differ.")
    # ANOVA table, p-value with color (green = significant, red = not)

    # Section 4 - Visual First
    st.markdown("### 📊 Exploratory View")
    # Box plot here
    
    # Box plot of reviews_per_month by cancellation_policy
    cancellation_data = conn.execute("""
        SELECT cancellation_policy, reviews_per_month 
        FROM airbnb_data 
        WHERE reviews_per_month IS NOT NULL AND cancellation_policy IS NOT NULL
    """).fetchall()
    cancellation_df = pd.DataFrame(cancellation_data, columns=['cancellation_policy', 'reviews_per_month'])
    
    fig_box_plot = px.box(cancellation_df, x='cancellation_policy', y='reviews_per_month', 
                          title='Reviews per Month by Cancellation Policy')
    st.plotly_chart(fig_box_plot, use_container_width=True)
    
    # Table of group means + sample sizes
    group_stats = cancellation_df.groupby('cancellation_policy')['reviews_per_month'].agg(['mean', 'count']).reset_index()
    group_stats.columns = ['cancellation_policy', 'mean_reviews_per_month', 'sample_size']
    st.markdown("### 📋 Group Means and Sample Sizes")
    st.dataframe(group_stats)
    
    # ANOVA result (F-statistic, p-value)
    st.markdown("### 📊 ANOVA Results")
    
    # Perform ANOVA
    groups = [group['reviews_per_month'].values for name, group in cancellation_df.groupby('cancellation_policy')]
    f_stat, p_value = stats.f_oneway(*groups)
    
    # Display ANOVA results
    anova_result = pd.DataFrame({
        'Statistic': ['F-statistic', 'p-value'],
        'Value': [f'{f_stat:.4f}', f'{p_value:.4f}']
    })
    st.dataframe(anova_result)
    
    # Tukey post-hoc table (if significant)
    if p_value < 0.05:
        st.markdown("### 📊 Tukey's Post-hoc Test")
        tukey = pairwise_tukeyhsd(endog=cancellation_df['reviews_per_month'], 
                                  groups=cancellation_df['cancellation_policy'], 
                                  alpha=0.05)
        # Create a more readable table with formatted p-values
        tukey_results = []
        for i in range(len(tukey.groupsunique)):
            for j in range(i+1, len(tukey.groupsunique)):
                group1 = tukey.groupsunique[i]
                group2 = tukey.groupsunique[j]
                # Get the p-value for this pair
                reject = tukey.reject[i,j]
                mean_diff = tukey.meandiffs[i,j]
                lower_ci = tukey.confint[i,j,0]
                upper_ci = tukey.confint[i,j,1]
                # For Tukey HSD, the reject value indicates significance
                # Create a more readable format
                tukey_results.append({
                    'Pair': f"{group1} vs {group2}",
                    'Mean Difference': f"{mean_diff:.4f}",
                    'Lower CI': f"{lower_ci:.4f}",
                    'Upper CI': f"{upper_ci:.4f}",
                    'Significant': 'Yes' if reject else 'No'
                })
        
        tukey_df = pd.DataFrame(tukey_results)
        st.dataframe(tukey_df, use_container_width=True)
        
        # Statistical Analysis in Sentences
        st.markdown("### 📝 Statistical Analysis Summary")
        st.write(f"**ANOVA Result**: The one-way ANOVA test yielded an F-statistic of {f_stat:.4f} with a p-value of {p_value:.4f}.")
        if p_value < 0.05:
            st.write("Since the p-value is less than 0.05, we reject the null hypothesis and conclude that there are statistically significant differences in reviews per month across at least one pair of cancellation policies.")
            
            # Identify significant pairs
            significant_pairs = [row['Pair'] for row in tukey_results if row['Significant'] == 'Yes']
            if significant_pairs:
                st.write(f"**Post-hoc Analysis**: Tukey's HSD test identified the following significant differences:")
                for pair in significant_pairs:
                    st.write(f"- {pair}")
        else:
            st.write("Since the p-value is greater than or equal to 0.05, we fail to reject the null hypothesis. There are no statistically significant differences in reviews per month across the cancellation policy groups.")
    else:
        st.markdown("#### No significant difference detected (p >= 0.05)")
        st.write("Tukey post-hoc test not performed.")
        
        # Statistical Analysis in Sentences
        st.markdown("### 📝 Statistical Analysis Summary")
        st.write(f"**ANOVA Result**: The one-way ANOVA test yielded an F-statistic of {f_stat:.4f} with a p-value of {p_value:.4f}.")
        if p_value >= 0.05:
            st.write("Since the p-value is greater than or equal to 0.05, we fail to reject the null hypothesis. There are no statistically significant differences in reviews per month across the cancellation policy groups.")

    # Section 5 - Conclusion
    st.markdown("### ✅ Recommendation")
    if p_value < 0.05:
        st.success("Flexible cancellation listings show significantly higher booking engagement compared to strict and moderate policies.")
        st.write("This suggests that offering more flexible cancellation policies may increase guest engagement and booking frequency.")
    else:
        st.warning("No statistically significant difference found between cancellation policies.")
        st.write("This suggests that cancellation policy may not be a significant factor in booking engagement.")

with tab7:
    st.write("""
    ## 🧪 A/B Testing 2: Does Instant Bookable Affect Bookings?
    """)

    st.markdown("### 🎯 Business Problem")
    st.write("Does instant bookable have significantly higher reviews per month than non-instant listings?")

    st.markdown("### 💡 Hypothesis")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("$H_0:$ There is no difference in reviews_per_month between instant bookable and non-instant listings")
    with col2:
        st.markdown("$H_1:$ There is a significant difference in reviews_per_month between instant bookable and non-instant listings")

    st.markdown("### 🔬 Methodology")
    st.write("Independent samples t-test will be used to compare the means of two groups. However, before proceeding, we need to check: (1) Normality assumption using Shapiro-Wilk test, QQ plots, and histograms; (2) Variance equality using Levene's test.")

    st.markdown("### 📊 Exploratory View")

    instant_book_data = conn.execute("""
        SELECT instant_bookable, reviews_per_month
        FROM airbnb_data
        WHERE reviews_per_month IS NOT NULL AND instant_bookable IS NOT NULL
    """).fetchall()
    instant_book_df = pd.DataFrame(instant_book_data, columns=['instant_bookable', 'reviews_per_month'])

    group_instant = instant_book_df[instant_book_df['instant_bookable'] == True]['reviews_per_month'].dropna()
    group_non_instant = instant_book_df[instant_book_df['instant_bookable'] == False]['reviews_per_month'].dropna()

    fig_box = px.box(instant_book_df, x='instant_bookable', y='reviews_per_month',
                      title='Reviews per Month by Instant Bookable Status')
    st.plotly_chart(fig_box, use_container_width=True)

    group_stats = instant_book_df.groupby('instant_bookable')['reviews_per_month'].agg(['mean', 'count', 'std']).reset_index()
    group_stats.columns = ['instant_bookable', 'mean_reviews_per_month', 'sample_size', 'std']
    st.markdown("### 📋 Group Means and Sample Sizes")
    st.dataframe(group_stats)

    st.markdown("### 📈 Normality Check")

    col_norm1, col_norm2 = st.columns(2)

    with col_norm1:
        st.markdown("#### Shapiro-Wilk Test")
        if len(group_instant) > 5000:
            shapiro_instant_sample = group_instant.sample(5000, random_state=42)
            shapiro_non_instant_sample = group_non_instant.sample(5000, random_state=42)
        else:
            shapiro_instant_sample = group_instant
            shapiro_non_instant_sample = group_non_instant

        shapiro_instant = stats.shapiro(shapiro_instant_sample)
        shapiro_non_instant = stats.shapiro(shapiro_non_instant_sample)

        shapiro_df = pd.DataFrame({
            'Group': ['Instant Bookable', 'Non-Instant Bookable'],
            'Statistic': [f'{shapiro_instant.statistic:.4f}', f'{shapiro_non_instant.statistic:.4f}'],
            'p-value': [f'{shapiro_instant.pvalue:.4e}', f'{shapiro_non_instant.pvalue:.4e}'],
            'Normal (p > 0.05)': ['Yes' if shapiro_instant.pvalue > 0.05 else 'No',
                                   'Yes' if shapiro_non_instant.pvalue > 0.05 else 'No']
        })
        st.dataframe(shapiro_df, use_container_width=True)
        st.caption("If p-value > 0.05, we fail to reject the null hypothesis that the data is normally distributed.")

    with col_norm2:
        st.markdown("#### Levene's Test for Variance Equality")
        levene_stat, levene_p = stats.levene(group_instant, group_non_instant)
        levene_df = pd.DataFrame({
            'Test': ['Levene\'s Test'],
            'Statistic': [f'{levene_stat:.4f}'],
            'p-value': [f'{levene_p:.4e}'],
            'Equal Variance (p > 0.05)': ['Yes' if levene_p > 0.05 else 'No']
        })
        st.dataframe(levene_df, use_container_width=True)
        st.caption("If p-value > 0.05, we fail to reject the null hypothesis that variances are equal.")

    col_vis1, col_vis2 = st.columns(2)

    with col_vis1:
        st.markdown("#### Histogram")
        fig_hist = px.histogram(instant_book_df, x='reviews_per_month', color='instant_bookable',
                                title='Distribution of Reviews per Month by Group',
                                barmode='overlay', opacity=0.7)
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_vis2:
        st.markdown("#### Q-Q Plot")
        qq_instant = stats.probplot(group_instant, dist="norm")
        qq_non_instant = stats.probplot(group_non_instant, dist="norm")

        qq_instant_df = pd.DataFrame({
            'Theoretical Quantiles': qq_instant[0][0],
            'Sample Quantiles': qq_instant[0][1],
            'Group': 'Instant Bookable'
        })
        qq_non_instant_df = pd.DataFrame({
            'Theoretical Quantiles': qq_non_instant[0][0],
            'Sample Quantiles': qq_non_instant[0][1],
            'Group': 'Non-Instant'
        })
        qq_combined = pd.concat([qq_instant_df, qq_non_instant_df])

        fig_qq = px.scatter(qq_combined, x='Theoretical Quantiles', y='Sample Quantiles',
                           color='Group', title='Q-Q Plot Comparison',
                           facet_col='Group')
        fig_qq.update_layout(showlegend=True)
        st.plotly_chart(fig_qq, use_container_width=True)

    st.markdown("### 📊 Independent Samples t-Test Results")

    if levene_p > 0.05:
        equal_var = True
        st.info("Equal variances assumed (Levene's test p > 0.05). Using standard t-test.")
    else:
        equal_var = False
        st.warning("Unequal variances detected (Levene's test p <= 0.05). Using Welch's t-test.")

    t_stat, t_pvalue = stats.ttest_ind(group_instant, group_non_instant, equal_var=equal_var)

    t_result_df = pd.DataFrame({
        'Statistic': ['t-statistic', 'p-value (two-tailed)'],
        'Value': [f'{t_stat:.4f}', f'{t_pvalue:.4e}']
    })
    st.dataframe(t_result_df)

    st.markdown("### 📝 Statistical Analysis Summary")
    st.write(f"**t-Test Result**: The independent samples t-test yielded a t-statistic of {t_stat:.4f} with a p-value of {t_pvalue:.4e}.")
    if t_pvalue < 0.05:
        st.write("Since the p-value is less than 0.05, we reject the null hypothesis and conclude that there is a statistically significant difference in reviews per month between instant bookable and non-instant listings.")
    else:
        st.write("Since the p-value is greater than or equal to 0.05, we fail to reject the null hypothesis. There is no statistically significant difference in reviews per month between the two groups.")

    st.markdown("### ✅ Recommendation")
    if t_pvalue < 0.05:
        mean_instant = group_instant.mean()
        mean_non_instant = group_non_instant.mean()
        diff = mean_instant - mean_non_instant
        if diff > 0:
            st.success(f"Instant bookable listings show significantly {'higher' if diff > 0 else 'lower'} booking engagement (mean difference: {diff:.4f} reviews/month).")
            st.write("This suggests that enabling instant booking may increase guest engagement and booking frequency.")
        else:
            st.error(f"Non-instant listings show significantly higher booking engagement (mean difference: {abs(diff):.4f} reviews/month).")
            st.write("This suggests that instant booking may not be beneficial for booking engagement.")
    else:
        st.warning("No statistically significant difference found between instant bookable and non-instant listings.")
        st.write("This suggests that instant bookable status may not be a significant factor in booking engagement.")


conn.close()
