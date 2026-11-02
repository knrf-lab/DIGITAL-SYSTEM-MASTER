// Build: concatenate src/*.html, include gen/*.html fragments, pre-render KaTeX, write dist/binder.html.
// Math: \( ... \) inline, \[ ... \] display.  Includes: {{inc:NAME}} -> gen/NAME.html
// Page refs: {{p:ID}} filled from dist/pages.json (written by stamp.py).
const fs = require('fs');
const path = require('path');
const katex = require('/projects/sandbox/.build/node_modules/katex');

const root = __dirname;
const srcDir = path.join(root, 'src');
const dist = path.join(root, 'dist');
fs.mkdirSync(dist, { recursive: true });

const files = fs.readdirSync(srcDir).filter(f => f.endsWith('.html')).sort();
let body = files.map(f => fs.readFileSync(path.join(srcDir, f), 'utf8')).join('\n');

let errors = 0;
body = body.replace(/\{\{inc:([A-Za-z0-9_-]+)\}\}/g, (_, n) => {
  const f = path.join(root, 'gen', n + '.html');
  if (!fs.existsSync(f)) { errors++; console.error('missing include', n); return `[MISSING ${n}]`; }
  return fs.readFileSync(f, 'utf8');
});
body = body.replace(/\{\{svg:([A-Za-z0-9_-]+)\}\}/g, (_, n) => {
  const f = path.join(root, 'svg', n + '.svg');
  if (!fs.existsSync(f)) { errors++; console.error('missing svg', n); return `[MISSING SVG ${n}]`; }
  return fs.readFileSync(f, 'utf8');
});

const render = (tex, display) => {
  tex = tex.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&').replace(/&nbsp;/g, ' ');
  try {
    return katex.renderToString(tex, { displayMode: display, throwOnError: true, strict: false });
  } catch (e) {
    errors++;
    console.error('KaTeX error:', e.message, '\n   in:', tex.slice(0, 120));
    return `<span style="color:red">[MATH ERROR: ${tex}]</span>`;
  }
};
body = body.replace(/\\\[([\s\S]+?)\\\]/g, (_, t) => render(t, true));
body = body.replace(/\\\(([\s\S]+?)\\\)/g, (_, t) => render(t, false));

const pagesFile = path.join(dist, 'pages.json');
const pages = fs.existsSync(pagesFile) ? JSON.parse(fs.readFileSync(pagesFile, 'utf8')) : {};
const missing = new Set();
body = body.replace(/\{\{p:([A-Za-z0-9_-]+)\}\}/g, (_, id) => {
  if (pages[id] === undefined) { missing.add(id); return '<span class="pref">p.&#8199;&#8199;</span>'; }
  return `<span class="pref">p.${pages[id]}</span>`;
});
body = body.replace(/<anchor id="([A-Za-z0-9_-]+)"\s*(?:label="([^"]*)")?\s*\/>/g,
  (_, id, label) => `<span class="anchor">@@${id}|${label || ''}@@</span>`);

const css = fs.readFileSync(path.join(root, 'style.css'), 'utf8');
const katexCss = 'file:///projects/sandbox/.build/node_modules/katex/dist/katex.min.css';
const html = `<!doctype html><html lang="id"><head><meta charset="utf-8">
<link rel="stylesheet" href="${katexCss}"><style>${css}</style></head><body>${body}</body></html>`;
fs.writeFileSync(path.join(dist, 'binder.html'), html);
console.log(`built ${files.length} files, errors: ${errors}, unresolved page refs: ${missing.size ? [...missing].join(',') : 0}`);
if (errors) process.exit(1);
