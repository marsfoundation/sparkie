import pandas as pd
import streamlit as st

#TODO:
# - validation of unselected collateral
# - button add collateral
# - borrow asset price variable
# collateral needed (vs max borrow)
# simulation (e.g. if you opened the position last month, would you have been liquidatied?)
# fee (need to also add loan duration)
# use cases(lending arbitrage w/ expected breakeven, long/short/token farming, for looping need "x5" instead of max ltv)
# add sdai yield
# number input field empty rather than 0.00
# clean up assets/markets table (category, name -> emode_name)
# validate selected_collateral so that you cannot choose it twice, nor choose it as a borrow asset

# Set page configuration
st.set_page_config(
    page_title='SparkLend Calculator',
    page_icon='spark_logo.svg',
    layout='wide',
    initial_sidebar_state='collapsed'
)

# utils
def get_param(df,selected_network,selected_asset,param):
    return df[(df['underlying_symbol'] == selected_asset) & (df['network'] == selected_network)][param].unique()[0]    

def get_ltv(df,selected_network,selected_asset,emode):
    if emode == None:
        return df[(df['underlying_symbol'] == selected_asset) & (df['network'] == selected_network)]['ltv'].unique()[0]    
    else:
        return df[(df['underlying_symbol'] == selected_asset) & (df['network'] == selected_network)]['ltv_emode'].unique()[0]    

def get_lt(df,selected_network,selected_asset,emode):
    if emode == None:
        return df[(df['underlying_symbol'] == selected_asset) & (df['network'] == selected_network)]['liquidation_threshold'].unique()[0]    
    else:
        return df[(df['underlying_symbol'] == selected_asset) & (df['network'] == selected_network)]['liquidation_threshold_emode'].unique()[0]    

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

def usd_price(df,selected_asset,selected_network='ethereum'):
    return df[(df['underlying_symbol'] == selected_asset) & (df['network'] == selected_network)]['underlying_price'].values[0]

def usd_value(df,selected_amount,selected_asset):
    return usd_price(df,selected_asset) * selected_amount

def pretty_usd(usd_value):
    formatted_string = '{:,.2f} USD'.format(usd_value)
    return formatted_string

# backend
# @st.cache_data
def get_market_data():
    df = pd.read_csv('data/assets.csv')
    return df

def available_markets(df):
    return df['network'].unique()

def available_collaterals(df,network):
    available_collaterals = df[ (df['usage_as_collateral_enabled'] == True) & (df['network'] == network) & (df['underlying_symbol'] != 'GNO') ][['underlying_symbol','emode_category']] #GNO should be removed based on market data
    return available_collaterals

def available_borrows(df,network,emode):
    if emode == None:
        available_borrows = df[(df['borrowing_enabled'] == True) & (df['network'] == network) ]['underlying_symbol'].unique()
    # & (df[~df['underlying_symbol'].isin(st.session_state['collaterals'])])
    else:
        available_borrows = df[(df['borrowing_enabled'] == True) & (df['network'] == network) & (df['emode_category'] == emode)]['underlying_symbol'].unique()
    return available_borrows

def liquidation_threshold(df,selected_network,selected_collateral,emode):
    if emode == None:
        return df[(df['underlying_symbol'] == selected_collateral) & (df['network'] == selected_network)]['liquidation_threshold'].unique()[0]
    else:
        return df[(df['underlying_symbol'] == selected_collateral) & (df['network'] == selected_network)]['liquidation_threshold_emode'].unique()[0]

def heath_factor(df,selected_network,collaterals,selected_borrow,amount_borrow,emode):
    usd_borrow = usd_value(df,amount_borrow,selected_borrow)
    collateral_capacity = 0
    for key in collaterals:
        usd_collateral = usd_value(df,collaterals[key],key)
        collateral_liq_threshold = liquidation_threshold(df,selected_network,key,emode)
        collateral_capacity += (usd_collateral * collateral_liq_threshold)
    health_factor = collateral_capacity / usd_borrow
    return health_factor.item()

def liquidation_price(df,selected_network,collaterals,selected_borrow,amount_borrow,selected_collateral=None,emode_category=None):
    collateral_capacity = 0
    other_usd_collateral_capacity = 0
    usd_borrow = usd_value(df,amount_borrow,selected_borrow)

    for key in collaterals: #two concurrent flows to account for collaterals goin 0 without liquidating position
        if key == selected_collateral:
            amount_collateral = collaterals[key]
            amount_collateral_usd = 0
        else:
            amount_collateral = usd_value(df,collaterals[key],key) / usd_value(df,collaterals[selected_collateral],selected_collateral) #synthetic rate via USD eg. ETH/BTC
            amount_collateral_usd = usd_value(df,collaterals[key],key)

        collateral_liq_threshold = liquidation_threshold(df,selected_network,key,emode_category)

        liq_factor = amount_collateral * collateral_liq_threshold
        collateral_capacity += liq_factor

        liq_factor_usd = amount_collateral_usd * collateral_liq_threshold
        other_usd_collateral_capacity += liq_factor_usd

    if other_usd_collateral_capacity > usd_borrow:
        liquidation_price = float('inf') #even if collateral goes to 0 it does not trigger a liquidation
    else:
        liquidation_price = usd_borrow / collateral_capacity
    return liquidation_price

def max_borrow_amount(df,selected_network,collaterals,selected_borrow,emode):
    collateral_capacity = 0
    for key in collaterals:
        usd_collateral = usd_value(df,collaterals[key],key)
        max_ltv = get_ltv(df,selected_network,key,emode)
        collateral_capacity += (usd_collateral * max_ltv)
    max_borrow = collateral_capacity / usd_price(df,selected_borrow)
    return max_borrow.item()

