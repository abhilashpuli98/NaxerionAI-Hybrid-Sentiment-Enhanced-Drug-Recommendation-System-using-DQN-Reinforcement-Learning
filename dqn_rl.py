"""Deep Q-Network Reinforcement Learning Module"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque
import random
from config import (DQN_STATE_SIZE, DQN_ACTION_SIZE, LEARNING_RATE_DQN, 
                    DISCOUNT_FACTOR, EPSILON, EPSILON_DECAY, EPSILON_MIN, MEMORY_SIZE, BATCH_SIZE_DQN)

class ExperienceReplay:
    """Experience replay memory for DQN"""
    def __init__(self, capacity=MEMORY_SIZE):
        self.capacity = capacity
        self.memory = deque(maxlen=capacity)
        
    def push(self, state, action, reward, next_state, done):
        """Store experience in memory"""
        self.memory.append((state, action, reward, next_state, done))
        
    def sample(self, batch_size):
        """Sample a batch of experiences"""
        batch = random.sample(self.memory, min(batch_size, len(self.memory)))
        
        states = np.array([exp[0] for exp in batch])
        actions = np.array([exp[1] for exp in batch])
        rewards = np.array([exp[2] for exp in batch])
        next_states = np.array([exp[3] for exp in batch])
        dones = np.array([exp[4] for exp in batch])
        
        return states, actions, rewards, next_states, dones
    
    def __len__(self):
        return len(self.memory)

class QNetwork(nn.Module):
    """Neural network for Q-value estimation"""
    def __init__(self, state_size=DQN_STATE_SIZE, action_size=DQN_ACTION_SIZE):
        super(QNetwork, self).__init__()
        self.fc1 = nn.Linear(state_size, 256)
        self.fc2 = nn.Linear(256, 256)
        self.fc3 = nn.Linear(256, 128)
        self.fc4 = nn.Linear(128, action_size)
        
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, state):
        """Forward pass"""
        x = self.relu(self.fc1(state))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.relu(self.fc3(x))
        x = self.fc4(x)
        return x

class DQNAgent:
    """Deep Q-Network Agent for drug recommendation"""
    def __init__(self, state_size=DQN_STATE_SIZE, action_size=DQN_ACTION_SIZE, 
                 device='cpu', learning_rate=LEARNING_RATE_DQN):
        self.state_size = state_size
        self.action_size = action_size
        self.device = device
        self.learning_rate = learning_rate
        
        # Q-networks
        self.q_network = QNetwork(state_size, action_size).to(device)
        self.target_network = QNetwork(state_size, action_size).to(device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        # Optimizer and loss
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        
        # Experience replay
        self.memory = ExperienceReplay()
        
        # Exploration-exploitation
        self.epsilon = EPSILON
        self.epsilon_decay = EPSILON_DECAY
        self.epsilon_min = EPSILON_MIN
        
        # Training metrics
        self.total_steps = 0
        self.episode_rewards = []
        
    def get_action(self, state, training=True):
        """
        Select action using epsilon-greedy policy
        
        Args:
            state: current state
            training: whether in training mode
        
        Returns:
            action: selected action
        """
        if training and np.random.random() < self.epsilon:
            return np.random.randint(0, self.action_size)
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.q_network(state_tensor)
        
        return q_values.argmax(dim=1).item()
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience in memory"""
        self.memory.push(state, action, reward, next_state, done)
    
    def replay(self, batch_size=BATCH_SIZE_DQN):
        """Train on a batch of experiences"""
        if len(self.memory) < batch_size:
            return 0
        
        states, actions, rewards, next_states, dones = self.memory.sample(batch_size)
        
        # Convert to tensors
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        # Q-value predictions
        q_values = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        
        # Target Q-values
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(dim=1)[0]
            target_q_values = rewards + (DISCOUNT_FACTOR * next_q_values * (1 - dones))
        
        # Loss and optimization
        loss = self.criterion(q_values, target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        return loss.item()
    
    def update_target_network(self):
        """Update target network weights"""
        self.target_network.load_state_dict(self.q_network.state_dict())
    
    def decay_epsilon(self):
        """Decay exploration rate"""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def train_episode(self, initial_state, max_steps=100, target_update_freq=10):
        """Train for one episode"""
        state = initial_state
        episode_reward = 0
        
        for step in range(max_steps):
            # Select and perform action
            action = self.get_action(state, training=True)
            
            # Simulate environment
            reward = self._compute_reward(action, state)
            next_state = self._get_next_state(state, action)
            done = step == max_steps - 1
            
            # Store experience
            self.remember(state, action, reward, next_state, done)
            
            # Train
            loss = self.replay()
            
            episode_reward += reward
            state = next_state
            
            if done:
                break
        
        # Decay epsilon
        self.decay_epsilon()
        
        # Update target network periodically
        self.total_steps += 1
        if self.total_steps % target_update_freq == 0:
            self.update_target_network()
        
        self.episode_rewards.append(episode_reward)
        return episode_reward
    
    def _compute_reward(self, action, state):
        """
        Compute reward based on multimodal sentiment state and selected drug action.

        State layout (first 6 elements used):
          [0] text_sentiment_score   (0–2, negative/neutral/positive)
          [1] text_confidence        (0–1)
          [2] audio_emotion_valence  (−1 to +1, negative→positive)
          [3] audio_confidence       (0–1)
          [4] image_validity_score   (0–2, invalid/uncertain/valid)
          [5] image_confidence       (0–1)

        Reward is higher when:
          - Patient sentiment is positive AND drug action matches well
          - High overall confidence across modalities
        """
        # Extract sentiment signals from state
        text_sent   = state[0] if len(state) > 0 else 1.0  # 0=neg, 1=neut, 2=pos
        text_conf   = state[1] if len(state) > 1 else 0.5
        audio_val   = state[2] if len(state) > 2 else 0.0  # -1 to +1
        audio_conf  = state[3] if len(state) > 3 else 0.5
        img_valid   = state[4] if len(state) > 4 else 1.0  # 0=invalid, 2=valid
        img_conf    = state[5] if len(state) > 5 else 0.5

        # Sentiment component: positive sentiment → higher reward
        sentiment_reward = (text_sent / 2.0) * text_conf  # 0 to 1

        # Audio component: positive valence → boost
        audio_reward = max(0, (audio_val + 1) / 2.0) * audio_conf  # 0 to 1

        # Image component: valid drug image → trust boost
        image_reward = (img_valid / 2.0) * img_conf  # 0 to 1

        # Drug action diversity bonus (encourage exploration)
        action_norm = action / max(self.action_size, 1)
        diversity_bonus = 0.1 * np.sin(action_norm * np.pi)

        # Composite reward
        reward = (0.4 * sentiment_reward +
                  0.25 * audio_reward +
                  0.25 * image_reward +
                  0.1 * diversity_bonus)

        # Scale to a reasonable range
        reward *= 10.0
        return reward

    def _get_next_state(self, state, action):
        """Compute next state: slight sentiment shift based on action quality."""
        next_state = state.copy()
        # Simulate small improvement in sentiment after drug recommendation
        next_state[0] = min(2.0, next_state[0] + 0.05)  # Marginal sentiment improvement
        # Small random perturbation to remaining state dimensions
        noise = np.random.normal(0, 0.02, len(next_state))
        noise[0] = 0  # Don't add noise to the deliberate sentiment shift
        next_state = next_state + noise
        return next_state
    
    def save_model(self, path):
        """Save model checkpoint"""
        torch.save({
            'q_network': self.q_network.state_dict(),
            'target_network': self.target_network.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, path)
    
    def load_model(self, path):
        """Load model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)
        self.q_network.load_state_dict(checkpoint['q_network'])
        self.target_network.load_state_dict(checkpoint['target_network'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']
    
    def get_training_stats(self):
        """Get training statistics"""
        if self.episode_rewards:
            avg_reward = np.mean(self.episode_rewards[-100:])
            max_reward = np.max(self.episode_rewards[-100:])
            return {
                'avg_reward': avg_reward,
                'max_reward': max_reward,
                'epsilon': self.epsilon,
                'total_episodes': len(self.episode_rewards)
            }
        return None
