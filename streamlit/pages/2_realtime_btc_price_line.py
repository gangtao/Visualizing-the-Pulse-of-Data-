import streamlit as st
import pandas as pd
import json
from proton_driver import client

c = client.Client(host='127.0.0.1', port=8463)
query = '''SELECT
  window_start, latest(price) AS price
FROM
  tumble(tickers, 1s)
WHERE
  (product_id = 'BTC-USD') AND (_tp_time > (now() - 2m))
GROUP BY
  window_start
'''

viz_config_json = '''{
    "mark": {"type": "line", "tooltip": true},
    "encoding": {
        "x": {"field": "window_start", "type": "quantitative", "timeUnit": "minutesseconds"},
        "y": {"field": "price", "type": "quantitative"}
    }
}'''

stopped = False
rows = c.execute_iter(query, with_column_types=True)
header = next(rows)
first_row = next(rows)
columns = [f[0] for f in header]
df = pd.DataFrame([list(first_row)], columns=columns)
if st.button("stop", type="primary"):
    stopped = True

viz_config = json.loads(viz_config_json)

with st.empty():
    try:
        for row in rows:
            if stopped:
                break
            data = list(row)
            new_row = pd.DataFrame([data], columns=columns)
            df = pd.concat([df, new_row], ignore_index=True)
            # convert decimal object to float
            df['price'] = df['price'].astype(float)
            max_price = df['price'].max()
            min_price = df['price'].min()
            scale = {"domain": [min_price, max_price]}
            viz_config['encoding']['y']['scale'] = scale
            st.vega_lite_chart(df, viz_config , use_container_width=True)
        c.disconnect()
    except Exception as e:
        print(f'failed to read {e}')
        c.disconnect()
