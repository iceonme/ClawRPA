#!/usr/bin/env node
// bridge.js v1.2 — 修复命令队列混串 bug（移除 fallback）
const PORT = process.argv[2] || 18900;
const { createServer } = require('http');

let commands = {};
let results = {};

function ts() { return new Date().toISOString().slice(11,19); }

const server = createServer((req, res) => {
  res.setHeader('Content-Type', 'application/json');
  
  if (req.method === 'POST' && req.url.startsWith('/rpa/')) {
    let body = '';
    req.on('data', c => body += c);
    req.on('end', () => {
      try { body = JSON.parse(body); } catch {}
      const action = req.url.replace('/rpa/', '');
      const id = Date.now().toString(36);
      const target = (typeof body === 'object' ? body.target : null) || '15000952727';
      if (!commands[target]) commands[target] = [];
      commands[target].push({ id, action, ...(typeof body === 'object' ? body : {}) });
      console.log('[' + ts() + '] 📤 ' + action + ' → ' + target + ' (id=' + id + ')');
      let tries = 0;
      const check = setInterval(() => {
        if (results[id]) {
          clearInterval(check);
          console.log('[' + ts() + '] ✅ ' + target + ' 回传 ok=' + results[id].ok);
          res.end(JSON.stringify(results[id]));
          delete results[id];
        } else if (++tries > 40) {
          clearInterval(check);
          console.log('[' + ts() + '] ❌ ' + target + ' 超时');
          res.end(JSON.stringify({ ok: false, error: 'timeout' }));
        }
      }, 500);
    });
    return;
  }

  if (req.method === 'GET' && req.url.startsWith('/poll')) {
    const name = new URL(req.url, 'http://x').searchParams.get('name') || '15000952727';
    if (commands[name] && commands[name].length > 0) {
      const cmd = commands[name].shift();
      console.log('[' + ts() + '] 📥 ' + name + ' 取走: ' + cmd.action);
      return res.end(JSON.stringify(cmd));
    }
    return res.end(JSON.stringify(null));
  }

  if (req.method === 'POST' && req.url.startsWith('/result')) {
    let body = '';
    req.on('data', c => body += c);
    req.on('end', () => {
      try { body = JSON.parse(body); } catch {}
      console.log('[' + ts() + '] 📨 ' + body.id + ' ok=' + body.ok);
      results[body.id] = body;
      res.end(JSON.stringify({ ok: true }));
    });
    return;
  }

  res.end(JSON.stringify({ ok: false }));
});

server.listen(PORT, () => {
  console.log('[' + ts() + '] 🌉 桥接 v1.2 → :' + PORT);
});
