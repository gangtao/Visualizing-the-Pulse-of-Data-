Reveal.initialize({
  hash: true,
  plugins: [RevealMarkdown, RevealHighlight, RevealNotes]
});

let subscription = null;

// Simulated asynchronous function to fetch stream data
async function consumeStream(response) {
  const reader = response.body.getReader();
  let partialLine = '';

  return new rxjs.Observable(observer => {
    (async function readStream() {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            if (partialLine) {
              observer.next(JSON.parse(partialLine));
            }
            observer.complete();
            break;
          }

          const chunk = partialLine + new TextDecoder().decode(value);
          const lines = chunk.split('\n');

          for (let i = 0; i < lines.length - 1; i++) {
            observer.next(JSON.parse(lines[i]));
          }
          partialLine = lines[lines.length - 1];
        }
      } catch (error) {
        observer.error(error);
      }
    })();
  });
}

// Function to process data
async function processData(data) {
  console.log(data);
  var element = document.getElementById('container');
  element.textContent =  JSON.stringify(data) + "\n" + element.textContent
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
  console.log("query : " + sql);
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

const code = `SELECT * FROM tickers`;
const template = `renderStream("${code}")`

function codeDemo(codeContainerId, code) {
  var editor = monaco.editor.create(document.getElementById(codeContainerId), {
    minimap: {
      enabled: false,
    },
    value: code,
    language: 'sql',
    theme: 'vs-dark',
  });
  editor.onDidChangeModelContent(function (e) {
    subscription.unsubscribe();
    eval(`renderStream("${editor.getValue()}")`);
  });
  eval(`renderStream("${code}")`);
}

require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.26.1/min/vs' } });
require(["vs/editor/editor.main"], () => {
  codeDemo("code", code);
});