# frontend
def home():
    df = get_market_data()
    st.title('SparkLend Calculator')
    # title section
    col01, col02 = st.columns([3,1])
    with col01:
        st.caption('A simple calculator to know liquidation price and maximum borrowable amount for your position.')
    with col02:
        st.caption('data updated on 25th Jan 2024')

    st.write("") # space

    # network section
    selected_network = st.selectbox('select network', available_markets(df))
    
    # collateral section
    st.divider()
    colq, colw, cole = st.columns([2,1,2])
    with colq:
        collateral_quantity = st.slider('select number of collaterals',1, 4, 1, 1)
    with cole:
        emodes = {
            'none': None,
            'ETH': 1,
            'USD': 2,
        }
        selected_emode = st.radio('select emode', list(emodes.keys()), horizontal=True)

    # define collaterals available to user
    collaterals_available = available_collaterals(df,selected_network)
    collaterals_available['emode_category'] = collaterals_available['emode_category'].astype(int)
    if selected_emode == 'none':
        pass
    elif selected_emode == 'ETH':
        collaterals_available = collaterals_available[collaterals_available['emode_category'] == emodes[selected_emode]]['underlying_symbol']
    elif selected_emode == 'USD':
        collaterals_available = collaterals_available[collaterals_available['emode_category'] == emodes[selected_emode]]['underlying_symbol']

    col1, col2 = st.columns(2)
    usd_collaterals_total = 0
    st.session_state['collaterals'] = {}
    for i in range(collateral_quantity):
        with col1:
            selected_collateral = st.selectbox('select collateral asset', collaterals_available, key='selected_collateral_' + str(i))
            
            if get_param(df,selected_network,selected_collateral,'supply_cap') > 0:

                supply_headroom = pretty_number(get_param(df,selected_network,selected_collateral,'supply_cap') - get_param(df,selected_network,selected_collateral,'total_supply'))
            else:
                supply_headroom = 'unlimited'
            
            st.write(
                'available capacity:', supply_headroom, ' | ',
                'supply rate:', pretty_percent(get_param(df,selected_network,selected_collateral,'supply_rate')), ' | ',
                'max ltv:', pretty_percent(get_ltv(df,selected_network,selected_collateral,emodes[selected_emode])), ' | ',
                'lt:', pretty_percent(get_lt(df,selected_network,selected_collateral,emodes[selected_emode])),
                )

        with col2:
            amount_collateral = st.number_input('enter collateral amount', step=1.00, format='%.2f', min_value=0.0, key='amount_collateral_' + str(i))
            usd_collateral = usd_value(df,amount_collateral,selected_collateral)
            usd_collaterals_total += usd_collateral
            st.write(pretty_usd(usd_collateral))

        st.session_state['collaterals'].update({selected_collateral: amount_collateral})

    for key in st.session_state.keys():
        print(key) # delete all other session items, might lead to issues in the future
        if key != 'collaterals':
            del st.session_state[key]

    # borrow section
    st.divider()
    col3, col4 = st.columns(2)
    with col3:
        selected_borrow = st.selectbox('select borrow asset', available_borrows(df,selected_network,emodes[selected_emode]))
        st.write(
            'available liquidity:', pretty_number(get_param(df,selected_network,selected_borrow,'available_liquidity')), ' | ',
            'borrow rate:', pretty_percent(get_param(df,selected_network,selected_borrow,'variable_borrow_rate')),
            )

    with col4:
        amount_borrow = st.number_input('enter borrow amount', step=1.00, format='%.2f', min_value=0.0) # %d %e %f %g %i %u
        usd_borrow_value = pretty_usd(usd_value(df,amount_borrow,selected_borrow))
        st.write(usd_borrow_value)

    # results section
    st.divider()
    cola, colb, colc = st.columns(3)

    # health factor
    with colb:
        health_factor = heath_factor(df,selected_network, st.session_state['collaterals'],selected_borrow,amount_borrow,selected_emode)
        if health_factor < 1:
            st.metric(label='Health Factor', value=pretty_number(health_factor), delta='liquidated', delta_color='inverse', help='')
        else:
            st.metric(label='Health Factor', value=pretty_number(health_factor), help='')

    # liquidation price
    with cola:
        liq_p = st.empty()
        if len(st.session_state['collaterals']) > 1:
            liq_price_collateral = st.selectbox('select collateral asset', st.session_state['collaterals'].keys())
        else:
            liq_price_collateral = list(st.session_state['collaterals'].keys())[0]
        liq_price = liquidation_price(df,selected_network,st.session_state['collaterals'],selected_borrow,amount_borrow,liq_price_collateral)
        current_price = usd_price(df,liq_price_collateral)
        drawdown = -(current_price - liq_price) / current_price
        delta_text = pretty_percent(drawdown)+' to liquidation'
        if health_factor < 1:
            liq_p.metric(label='Liquidation Price', value=pretty_number(liq_price), delta='liquidated', delta_color='inverse', help='inf: infinite liquidation price if collateral going to 0 does not liquidate the position.')
        else:
            liq_p.metric(label='Liquidation Price', value=pretty_number(liq_price), delta=delta_text, delta_color='off', help='inf: infinite liquidation price if collateral going to 0 does not liquidate the position.')

    # max borrow amount
    with colc:
        max_borrow = max_borrow_amount(df,selected_network,st.session_state['collaterals'],selected_borrow,emodes[selected_emode])
        st.metric(label='Max Borrow Amount', value=pretty_number(max_borrow), help='The max borrowable amount is based on the max LTV rather than the liquidation threshold, creating a buffer betweet it and the amount at inmediate liquidation.')

# app
if __name__ == '__main__':
    home()
