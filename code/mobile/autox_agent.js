// autox_agent.js — 手机端 AutoX.js HTTP 轮询代理
// 导入到 AutoX.js → 运行

var BRIDGE = "http://192.168.1.61:18900";
var NAME = "phone-1";

console.log("连接桥接服务: " + BRIDGE);

var polling = false;

function poll() {
  if (polling) return;
  polling = true;
  threads.start(function () {
    while (true) {
      try {
        var r = http.get(BRIDGE + "/poll?name=" + NAME);
        if (r.statusCode == 200) {
          var msg = r.body.json();
          if (msg) {
            console.log("收到指令: " + JSON.stringify(msg));
            try {
              var result = handleAction(msg.action, msg);
              sendResult(msg.id, true, result);
            } catch (e) {
              sendResult(msg.id, false, e.message);
            }
          }
        }
      } catch (e) {
        console.error("轮询失败: " + e);
      }
      sleep(500);
    }
  });
}

function sendResult(id, ok, data) {
  try {
    http.postJson(BRIDGE + "/result", {
      id: id, ok: ok, data: data || (ok ? "ok" : "error")
    });
  } catch (e) {
    console.error("回传失败: " + e);
  }
}

function handleAction(action, params) {
  switch (action) {
    case "launch":
      var pkg = params.pkg || params;
      app.launch(pkg);
      sleep(2000);
      return "打开 " + pkg;
    case "click":
      var text = params.text || params;
      var s = text.length <= 2 ? textContains(text) : text(text);
      var node = s.findOne(3000);
      if (!node) throw new Error("未找到: " + text);
      node.click();
      sleep(500);
      return "点击 " + text;
    case "click_xy":
      click(params.x, params.y);
      sleep(300);
      return "点击 " + params.x + "," + params.y;
    case "screenshot":
      var img = captureScreen();
      return images.toBase64(img);
    case "eval":
      return eval(params.js || params);
    case "input":
      setText(params.text || params);
      return "ok";
    case "back":
      back();
      sleep(300);
      return "ok";
    default:
      throw new Error("未知: " + action);
  }
}

requestScreenCapture(false);
device.keepScreenOn(3600 * 1000);
toast("Agent 已启动");
console.log("AutoX.js Agent 已启动，开始轮询...");
poll();
