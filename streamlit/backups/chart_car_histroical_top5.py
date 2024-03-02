import streamlit as st
import pandas as pd
import json
from proton_driver import client

c = client.Client(host='127.0.0.1', port=8463)
query = '''SELECT 
  cid, max(speed_kmh) AS max_speed
FROM 
  table(car_live_data)
GROUP BY 
  cid
ORDER BY 
  max_speed DESC
LIMIT 5
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
        df = pd.concat([df, new_row])

    st.vega_lite_chart(df, json.loads(viz_config), use_container_width=True)
