let ws = null;
let isConnected = false;
let contentPort = null;

function connectWebSocket() {
  if (ws && isConnected) return;

  ws = new WebSocket("ws://localhost:8765");

  ws.onopen = () => {
    isConnected = true;
    console.log("Connected to RL server");
  };

ws.onclose = () => {
    isConnected = false;
    console.log("Disconnected from RL server");
    setTimeout(connectWebSocket, 2000);
  };

  ws.onmessage = (event) => {
    if (contentPort) {
      contentPort.postMessage({
        type: "ACTION_FROM_SERVER",
        data: event.data
      });
    }
  };
}

chrome.runtime.onConnect.addListener((port) => {
  if (port.name === "polytrack-content") {
    contentPort = port;

    port.onMessage.addListener((msg) => {
      if (msg.type === "STATE_TO_SERVER" && isConnected) {
        ws.send(JSON.stringify(msg.data));
      }
    });

    port.onDisconnect.addListener(() => {
      contentPort = null;
    });
  }
});

connectWebSocket();
