Reveal.initialize({
  hash: true,
  plugins: [RevealMarkdown, RevealHighlight, RevealNotes]
});


const code = `const data = [
    { genre: 'Sports', sold: 275 },
    { genre: 'Strategy', sold: 115 },
    { genre: 'Action', sold: 120 },
    { genre: 'Shooter', sold: 350 },
    { genre: 'Other', sold: 150 },
];

const chart = new G2.Chart({
    container: 'container',
    theme: 'dark',
});

chart
    .interval()
    .data(data)
    .encode('x', 'genre') 
    .encode('y', 'sold'); 

chart.render();
`;

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
  codeDemo("code", code);
});








