let running = false;
let port = chrome.runtime.connect({ name: "polytrack-content" });

function getGameState() {
  return window.polytrackState || null;
}

function sendStateToServer() {
  if (!running) return;

  const state = getGameState();
  if (!state) {
    requestAnimationFrame(sendStateToServer);
    return;
  }

  const rlState = {
    playerLane: state.playerLane,
    speed: state.speed,
    distance: state.distance,
    isDead: state.isDead,
    score: state.score,
    obstacles: state.obstacles.slice(0, 3)
  };

  port.postMessage({
    type: "STATE_TO_SERVER",
    data: rlState
  });

  requestAnimationFrame(sendStateToServer);
}

function pressKey(key) {
  document.dispatchEvent(new KeyboardEvent("keydown", { key }));
  document.dispatchEvent(new KeyboardEvent("keyup", { key }));
}

function applyAction(actionId) {
  if (actionId === 1) pressKey("ArrowLeft");
  if (actionId === 2) pressKey("ArrowRight");
}

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "START_AGENT") {
    running = true;
    requestAnimationFrame(sendStateToServer);
  }
  if (msg.type === "STOP_AGENT") running = false;
});

port.onMessage.addListener((msg) => {
  if (msg.type === "ACTION_FROM_SERVER") {
    applyAction(parseInt(msg.data, 10));
  }
});
