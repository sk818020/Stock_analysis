import pandas as pd
import streamlit as st
import yfinance as yf
import plotly_express as px

# Page layout and title
st.set_page_config(layout='wide')

# Get ticker data
ticker_list = pd.read_csv(r'ticker_list.csv')

# Create side bar
st.sidebar.title('User Inputs')
#st.session_state['ticker'] = st.sidebar.selectbox(label='Select a stock symbol',
#                              options=ticker_list['Symbol'].unique())


def clean_data(sym_con):
    clean_df = sym_con.income_stmt.reset_index().copy()
    clean_df = clean_df.melt(id_vars=['index'])
    clean_df.columns = ['IS_Category', 'Date', '$_amount']
    clean_df['Date'] = pd.to_datetime(clean_df['Date'])
    return clean_df


# Get connection to the stock symbol and define variables
sym_con = yf.Ticker(st.session_state['ticker'])
st.markdown(f"<h1 style='font-size:45px;'>Stock Basics - {sym_con.info['shortName']}</h1",
            unsafe_allow_html=True)
sector = sym_con.info['sector']
#industry = sym_con.info['industry']
industries = pd.DataFrame(yf.Sector(sector.lower().replace(' ', '-')).industries)
data = clean_data(sym_con)
is_item = st.sidebar.selectbox(label='Income statement category:',
                               options=data['IS_Category'].unique(),
                               index=21)

col1, col2 = st.columns([7,5])

with col1:
    st.markdown(f'__{st.session_state['ticker']} - stock price past year with moving average__')
    stock_data = sym_con.history(period = '1y').reset_index()
    stock_data['Date'] = pd.to_datetime(stock_data['Date'])
    day_avg = st.number_input('Number of days for moving average',
                              min_value = int(5),
                              max_value=int(len(stock_data)*.75),
                              value = int(30))
    stock_data['Rolling_Average'] = stock_data['Close'].rolling(window = day_avg).mean()
    fig_price_plot = px.line(stock_data,
                             x = 'Date',
                             y = ['Rolling_Average', 'Close'])
    st.plotly_chart(fig_price_plot)
    is_items_table = pd.DataFrame(sym_con.income_stmt.reset_index())



with col2:
    fig = px.bar(data.query(f"IS_Category == '{is_item}'"), x='Date', y='$_amount',
                 title = f'{is_item} by year (change using category selector to left)',
                 text = '$_amount',
                 height=600)
    st.plotly_chart(fig)


col5, col6 = st.columns([7, 5])
with col5:
    filter_list = ['Total Revenue', 'Cost Of Revenue', 'Total Expenses',
                   'Operating Expense', 'General And Administrative Expense',
                   'Selling and Marketing Expense', 'Net Income']
    is_items_table = is_items_table[is_items_table['index'].isin(filter_list)]
    st.markdown('__Key Income Statement Lines__')
    st.data_editor(is_items_table)
with col6:
    st.markdown('__Selected Income Statement Line by Year__')
    st.data_editor(data.query(f"IS_Category == '{is_item}'"), hide_index=True)
