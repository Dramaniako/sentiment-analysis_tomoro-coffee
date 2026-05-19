import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Tomoro Sentiment Dashboard", layout="wide")

st.title("☕ Tomoro Coffee Sentiment Analysis")

# Load your processed data
df = pd.read_csv('tomoro_sentiment_results.csv')

# Create a layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("Sentiment Distribution")
    fig = px.pie(df, names='sentiment', hole=0.3, color='sentiment', 
                 color_discrete_map={'positive':'green', 'negative':'red', 'neutral':'gray'})
    st.plotly_chart(fig)

with col2:
    st.subheader("Recent Negative Feedback")
    negative_reviews = df[df['sentiment'] == 'negative'][['text', 'rating']]
    st.dataframe(negative_reviews.head(10))

# Show raw data
if st.checkbox("Show raw data"):
    st.write(df)