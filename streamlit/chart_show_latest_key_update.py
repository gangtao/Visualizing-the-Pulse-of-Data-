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
  longitude != 0 and latitude != 0
'''

rows = c.execute_iter(query, with_column_types=True)
header = next(rows)
first_row = next(rows)
columns = [f[0] for f in header]
df = pd.DataFrame([list(first_row)], columns=columns)

# add_rows not working with map
# chart = st.map(df,
#                 latitude='latitude',
#                 longitude='longitude',
#                 size='speed_kmh',
#                 zoom=12)

chart = st.table(df)

start_time = datetime.now()
new_rows = []
for row in rows:
    new_rows.append(list(row))
    current_time = datetime.now()
    time_diff = current_time - start_time
    # render every 1 second
    if time_diff.total_seconds() > 1:
        new_row_df = pd.DataFrame(new_rows, columns=columns)
        # st.write(new_row_df)
        chart.add_rows(new_row_df)
        new_rows = []
