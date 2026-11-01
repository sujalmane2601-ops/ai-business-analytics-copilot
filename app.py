import streamlit as st

from copilot import ask, sanity_warnings

st.set_page_config(page_title='Business Analytics Copilot', layout='wide')
st.title('AI-Powered Business Analytics Copilot')
st.caption('Ask questions about the Online Retail II dataset (Dec 2009 - Dec 2011, GBP).')

EXAMPLES = ['What is the monthly revenue?',
            'Top 10 products by revenue',
            'Which countries outside the UK bring the most revenue?',
            'What is the return rate?']
cols = st.columns(len(EXAMPLES))
picked = None
for c, ex in zip(cols, EXAMPLES):
    if c.button(ex):
        picked = ex

question = st.text_input('Your question', value=picked or '')
if question:
    with st.spinner('Thinking...'):
        res = ask(question)
    if res['error']:
        st.error(f'Could not produce a valid query: {res["error"]}')
        st.code(res['sql'], language='sql')
    else:
        df = res['df']
        if res['summary']:
            st.subheader('Insight')
            st.write(res['summary'])
        left, right = st.columns([3, 2])
        with left:
            st.subheader('Result')
            st.dataframe(df)
            if df.shape[1] >= 2 and len(df) > 1:
                x, y = df.columns[0], df.columns[1]
                chart_df = df.set_index(x)[[y]]
                if 'month' in x.lower() or 'date' in x.lower():
                    st.line_chart(chart_df)
                else:
                    st.bar_chart(chart_df)
        with right:
            st.subheader('Generated SQL (verify me)')
            st.code(res['sql'], language='sql')
            st.caption(f'Attempts: {res["attempts"]} | Rows: {len(df)}')

        for w in sanity_warnings(df):
            st.warning(w)