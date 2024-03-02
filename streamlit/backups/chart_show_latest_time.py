import streamlit as st
import pandas as pd
import json
from proton_driver import client

c = client.Client(host='127.0.0.1', port=8463)
query = '''SELECT 
  window_start, cid, max(speed_kmh) AS max_speed
FROM 
  tumble(car_live_data, 1s)
GROUP BY 
  window_start, cid
ORDER BY 
  max_speed DESC
LIMIT 5 BY window_start
'''

viz_config = '''{
    "mark": {"type": "bar", "tooltip": true},
    "encoding": {
        "x": {"field": "max_speed", "type": "quantitative"},
        "y": {"field": "cid", "type": "ordinal", "sort": null}
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

        # only show latest time range
        latest_time = new_row.iloc[0]['window_start']
        df = pd.concat([df, new_row])
        filtered_df = df[df['window_start'] == latest_time]

        st.vega_lite_chart(filtered_df, json.loads(viz_config), use_container_width=True)
