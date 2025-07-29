import pandas as pd
import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import plotly_express as px
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

# Establishing sentiment analyzer parameters
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

# Page layout and title
st.set_page_config(layout='wide')

def clean_data(sym_con):
    clean_df = sym_con.income_stmt.reset_index().copy()
    clean_df = clean_df.melt(id_vars=['index'])
    clean_df.columns = ['IS_Category', 'Date', '$_amount']
    clean_df['Date'] = pd.to_datetime(clean_df['Date'])
    return clean_df


# Get connection to the stock symbol and define variables
sym_con = yf.Ticker(st.session_state['ticker'])
st.markdown(f"<h1 style='font-size:45px;'>Market Overview - {sym_con.info['shortName']}</h1 \n"
            f"<h2 style='font-size:20px;'>Note: You can change the sector using the selector in the side bar.</h2",
            unsafe_allow_html=True)
sector = sym_con.info['sector']
#industry = sym_con.info['industry']
industries = pd.DataFrame(yf.Sector(sector.lower().replace(' ', '-')).industries)
data = clean_data(sym_con)
industry = st.sidebar.selectbox('Select the comparator industry',
                                options=industries.index)
industries_sym = industries.loc[industry, 'symbol']

st.divider()

# Develop top of page (above graphs)
col3, col4 = st.columns(2)
company_change = yf.Ticker(st.session_state['ticker']).history('1y').reset_index()
sector_change = yf.Ticker(industries_sym).history('1y').reset_index()
company_change['prc_change'] = company_change['Close'].pct_change()
sector_change['prc_change'] = sector_change['Close'].pct_change()
company_change = pd.merge(left=company_change,
                          right=sector_change[['Date', 'prc_change']],
                          how='left', on='Date')
new_names = {
    'prc_change_x': f'{st.session_state['ticker']}_prc_change',
    'prc_change_y': f'sect_prc_change'
}
company_change = company_change.rename(columns=new_names)
with col3:
    fig = px.line(company_change,
                  x = 'Date',
                  y = [f'{st.session_state['ticker']}_prc_change', 'sect_prc_change'],
                  title = f"Daily returns for {st.session_state['ticker']} and it's sector")
    st.plotly_chart(fig)
with col4:
    fig = px.scatter(company_change,
                     x = f'sect_prc_change',
                     y = f'{st.session_state['ticker']}_prc_change',
                     title = f'{st.session_state['ticker']} vs {industry} Daily Returns w/ Correlation',
                     trendline = 'ols')
    st.plotly_chart(fig)

st.divider()
col5, col6 = st.columns(2, gap='large')
with col5:
    st.markdown(f'__Top Companies in {industry}, by market weight__')
    st.table(yf.Industry(industry).top_companies[0:10])
with col6:
    st.markdown(f'__Top 5 Growth Companies in {industry}, by est. Growth__')
    st.table(yf.Industry(industry).top_growth_companies[0:10])

st.divider()

# Section for news

col7, col8 = st.columns(2)

with col7:
    st.markdown(f'__Most Recent News for {st.session_state['ticker']} w/ Sentiment Scores*__')
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
            'Title': f'{title[0:30]}...',
            'Link': f'{url}',
            'Positive': '{x}'.format(x = sentiment_scores['pos']),
            'Negative': '{y}'.format(y = sentiment_scores['neg']),
    #           'Neutral': '{z}'.format(z = sentiment_scores['neu']),
    #           'Compound': '{w}'.format(w = sentiment_scores['compound'])

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
with col8:
    holder = pd.DataFrame(data_news, index=[0])
    df_news = pd.concat([df_news, holder], ignore_index=True)
    df_news = pd.melt(df_news, id_vars=['Date', 'Title', 'Link'])
    df_news['value'] = df_news['value'].astype(float)
    df_news = df_news.rename(columns={'variable': 'PosNeg'})
    df_news_groups = df_news.groupby(['PosNeg']).agg({'value': 'mean'})
    fig = px.bar(df_news_groups.reset_index(),
                 y ='value',
                 x = 'PosNeg',
                 title = 'Average positive / negative value',
                 height = 551)
    fig.update_layout(
        xaxis_title='',
        yaxis_title=''
    )
    st.plotly_chart(fig)

st.markdown('_Sentiment scores are calculated using the NLTK-VADER algorithm._')