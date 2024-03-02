import streamlit as st
import pandas as pd
import json
from proton_driver import client

c = client.Client(host='127.0.0.1', port=8463)
query = '''SELECT 
  cid, avg(speed_kmh) AS avg_speed, emit_version() as version
FROM 
  car_live_data
GROUP BY 
  cid
ORDER BY 
  avg_speed DESC
LIMIT 5 BY emit_version()
'''

viz_config = '''{
    "mark": {"type": "bar", "tooltip": true},
    "encoding": {
        "x": {"field": "avg_speed", "type": "quantitative"},
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
        latest_version = new_row.iloc[0]['version']
        df = pd.concat([df, new_row])
        filtered_df = df[df['version'] == latest_version]

        st.vega_lite_chart(filtered_df, json.loads(viz_config), use_container_width=True)
