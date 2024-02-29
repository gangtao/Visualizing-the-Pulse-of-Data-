import streamlit as st
import pandas as pd
import json
from proton_driver import client

c = client.Client(host='127.0.0.1', port=8463)
query = '''SELECT
  product_id, max(price) AS max_price
FROM
  table(tickers)
GROUP BY
  product_id
ORDER BY
  max_price DESC
LIMIT 3
'''

viz_config = '''{
    "mark": {"type": "bar", "tooltip": true},
    "encoding": {
        "x": {"field": "max_price", "type": "quantitative"},
        "y": {"field": "product_id", "type": "ordinal", "sort": null}
    }
}'''

rows = c.execute_iter(query, with_column_types=True)
header = next(rows)
first_row = next(rows)
columns = [f[0] for f in header]
df = pd.DataFrame([list(first_row)], columns=columns)
with st.empty():
    for row in rows:
        data = list(row)
        new_row = pd.DataFrame([data], columns=columns)
        df = pd.concat([df, new_row])

    df['max_price'] = df['max_price'].astype('float64')
    st.vega_lite_chart(df, json.loads(viz_config), use_container_width=True)
