import pandas as pd
import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import plotly_express as px
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from streamlit import title

# Establishing sentiment analyzer parameters
nltk.download('vader_lexicon')
sia= SentimentIntensityAnalyzer()

# Page layout and title
st.set_page_config(layout = 'wide')
st.title('Stock Analysis')
st.subheader('Created by: Jared Heiner, Page last updated on 7/25/2025')



ticker_list = pd.read_csv(r'/ticker_list.csv')
st.sidebar.title('User Inputs')
ticker = st.sidebar.selectbox(label='Select a stock symbol',
                              options=ticker_list['Symbol'].unique(),
                              index = 1586)
sym_con = yf.Ticker(ticker)
sector = sym_con.info['sector']
industries = pd.DataFrame(yf.Sector(sector.lower().replace(' ', '-')).industries)

def clean_data(sym_con):
    inc_stmt = sym_con.income_stmt.reset_index().copy()
    inc_stmt = inc_stmt.melt(id_vars = ['index'])
    inc_stmt.columns = ['IS_Category', 'Date', '$_amount']
    inc_stmt['Date'] = pd.to_datetime(inc_stmt['Date'])
    return inc_stmt

data = clean_data(sym_con)

is_item = st.sidebar.selectbox(label = 'Income statement category:',
                               options = data['IS_Category'].unique(),
                               index = 21)
industry = st.sidebar.selectbox('Select the comparator industry',
                                options = industries.index)
industries_sym = industries.loc[industry, 'symbol']
#industry_sym = industries

tab1, tab2 = st.tabs(['Stock Basics', 'Market Information'])

with tab1:
    col1, col2 = st.columns([7,5])

    with col1:
        stock_data = sym_con.history(period = '1y').reset_index()
        stock_data['Date'] = pd.to_datetime(stock_data['Date'])
        fig_price_plot = px.line(stock_data, x = 'Date',
                                 y = 'Close',
                                 title = f'{ticker} - Daily Stock Price - Past Year')
        st.plotly_chart(fig_price_plot)
        is_items_table = pd.DataFrame(sym_con.income_stmt.reset_index())
        filter_list = ['Total Revenue', 'Cost Of Revenue', 'Total Expenses',
                       'Operating Expense', 'General And Administrative Expense',
                       'Selling and Marketing Expense', 'Net Income']
        is_items_table = is_items_table[is_items_table['index'].isin(filter_list)]
        st.markdown('__Key Income Statement Lines__')
        st.dataframe(is_items_table, hide_index=True)

    with col2:
        fig = px.bar(data.query(f"IS_Category == '{is_item}'"), x='Date', y='$_amount',
                     title = f'{is_item} by year (change using category selector to left)',
                     text = '$_amount')
        st.plotly_chart(fig, )
        st.markdown('__Selected Income Statement Line by Year__')
        st.data_editor(data.query(f"IS_Category == '{is_item}'"), hide_index=True)

    col_news1, col_news2 = st.columns([10,2])


with tab2:
    col3, col4 = st.columns(2)
    company_change = yf.Ticker(ticker).history('1y').reset_index()
    sector_change = yf.Ticker(industries_sym).history('1y').reset_index()
    company_change['prc_change'] = company_change['Close'].pct_change()
    sector_change['prc_change'] = sector_change['Close'].pct_change()
    company_change = pd.merge(left=company_change,
                              right=sector_change[['Date', 'prc_change']],
                              how='left', on='Date')
    new_names = {
        'prc_change_x': f'{ticker}_prc_change',
        'prc_change_y': f'sect_prc_change'
    }
    company_change = company_change.rename(columns=new_names)
    with col3:
        fig = px.line(company_change,
                      x = 'Date',
                      y = [f'{ticker}_prc_change', 'sect_prc_change'],
                      title = f"Daily returns for {ticker} and it's sector")
        st.plotly_chart(fig)
    with col4:
        fig = px.scatter(company_change,
                         x = f'sect_prc_change',
                         y = f'{ticker}_prc_change',
                         title = f'{ticker} vs {industry} Daily Returns w/ Correlation',
                         trendline = 'ols')
        st.plotly_chart(fig)
    col5, col6 = st.columns(2, gap='large')
    with col5:
        st.markdown(f'__Top Companies in {industry}, by market weight__')
        st.table(yf.Industry(industry).top_companies[0:10])
    with col6:
        st.markdown(f'__Top 5 Growth Companies in {industry}, by est. Growth__')
        st.table(yf.Industry(industry).top_growth_companies[0:10])

    # Section for news
    st.markdown(f'__Most Recent News for {ticker} w/ Sentiment Scores*__')
    st.write('Sentiment scores measure how positive, negative, or neutral an article is.')
    df_news = pd.DataFrame()
    for i in range(len(sym_con.news)):
        title = sym_con.news[i].get('content', {}).get('title')
        date = sym_con.news[i].get('content', {}).get('pubDate')
        print(date)
        url = sym_con.news[i].get('content', {}).get('canonicalUrl', {}).get('url')
        sentiment_scores = sia.polarity_scores(sym_con.news[i].get('content', {}).get('summary'))
        data_news = {
            'Date': f'{date[0:10]}',
            'Title': f'{title[0:35]}...',
            'Link': f'{url}',
            'Positive': f'{sentiment_scores['pos']}',
            'Negative': f'{sentiment_scores['neg']}',
            'Neutral': f'{sentiment_scores['neu']}',
            'Compound': f'{sentiment_scores['compound']}'
        }
        holder = pd.DataFrame(data_news, index=[0])
        df_news = pd.concat([df_news, holder], ignore_index=True)
    st.data_editor(
        df_news,
        column_config={
            "Link": st.column_config.LinkColumn(
                "Link to Site",
                validate=r"^https://[a-z]+\.streamlit\.app$",
                max_chars=100,
                display_text=r"Go to article"
            )
        },
        hide_index=True,
    )
    st.markdown('_Sentiment scores are calculated using the NLTK-VADER algorithm._')



#st.data_editor(is_data, hide_index = True)