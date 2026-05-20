// autox_agent.js v1.5 — 截图初始化只做一次
// 手机: DT1901A (15000952727)
var BRIDGE = "http://192.168.1.61:18900";
var NAME = "15000952727";
var count = 0;
var screenReady = false;

toast("Agent v1.5 启动");

// 初始化截图（只做一次）
try {
  requestScreenCapture(false);
  screenReady = true;
  toast("截图就绪");
} catch(e) {
  toast("截图失败: " + e.message);
}

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
          var result;
          if (msg.action == "launch") { app.launch(msg.pkg || msg); sleep(2000); result = "ok"; }
          else if (msg.action == "click") {
            var t = msg.text || msg;
            var n = (t.length <= 2 ? textContains(t) : text(t)).findOne(3000);
            if (!n) throw new Error("未找到: " + t);
            n.click(); sleep(500); result = "ok";
          }
          else if (msg.action == "click_xy") { click(msg.x, msg.y); sleep(300); result = "ok"; }
          else if (msg.action == "screenshot") {
            if (!screenReady) throw new Error("截图未就绪");
            sleep(300);
            var img = captureScreen();
            sleep(300);
            result = images.toBase64(img);
          }
          else if (msg.action == "eval") { result = eval(msg.js || msg); }
          else if (msg.action == "back") { back(); sleep(300); result = "ok"; }
          else { throw new Error("未知: " + msg.action); }
          http.postJson(BRIDGE + "/result", {id: msg.id, ok: true, data: result});
        } catch (e) {
          try { http.postJson(BRIDGE + "/result", {id: msg.id, ok: false, data: e.message}); } catch(e2){}
        }
      }
    }
  } catch (e) {}
}

setInterval(poll, 500);
