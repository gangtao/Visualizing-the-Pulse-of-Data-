import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from proton_driver import client

c = client.Client(host='127.0.0.1', port=8463)
query = '''SELECT 
  cid, speed_kmh, longitude, latitude
FROM 
  car_live_data
WHERE
  longitude != 0 and latitude != 0 and cid in ('c00001', 'c00002', 'c00003', 'c00004', 'c00005')
'''

rows = c.execute_iter(query, with_column_types=True)
header = next(rows)
first_row = next(rows)
columns = [f[0] for f in header]
df = pd.DataFrame([list(first_row)], columns=columns)
with st.empty():
    start_time = datetime.now()
    for row in rows:
        data = list(row)
        new_row = pd.DataFrame([data], columns=columns)
        df = pd.concat([df, new_row])

        result_df = df.groupby('cid').last().reset_index()

        current_time = datetime.now()
        time_diff = current_time - start_time
        # render every 1 second
        if time_diff.total_seconds()  > 3:
            st.map(result_df,
                latitude='latitude',
                longitude='longitude',
                size='speed_kmh',
                zoom=12)
            start_time = datetime.now()
