import streamlit as st
import pandas as pd
import json
from proton_driver import client

c = client.Client(host='127.0.0.1', port=8463)
query = '''SELECT
 window_start, product_id, earliest(price) AS open, max(price) AS high, min(price) AS low, latest(price) AS close
FROM
 tumble(tickers, 5s)
WHERE
 product_id = 'BTC-USD' and _tp_time > now() - 60s
GROUP BY
 window_start, product_id
'''

viz_config = '''{
   "encoding":{
      "x":{
        "field":"window_start",
        "type": "temporal",
        "title": "Time",
        "axis": {
            "format": "%H:%M:%S",
            "labelAngle": -45,
            "title": "Time"
        }
      },
      "y":{
         "type":"quantitative",
         "scale":{
            "zero":false
         },
         "axis":{
            "title":"Price"
         }
      },
      "color":{
         "condition":{
            "test":"datum.open < datum.close",
            "value":"#06982d"
         },
         "value":"#ae1325"
      }
   },
   "layer":[
      {
         "mark":"rule",
         "encoding":{
            "y":{
               "field":"low"
            },
            "y2":{
               "field":"high"
            }
         }
      },
      {
         "mark":"bar",
         "encoding":{
            "y":{
               "field":"open"
            },
            "y2":{
               "field":"close"
            }
         }
      }
   ]
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

        df['open'] = df['open'].astype('float64')
        df['high'] = df['high'].astype('float64')
        df['low'] = df['low'].astype('float64')
        df['close'] = df['close'].astype('float64')

        st.vega_lite_chart(df.tail(10), json.loads(viz_config), use_container_width=True)
        #st.table(df)
