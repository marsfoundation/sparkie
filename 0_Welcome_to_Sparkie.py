import streamlit as st

st.set_page_config(
    page_title='Sparkie',
    page_icon='spark_logo.svg',
    layout='wide',
    initial_sidebar_state='expanded'
)

def app():
    st.title('⚡️ Welcome to Sparkie ⚡️')
    st.write('Sparkie is a companion app or set of tools to help you use Spark.')

    st.write('''
             #### SparkLend Simulator 
                - Calculate your liquidation price even with multiple collaterals
             #### sDAI Calculator
                - Calculate your effective return even if you've deposited, transfered and withdrawn multiple times
             ''')
    
    st.write("")
    st.write('Made by Phoenix Labs with data from BlockAnalitica')

    
if __name__ == "__main__":
    app()