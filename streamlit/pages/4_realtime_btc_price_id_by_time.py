import streamlit as st
import pandas as pd
import json
from proton_driver import client

c = client.Client(host='127.0.0.1', port=8463)
query = '''SELECT
  window_start, product_id, latest(price) AS price
FROM
  tumble(tickers, 1s)
GROUP BY
  window_start, product_id'''

viz_config_json = '''{
    "mark": {"type": "bar", "tooltip": true},
    "encoding": {
        "x": {"field": "price", "type": "quantitative"},
        "y": {"field": "product_id", "type": "ordinal", "sort": null}
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

            # only show latest time range
            latest_time = new_row.iloc[0]['window_start']
            df = pd.concat([df, new_row])
            result_df = df[df['window_start'] == latest_time]
            st.vega_lite_chart(result_df, viz_config , use_container_width=True)
        c.disconnect()
    except Exception as e:
        print(f'failed to read {e}')
        c.disconnect()
