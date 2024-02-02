import streamlit as st
import pandas as pd
from wallet_connect import wallet_connect

# TODO:
# - [ ] create cron job for data refresh
# - [ ] get data from api
# - [ ] add amounts in sDAI
# - [ ] add breakeven calculation


st.set_page_config(
    page_title='sDAI Calculator',
    page_icon='spark_logo.svg',
    layout='wide',
    initial_sidebar_state='collapsed'
)

# backend
def read_csv_and_convert_date(filename, date_column):
    df = pd.read_csv('data/'+filename)
    df[date_column] = pd.to_datetime(df[date_column])
    df[date_column] = df[date_column].dt.date
    return df

@st.cache_data
def get_dsr_rate():
    return read_csv_and_convert_date('pot_dsr.csv', 'datetime')

@st.cache_data
def get_sdai_wallets():
    return read_csv_and_convert_date('sdai_wallets.csv', 'date')

def process_user_transactions(df_transactions):
    df_transactions['date'] = pd.to_datetime(df_transactions['date'])
    df_dates = pd.DataFrame(pd.date_range(start=df_transactions['date'].min(), end=pd.to_datetime('today')), columns=['date'])
    df_daily = pd.concat([df_transactions, df_dates], axis=0, ignore_index=True)
    df_daily.sort_values('date', inplace=True)
    df_daily['balance'] = df_daily['amount'].cumsum()
    df_daily.drop(columns=['amount'], inplace=True)
    df_daily['balance'].fillna(method='ffill', inplace=True)
    df_daily['date'] = df_daily['date'].dt.date
    df_daily = df_daily.drop_duplicates(subset='date', keep='last')
    return df_daily

def calculate_return(df_daily, df_dsr):
    df_merged = pd.merge(df_daily, df_dsr, how='outer', left_on='date', right_on='datetime')
    df_merged['date'] = df_merged['date'].combine_first(df_merged['datetime'])
    df_merged.drop('datetime', axis=1, inplace=True)
    df_merged.sort_values(by='date', inplace=True)
    df_merged['rate'].fillna(method='ffill', inplace=True)
    df_merged.dropna(subset=['balance'], inplace=True)
    df_merged['apr'] = (1 + df_merged['rate'])**(1/365) - 1
    df_merged['return'] = df_merged['balance'] * df_merged['apr']
    return df_merged

# utils
def pretty_percent(percent):
    formatted_string = '{:,.2f}%'.format(percent * 100)
    return formatted_string

def pretty_number(number):
    try:
        integer_digits = len(str(int(number)))
        if integer_digits > 2:
            return '{:,.2f}'.format(number)
        else:
            return '{:,.4f}'.format(number)
        return formatted_string
    except:
        return '{:,.2f}'.format(number)
    
def pretty_dai(number):
    formatted_string = '{:,.2f} DAI'.format(number)
    return formatted_string

# frontend
def main():
    st.title('💸 sDAI Calculator 💸')

    col1, col2 = st.columns([3,1])
    with col1:
        st.caption('A simple calculator to know the effective yield of your sDAI.')

    with col2:
        st.caption('data updated on 19th Dec 2023')

    st.write('') # space
    success = False # control flow for the bulk of calculations

    col3, col4, col5, col6 = st.columns([3,1,2,2])
    with col3:
        uploaded_sdai = st.file_uploader('Upload your sDAI transactions', type=['csv'])
        st.caption('Upload a CSV file with 2 columns, date (yyyy-mm-dd) and amount (DAI amount w/ decimal point, negative when exiting sDAI).')
        with open('example_sdai.csv') as f:
            st.download_button('Download sample sDAI transactions', f, file_name='sample_sdai.csv', mime='text/csv')
    with col4:
        st.write('') # space
    with col5:
        st.write('') # space
        st.title('  or')
    with col6:
        connect_button = wallet_connect(label="wallet",key="wallet")
        st.write('or') # space
        input_wallet = st.text_input('Enter your wallet address', value=None)

    st.write('') # space
    status_update = st.empty()
    st.divider()

    if uploaded_sdai is not None:

        try:
            df_tx_user = pd.read_csv(uploaded_sdai)

            try:
                date_column = df_tx_user['date']
                amount_column = df_tx_user['amount']
                st.success('the csv file has been processed correctly')
                success = True
            except:
                st.warning('the csv file does not contain the correct format, please try using the sample file provided below.')
                success = False
        except:
            st.warning('there was an error, please try to uploading a valid csv file')
            success = False

    if len(connect_button) > 5 or input_wallet is not None:
        if len(connect_button) > 5:
            wallet_address = str(connect_button).strip().lower()
        else:
            wallet_address = str(input_wallet).strip().lower()

        try:
            df_transactions = get_sdai_wallets()
            df_transactions['wallet_address'] = df_transactions['wallet_address'].astype(str).str.strip().str.lower()
            df_tx_user = df_transactions[df_transactions['wallet_address'] == wallet_address]
            df_tx_user.drop(columns=['wallet_address'], inplace=True)

            if df_tx_user.empty:
                status_update.warning('the wallet address has no sDAI transactions')
                success = False
            else:
                try:
                    date_column = df_tx_user['date']
                    amount_column = df_tx_user['amount']
                    status_update.success('the wallet transactions have been successfully retrieved')
                    success = True
                except:
                    status_update.warning('there was an error reading the wallet transactions, please try again')
                    success = False
        except:
            status_update = st.warning('there was an error with wallet connect, please try again')
            success = False

    if success is True:
        df_dsr = get_dsr_rate()

        # process data
        df_daily = process_user_transactions(df_tx_user)
        df_merged = calculate_return(df_daily, df_dsr)
        
        date_range = st.date_input('select a date range', value=[df_merged['date'].min(), df_merged['date'].max()])
        df_merged = df_merged[(df_merged['date'] >= date_range[0]) & (df_merged['date'] <= date_range[1])]

        final_df = st.empty()
        
        average_balance = df_merged['balance'].mean()
        weighted_average_yield = (df_merged['balance'] * df_merged['rate']).sum() / df_merged['balance'].sum()
        weighted_average_rate = (1 + weighted_average_yield / 31536000) ** 31536000 - 1
        total_return = df_merged['return'].sum()
        total_percent_return = total_return / average_balance

        col01, col02, col03, col04 = st.columns([1,1,1,1])
        with col01:
            st.metric(label='effective return', value=pretty_dai(total_return))
        with col02:
            st.metric(label='effective percent return', value=pretty_percent(total_percent_return))
        with col03:
            st.metric(label='annual percentage yield (APY)', value=pretty_percent(weighted_average_rate))
        with col04:
            st.metric(label='annual percentage rate (APR)', value=pretty_percent(weighted_average_yield))

        with final_df.container():
            df_merged.rename(columns={'balance':'DAI nominal balance',
                                    'rate':'APY',
                                    'apr':'percent return',
                                    'return':'return',
                                    }, 
                            inplace=True)
            st.write(df_merged)

        st.write('') # space
        cola, colb = st.columns([1,1])
        with cola:
            st.download_button('Download your sDAI calculations', data=df_merged.to_csv(index=None), file_name='sdai_yield.csv', mime='text/csv')
        with colb:    
            st.download_button('Download historical DSR APY', data=df_dsr.to_csv(), file_name='pot_dsr.csv', mime='text/csv')
    else:
        st.write('')

# app
if __name__ == '__main__':
    main()