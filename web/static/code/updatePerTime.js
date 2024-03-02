Reveal.initialize({
  hash: true,
  plugins: [RevealMarkdown, RevealHighlight, RevealNotes]
});

const max_data_point = 10000;

let subscription = null;
let chart = null;
let querySQL = null;
let editor = null;
let chartEditor = null;
let controller = null;
let signal = null;
let chartCode = null;

// Simulated asynchronous function to fetch stream data
async function consumeStream(response) {
  const reader = response.body.getReader();
  let partialLine = '';
  let data = [];

  return new rxjs.Observable(observer => {
    (async function readStream() {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            if (partialLine) {
              data = [JSON.parse(partialLine), ...data];
              observer.next(data);
            }
            observer.complete();
            break;
          }

          const chunk = partialLine + new TextDecoder().decode(value);
          const lines = chunk.split('\n');

          for (let i = 0; i < lines.length - 1; i++) {
            data = [...data, JSON.parse(lines[i])]; // new data at the end
            // limit the data size to 1000
            if (data.length > max_data_point) {
              data.splice(0, data.length - max_data_point);
            }
            observer.next(data);
          }
          partialLine = lines[lines.length - 1];
        }
      } catch (error) {
        observer.error(error);
      }
    })();
  });
}

function drawTable(data) {
  // time based merge
  const resultTimesMap = {};
  const timeField = "window_start";
  for (let i = 0; i< data.length ; i++) {
    const event = data[i];
    if (event[timeField] in resultTimesMap) {
      resultTimesMap[event[timeField]].push(event)
    } else {
      resultTimesMap[event[timeField]] = [event]
    }
  }
  let keysArray = Object.keys(resultTimesMap);
  let maxKey = keysArray.reduce((max, key) => (key > max ? key : max), keysArray[0]);
  const maxValue = resultTimesMap[maxKey];
  
  if (chart == null) {
    chart = new G2.Chart({
      container: 'container'
    });
    chart.theme({ type: 'classicDark' });
    eval(chartCode);
    chart.render();
  } else {
    chart.changeData(maxValue);
  }
}

// Function to process data
async function processData(data) {
  if (data) {
    drawTable(data);
  }
}

// Make the HTTP POST request and create an observable from the stream
async function fetchStreamObservable(sql) {
  const url = 'http://localhost:5001/queries';
  const data = { sql: sql };
  const response = await fetch(url, {
    method: 'POST',
    body: JSON.stringify(data),
    headers: {
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return consumeStream(response);
}

// Function to render stream data
async function renderStream(sql) {
  try {
    const observable = await fetchStreamObservable(sql);
    subscription = observable.subscribe(
      data => processData(data),
      error => console.error('Error fetching stream:', error),
      () => console.log('Stream processing complete')
    );
  } catch (error) {
    console.error('Error:', error);
  }
}

let code = `SELECT window_start,
count(*) as count, product_id 
FROM tumble(tickers, 1s)
GROUP by window_start, product_id
`;

chartCode = `chart
.interval()
.data(data)
.encode('x', 'product_id')
.encode('y', 'count')
.animate(false);
`;

let template = `sql = \`${code}\``;

function codeDemo() {
  editor = monaco.editor.create(document.getElementById("sqlCode"), {
    minimap: {
      enabled: false,
    },
    value: code,
    fontSize: 20,
    lineNumbers: "off",
    language: 'sql',
    theme: 'vs-dark',
    scrollBeyondLastLine: false,
  });

  chartEditor = monaco.editor.create(document.getElementById("chartCode"), {
    minimap: {
      enabled: false,
    },
    value: chartCode,
    fontSize: 20,
    lineNumbers: "off",
    language: 'javascript',
    theme: 'vs-dark',
    scrollBeyondLastLine: false,
  });
}

document.getElementById('runButton').addEventListener('click', function () {
  if (subscription != null){
    subscription.unsubscribe();
    controller.abort();
    chart = null;
  }

  code = editor.getValue();
  chartCode = chartEditor.getValue();
  template = `sql = \`${code}\``;
  eval(template);
  controller = new AbortController();
  signal = controller.signal;
  renderStream(sql);
});

document.getElementById('stopButton').addEventListener('click', function () {
  subscription.unsubscribe();
  controller.abort();
  chart = null;
});


require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.26.1/min/vs' } });
require(["vs/editor/editor.main"], () => {
  codeDemo();
});

