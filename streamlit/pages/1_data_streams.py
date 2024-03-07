import streamlit as st
import pandas as pd
from proton_driver import client

st.set_page_config(layout="wide")

c = client.Client(host='127.0.0.1', port=8463)
query = '''SELECT
  time, product_id, price, best_ask, best_ask_size, best_bid, best_bid_size
FROM
  tickers'''

rows = c.execute_iter(query, with_column_types=True)
header = next(rows)
first_row = next(rows)
columns = [f[0] for f in header]
df = pd.DataFrame([list(first_row)], columns=columns)

st.code(query, language='sql')

with st.empty():
    for row in rows:
        data = list(row)
        new_row = pd.DataFrame([data], columns=columns)
        df = pd.concat([df, new_row], ignore_index=True).tail(10)
        st.table(df)
