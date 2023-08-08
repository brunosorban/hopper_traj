import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import random
from replay_buffer import ReplayBuffer
import rocket



def DeepQNetwork(lr, num_actions, input_dims, fc1, fc2):
    q_net = tf.keras.Sequential([
        tf.keras.layers.Dense(fc1, input_shape=(input_dims,), activation='relu'),
        tf.keras.layers.Dense(fc2, activation='relu'),
        tf.keras.layers.Dense(num_actions, activation=None)
    ])

    # Create an Adam optimizer with the specified learning rate
    optimizer = tf.keras.optimizers.Adam(learning_rate=lr)

    # Compile the model with the specified optimizer and loss function
    q_net.compile(optimizer=optimizer, loss='mse')

    return q_net


class Agent:
    def __init__(self, lr, discount_factor, num_actions, epsilon, batch_size, input_dims):
        self.action_space = [i for i in range(num_actions)]
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.batch_size = batch_size
        self.epsilon_decay = 0.0005
        self.epsilon_final = 0.01
        self.update_rate = 1000
        self.step_counter = 0
        # Initialize replay buffer
        self.buffer = ReplayBuffer(1000000, input_dims)
        # Initialize policy Network
        self.q_net = DeepQNetwork(lr, num_actions, input_dims, 64, 64)
        # Initialize target Network with same parameters as policy Network
        self.q_target_net = DeepQNetwork(lr, num_actions, input_dims, 64, 64)

    def store_tuple(self, state, action, reward, new_state, done):
        self.buffer.store_tuples(state, action, reward, new_state, done)

    def policy(self, observation):
        if np.random.random() < self.epsilon:
            action = np.random.choice(self.action_space)
            # action = random.random()  # Returns a random valve position between 0 and 1
        else:
            state = np.array([observation])
            actions = self.q_net(state)  # Get the set of Q-Values for each action
            # action = actions.numpy()[0][0]
            action = tf.math.argmax(actions, axis=1).numpy()[0]

        return action

    def train(self):
        if self.buffer.counter < self.batch_size:
            return
        if self.step_counter % self.update_rate == 0:
            self.q_target_net.set_weights(self.q_net.get_weights())

        state_batch, action_batch, reward_batch, new_state_batch, done_batch = \
            self.buffer.sample_buffer(self.batch_size)

        q_predicted = self.q_net(state_batch)
        q_next = self.q_target_net(new_state_batch)
        q_max_next = tf.math.reduce_max(q_next, axis=1, keepdims=True).numpy()
        q_target = np.copy(q_predicted)

        for idx in range(done_batch.shape[0]):
            target_q_val = reward_batch[idx]
            if not done_batch[idx]:
                target_q_val += self.discount_factor*q_max_next[idx]
            q_target[idx, action_batch[idx]] = target_q_val
        self.q_net.train_on_batch(state_batch, q_target)
        self.epsilon = self.epsilon - self.epsilon_decay if self.epsilon > self.epsilon_final else self.epsilon_final
        self.step_counter += 1

    def train_model(self, env, num_episodes, graph):

        scores, episodes, avg_scores, obj = [], [], [], []
        goal = 200
        f = 0
        txt = open("saved_networks.txt", "w")

        for i in range(num_episodes):
            done = False
            score = 0.0
            state = env.reset()
            while not done:
                action = self.policy(state)
                new_state, reward, done = env.step(action, state)
                score += reward
                self.store_tuple(state, action, reward, new_state, done)
                # print(f"State: {new_state} Action: {action}  Reward: {reward} ")
                state = new_state
                self.train()
            scores.append(score)
            obj.append(goal)
            episodes.append(i)
            avg_score = np.mean(scores[-100:])
            avg_scores.append(avg_score)
            print("Episode {0}/{1}, Score: {2} ({3}), AVG Score: {4}".format(i, num_episodes, score, self.epsilon,
                                                                             avg_score))
            if avg_score >= 0.0 and score >= 0.0:
                self.q_net.save(("saved_networks/dqn_model{0}".format(f)))
                self.q_net.save_weights(("saved_networks/dqn_model{0}/net_weights{0}.h5".format(f)))
                txt.write("Save {0} - Episode {1}/{2}, Score: {3} ({4}), AVG Score: {5}\n".format(f, i, num_episodes,
                                                                                                  score, self.epsilon,
                                                                                                  avg_score))
                f += 1
                print("Network saved")

        txt.close()
        if graph:
            df = pd.DataFrame({'x': episodes, 'Score': scores, 'Average Score': avg_scores, 'Solved Requirement': obj})

            plt.plot('x', 'Score', data=df, marker='', color='blue', linewidth=2, label='Score')
            plt.plot('x', 'Average Score', data=df, marker='', color='orange', linewidth=2, linestyle='dashed',
                     label='AverageScore')
            plt.plot('x', 'Solved Requirement', data=df, marker='', color='red', linewidth=2, linestyle='dashed',
                     label='Solved Requirement')
            plt.legend()
            plt.savefig('Hopper1D_Train.png')

    def test(self, env, num_episodes, file_type, file, graph):
        if file_type == 'tf':
            self.q_net = tf.keras.models.load_model(file)
        elif file_type == 'h5':
            self.train_model(env, 5, False)
            self.q_net.load_weights(file)
        self.epsilon = 0.0
        scores, episodes, avg_scores, obj = [], [], [], []
        goal = 0
        score = 0.0
        for i in range(num_episodes):
            state = env.reset()
            done = False
            episode_score = 0.0
            S1 = []
            S2 = []
            while not done:
                # env.render()
                action = self.policy(state)
                new_state, reward, done = env.step(action, state)

                # print(f"State: {new_state} Action: {action}  Reward: {reward} ")

                S1.append(new_state[0])
                S2.append(new_state[1])

                episode_score += reward
                state = new_state
            score += episode_score
            scores.append(episode_score)
            obj.append(goal)
            episodes.append(i)
            avg_score = np.mean(scores[-100:])
            avg_scores.append(avg_score)

            print("Episode {0}/{1}, Score: {2} ({3}), AVG Score: {4}".format(i, num_episodes, episode_score, self.epsilon,
                                                                             avg_score))

            if i % 10 == 0:
                plt.plot(np.linspace(0, rocket.HopperEnv.duration, np.size(S1)), S1)
        plt.savefig('TestRuns.png')
        plt.close()
        if graph:
            df = pd.DataFrame({'x': episodes, 'Score': scores, 'Average Score': avg_scores, 'Solved Requirement': obj})

            plt.plot('x', 'Score', data=df, marker='', color='blue', linewidth=2, label='Score')
            plt.plot('x', 'Average Score', data=df, marker='', color='orange', linewidth=2, linestyle='dashed',
                     label='AverageScore')
            plt.plot('x', 'Solved Requirement', data=df, marker='', color='red', linewidth=2, linestyle='dashed',
                     label='Solved Requirement')
            plt.legend()
            plt.savefig('Hopper1D_Test.png')


