import pandas as pd
import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import plotly_express as px
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from streamlit_plotly_events import plotly_events
from streamlit import title
from stockdex import Ticker
import plotly
from streamlit_extras.stylable_container import stylable_container

# Establishing sentiment analyzer parameters
nltk.download('vader_lexicon')
sia= SentimentIntensityAnalyzer()

# Page layout and title
st.set_page_config(layout = 'wide')

# Get ticker data
ticker_list = pd.read_csv(r'ticker_list.csv')

# Create side bar
st.sidebar.title('User Inputs')
st.session_state['ticker'] = st.sidebar.selectbox(label='Select a stock symbol',
                              options=ticker_list['Symbol'].unique(),
                              index = 1586)

def clean_data(sym_con):
    clean_df = sym_con.income_stmt.reset_index().copy()
    clean_df = clean_df.melt(id_vars = ['index'])
    clean_df.columns = ['IS_Category', 'Date', '$_amount']
    clean_df['Date'] = pd.to_datetime(clean_df['Date'])
    return clean_df

# Get connection to the stock symbol and define variables
sym_con = yf.Ticker(st.session_state['ticker'])
st.markdown(f"<h1 style='font-size:45px;'>Stock Analysis - {sym_con.info['shortName']}</h1",
            unsafe_allow_html = True)

# Develop top of page (above graphs)
col1, col2 = st.columns(2)
with col1:
    st.subheader('Company Overview ')
    st.write(' ')
    st.markdown(f"__Company Name:__ {sym_con.info['shortName']}")
    st.markdown(f"__Sector__: {sym_con.info['sector']}")
    st.markdown(f"__Industry__: {sym_con.info['industry']}")
    st.markdown(f"__Website:__ [{sym_con.info['shortName']}]({sym_con.info['website']})")
    try:
        st.markdown(f"__Investor Relations Website:__ [{sym_con.info['shortName']}]({sym_con.info['irWebsite']})")
    except:
        st.write()
    st.markdown(f"__Beta__: {sym_con.info['beta']}")
    st.markdown(f"__Market Cap__: ${round(sym_con.info['marketCap']/1000000000,1):,.1f} billion")
    st.markdown(f"__Avg. Analyst Rating__: {sym_con.info['averageAnalystRating']}")
with    col2:
    sankey = Ticker(ticker = st.session_state['ticker'])
    fig = sankey.plot_yahoo_api_financials()
    fig.update_layout(
        xaxis_title = "",
        yaxis_title = "$B",

    )
    st.plotly_chart(fig)

col3, col4 = st.columns(2)
with col3:
    st.markdown("<h2 style='font-size:20px;'><p1>Company Description:</h2>",
                unsafe_allow_html=True)
    st.markdown(sym_con.info['longBusinessSummary'])
with col4:
    con = Ticker(ticker = st.session_state['ticker'])
    st.plotly_chart(con.plot_yahoo_api_balance_sheet())
