import streamlit as st

st.set_page_config(
    page_title='Sparkie',
    page_icon='spark_logo.svg',
    layout='wide',
    initial_sidebar_state='expanded'
)

def app():
    st.title('⚡️ Welcome to Sparkie ⚡️')
    st.write('Sparkie is a companion set of tools to help you use SparkLend and sDAI.')

    st.write('''
             There are two tools available 
             - SparkLend Calculator: 
                - Calculate your health factor, liquidation price, and max borrowable amount
             - sDAI Calculator
                - Calculate your effective accrual and effective yield for sDAI
             ''')
    
    st.write("")
    st.write('Made by Phoenix Labs with data from BlockAnalitica')

    
if __name__ == "__main__":
    app()