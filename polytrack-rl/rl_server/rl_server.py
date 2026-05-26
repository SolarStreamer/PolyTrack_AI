import asyncio
import json
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import websockets
from collections import deque, namedtuple

STATE_SIZE = 10
ACTION_SIZE = 3
GAMMA = 0.99
LR = 1e-3
BATCH_SIZE = 64
REPLAY_SIZE = 50000
MIN_REPLAY = 1000
EPS_START = 1.0
EPS_END = 0.05
EPS_DECAY = 100000

Transition = namedtuple("Transition", ("state", "action", "reward", "next_state", "done"))

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class DQN(nn.Module):
    def __init__(self, state_size, action_size):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_size, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, action_size)
        )

    def forward(self, x):
        return self.net(x)

policy_net = DQN(STATE_SIZE, ACTION_SIZE).to(device)
target_net = DQN(STATE_SIZE, ACTION_SIZE).to(device)
target_net.load_state_dict(policy_net.state_dict())
target_net.eval()

optimizer = optim.Adam(policy_net.parameters(), lr=LR)
replay_buffer = deque(maxlen=REPLAY_SIZE)
steps_done = 0

def build_state_vector(js_state):
    lane = js_state.get("playerLane", 1)
    speed = js_state.get("speed", 0.0)
    distance = js_state.get("distance", 0.0)
    score = js_state.get("score", 0.0)
    is_dead = 1.0 if js_state.get("isDead", False) else 0.0

    obstacles = js_state.get("obstacles", [])[:3]
    obs_features = []
    for i in range(3):
        if i < len(obstacles):
            obs_features.append(obstacles[i].get("lane", 1))
            obs_features.append(obstacles[i].get("distance", 0.0))
        else:
            obs_features.append(1)
            obs_features.append(999.0)

    vec = np.array(
        [lane, speed, distance, score, is_dead] + obs_features,
        dtype=np.float32
    )

    if len(vec) > STATE_SIZE:
        vec = vec[:STATE_SIZE]
    elif len(vec) < STATE_SIZE:
        vec = np.concatenate([vec, np.zeros(STATE_SIZE - len(vec))])

    return vec

def select_action(state_vec):
    global steps_done
    eps = EPS_END + (EPS_START - EPS_END) * np.exp(-steps_done / EPS_DECAY)
    steps_done += 1

    if random.random() < eps:
        return random.randrange(ACTION_SIZE)

    with torch.no_grad():
        state_t = torch.tensor(state_vec, device=device).unsqueeze(0)
        q_values = policy_net(state_t)
        return int(q_values.argmax().item())

def compute_reward(prev, curr):
    if prev is None:
        return 0.0

    reward = 1.0
    reward += 0.1 * (curr.get("score", 0) - prev.get("score", 0))

    if curr.get("isDead", False):
        reward -= 10.0

    return reward

def optimize_model():
    if len(replay_buffer) < MIN_REPLAY:
        return

    batch = random.sample(replay_buffer, BATCH_SIZE)
    batch = Transition(*zip(*batch))

    state_batch = torch.tensor(np.stack(batch.state), device=device)
    action_batch = torch.tensor(batch.action, device=device).unsqueeze(1)
    reward_batch = torch.tensor(batch.reward, device=device)
    next_batch = torch.tensor(np.stack(batch.next_state), device=device)
    done_batch = torch.tensor(batch.done, device=device, dtype=torch.float32)

    q_values = policy_net(state_batch).gather(1, action_batch).squeeze(1)

    with torch.no_grad():
