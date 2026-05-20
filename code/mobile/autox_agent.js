// autox_agent.js v1.4 — 带心跳 + 增强容错
// 手机: DT1901A (15000952727)
var BRIDGE = "http://192.168.1.61:18900";
var NAME = "15000952727";
var count = 0;

toast("Agent v1.4 启动");

function poll() {
  count++;
  if (count % 10 == 0) toast("心跳 #" + count);
  try {
    var r = http.get(BRIDGE + "/poll?name=" + NAME);
    if (r.statusCode == 200) {
      var body = r.body.string();
      if (body != "null") {
        var msg = JSON.parse(body);
        toast("收到: " + msg.action);
        try { 
          var result = doAction(msg.action, msg);
          http.postJson(BRIDGE + "/result", {id: msg.id, ok: true, data: result});
        } catch (e) { 
          try { http.postJson(BRIDGE + "/result", {id: msg.id, ok: false, data: e.message}); } catch(e2){}
        }
      }
    }
  } catch (e) {
    // silent retry
  }
}

function doAction(action, p) {
  if (action == "launch") { app.launch(p.pkg || p); sleep(2000); return "ok"; }
  if (action == "click") {
    var t = p.text || p;
    var n = (t.length <= 2 ? textContains(t) : text(t)).findOne(3000);
    if (!n) throw new Error("未找到: " + t);
    n.click(); sleep(500); return "ok";
  }
  if (action == "click_xy") { click(p.x, p.y); sleep(300); return "ok"; }
  if (action == "screenshot") {
    requestScreenCapture(false);
    sleep(500);
    var img = captureScreen();
    sleep(300);
    return images.toBase64(img);
  }
  if (action == "eval") { return eval(p.js || p); }
  if (action == "back") { back(); sleep(300); return "ok"; }
  throw new Error("未知: " + action);
}

setInterval(poll, 500);
