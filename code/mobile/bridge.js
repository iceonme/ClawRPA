#!/usr/bin/env node
// bridge.js — TIXClaw 真机桥接服务（HTTP 轮询版）
// 用法：node bridge.js [端口]

const PORT = process.argv[2] || 18900;
const { createServer } = require('http');

let commands = {};  // name → { id, action, ...params }
let results = {};   // id → result

const server = createServer((req, res) => {
  res.setHeader('Content-Type', 'application/json');
  
  // TIXClaw → 桥 → 手机（发指令）
  if (req.method === 'POST' && req.url.startsWith('/rpa/')) {
    let body = '';
    req.on('data', c => body += c);
    req.on('end', () => {
      try { body = JSON.parse(body); } catch {}
      const action = req.url.replace('/rpa/', '');
      const id = Date.now().toString(36);
      const target = (typeof body === 'object' ? body.target : null) || 'phone-1';
      if (!commands[target]) commands[target] = [];
      commands[target].push({ id, action, ...(typeof body === 'object' ? body : {}) });
      // 等结果
      let tries = 0;
      const check = setInterval(() => {
        if (results[id]) {
          clearInterval(check);
          res.end(JSON.stringify(results[id]));
          delete results[id];
        } else if (++tries > 40) {
          clearInterval(check);
          res.end(JSON.stringify({ ok: false, error: 'timeout' }));
        }
      }, 500);
    });
    return;
  }

  // 手机 → 桥：轮询取指令
  if (req.method === 'GET' && req.url.startsWith('/poll')) {
    const name = new URL(req.url, 'http://x').searchParams.get('name') || 'phone-1';
    if (commands[name] && commands[name].length > 0) {
      const cmd = commands[name].shift();
      return res.end(JSON.stringify(cmd));
    }
    return res.end(JSON.stringify(null));
  }

  // 手机 → 桥：回传结果
  if (req.method === 'POST' && req.url.startsWith('/result')) {
    let body = '';
    req.on('data', c => body += c);
    req.on('end', () => {
      try { body = JSON.parse(body); } catch {}
      results[body.id] = body;
      res.end(JSON.stringify({ ok: true }));
    });
    return;
  }

  res.end(JSON.stringify({ ok: false }));
});

server.listen(PORT, () => {
  console.log(`🌉 桥接(HTTP)运行中 → http://localhost:${PORT}`);
  console.log(`   手机轮询 → GET /poll?name=phone-1`);
});
