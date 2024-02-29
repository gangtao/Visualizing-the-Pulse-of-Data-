Reveal.initialize({
  hash: true,
  plugins: [RevealMarkdown, RevealHighlight, RevealNotes]
});

let stopReading = false;
// Event handler for the stop button
function stopReadingHandler() {
  stopReading = true;
}

// Create a new ReadableStream and consume it
async function consumeStream(response, callback, cleanup) {
  const reader = response.body.getReader();
  stopReading = false;
  let partialLine = '';
  let data = [];

  while (!stopReading) {
    const { done, value } = await reader.read();
    if (done) {
      if (partialLine) {
        console.log("Received partial line:", partialLine);
      }
      console.log("Stream complete");
      break;
    }

    // Combine the previous partial line with the new chunk
    const chunk = partialLine + new TextDecoder().decode(value);
    // Split the combined chunk by lines
    const lines = chunk.split('\n');

    // Process all lines except the last one
    for (let i = 0; i < lines.length - 1; i++) {
      const datum = JSON.parse(lines[i]);
      data = [...data, datum]
      // TODO : should control the callback in a batch instead of call it on every data
      // TODO : callback to sperate first call and the rest, first call used for metadata handling
      callback(data);
    }

    // Update partialLine with the last chunk which may be incomplete
    partialLine = lines[lines.length - 1];
  };

  cleanup();
};

async function processData(data) {
  const renderData = data.reverse();
  const s2Options = {
    width: 600,
    height: 600
  };
  const colums = Object.keys(data[0]);
  const meta = colums.map( (f) => {
    return {
      field: f,
      name: f,
    }; 
  });
  const s2DataConfig = {
    fields: {
      columns: colums,
    },
    meta: meta,
    data: renderData,
  };
  const container = document.getElementById('container2');
  const s2 = new S2.TableSheet(container, s2DataConfig, s2Options);
  await s2.render();

  return function(){
    s2.destroy();
  }
}

// Make the HTTP POST request
async function fetchStream(url, data, renderFunc) {
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
  // Consume the response stream
  await consumeStream(response, renderFunc);
}

async function renderStream(sql, renderFunc) {
  // fetch stream data
  const url = 'http://localhost:5001/queries';
  const data = { sql: sql };

  await fetchStream(url, data, renderFunc)
    .then(() => console.log("Stream processing complete"))
    .catch(error => console.error("Error fetching stream:", error));
}

const code1 = `const data = [
    { genre: 'Sports', sold: 275 },
    { genre: 'Strategy', sold: 115 },
    { genre: 'Action', sold: 120 },
    { genre: 'Shooter', sold: 350 },
    { genre: 'Other', sold: 150 },
];

const chart = new G2.Chart({
    container: 'container1',
    theme: 'dark',
});

chart
    .interval()
    .data(data)
    .encode('x', 'genre') 
    .encode('y', 'sold'); 

chart.render();
`;

const code2 = `renderStream("select * from car_live_data limit 100", processData)`;

function codeDemo(codeContainerId, code) {
  var editor = monaco.editor.create(document.getElementById(codeContainerId), {
    minimap: {
      enabled: false,
    },
    value: code,
    language: 'javascript',
    theme: 'vs-dark',
  });
  editor.onDidChangeModelContent(function (e) {
    stopReadingHandler();
    eval(editor.getValue());
  });
  eval(code);
}

require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.26.1/min/vs' } });
require(["vs/editor/editor.main"], () => {
  codeDemo("code1", code1);
  codeDemo("code2", code2);
  //renderStream("select * from car_live_data", processData)
});








