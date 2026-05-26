const startBtn = document.getElementById("start");
const stopBtn = document.getElementById("stop");
const statusDiv = document.getElementById("status");

function sendMessageToActiveTab(msg) {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) chrome.tabs.sendMessage(tabs[0].id, msg);
  });
}

startBtn.addEventListener("click", () => {
  sendMessageToActiveTab({ type: "START_AGENT" });
  statusDiv.textContent = "Status: running";
});

stopBtn.addEventListener("click", () => {
  sendMessageToActiveTab({ type: "STOP_AGENT" });
  statusDiv.textContent = "Status: stopped";
});
