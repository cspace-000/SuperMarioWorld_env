import numpy as np
import gym
from gym import spaces
import socket, json
import time
import argparse, os
import random
from collections import deque, OrderedDict
from stable_baselines.common.env_checker import check_env
#from stable_baselines.common.policies import MlpPolicy
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines.common.callbacks import CheckpointCallback
from stable_baselines.common import make_vec_env
from stable_baselines import PPO2
from stable_baselines import DQN
import pdb
##v1 redoing socket to open close for each step.

class MarioEnv(gym.Env):
	def __init__(self):
		super(MarioEnv, self).__init__()
		
		n_actions = 4
		self.HOST='127.0.0.1'
		self.PORT=65432
		self.state_size = 169

		self.action_space = spaces.Discrete(n_actions)
		self.observation_space = spaces.Box(low=-1, high=1, shape=(self.state_size,), dtype=np.float32)
		#print(self.observation_space)
		# self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# self.sock.bind((self.HOST,self.PORT))
		# self.sock.listen(1)

		# print('listening for client: HOST:{}, PORT:{}'.format(self.HOST, self.PORT))
		# self.conn, self.addr = self.sock.accept()

		# print('connected at: {}'.format(self.addr))
		# self.sock.close()

	def step(self, action):
		prev_data_chunk = ''
		#print('here')
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.bind((self.HOST,self.PORT))
		sock.listen(1)		
		conn, addr = sock.accept()		

		#print('here2')
		self.toClient(action, conn)
		#print('sent')
		#print('here3')
		#pdb.set_trace()
		msg = conn.recv(400)
		if not msg:
			print('no client msg')
			pass
				
		else:	
			next_state, reward, done, score, curr_data_chunk, recv_action = self.fromClient(msg, prev_data_chunk)
			next_state = np.array(next_state).astype(np.float32)
			#print(next_state)
			#print(next_state.shape)
		#next_state = np.reshape(next_state, [1, state_size])
		sock.close()
		return next_state, reward, done, {}  


	def reset(self):
		state = np.zeros(self.state_size)
		#state = np.reshape(state, [1, self.state_size])
		return state

	def render(self, mode='human'):
		pass

	def close(self):
		pass


	def fromClient(self, msgx, prev_data_chunk):
	    #print(msgx)
	    msg_dec = msgx.decode()
	    msg_dec = prev_data_chunk + msg_dec
	    deliminator_start = msg_dec.find('S')
	    deliminator_end = msg_dec.find('E')
	    msg_length = len(msg_dec)

	    msg = msg_dec[deliminator_start+4:deliminator_end-3]

	    if deliminator_end < msg_length-4:

	        curr_data_chunk=msg_dec[deliminator_end+5:]
      
	    else:
	        curr_data_chunk = ''
	    data = json.loads(msg)

	    state = data[0]

	    reward = data[1]
	    done = data[2]
	    score = data[3]
	    action = data[4]
	    return state, reward, done, score, curr_data_chunk, action	


	def toClient(self, action, conn):
	    #action = no. from 0-8
	    act_dict = self.Controller(action)
	    act_dict = json.dumps(act_dict)
	    act_dict = act_dict + '\n'
	    act_dict = act_dict.encode()
	    #print('sent :',ss)
	    conn.sendall(act_dict)



	def Controller(self, action): #controller output
	    #lua output{'A': False, 'Up': False, 'Select': False, 'Right': False, 'Left': False, 'Y': False, 'X': False, 'R': False, 'Start': False, 'L': False, 'Down': False, 'B': False}
	    #print("here")
	    #actions_list = ["A", "Up", "Select", "Right", "Left", "Y", "X", "R", "Start", "L", "Down", "B"]
	    controller = {"P1 A":False, "P1 Up":False, "P1 Right":False, "P1 Left":False, "P1 Y":True, "P1 X":False, "P1 Down":False, "P1 B":False}
	    actions_list = ["A", "Right", "Left", "B"]
	    controller_no = "P1 "
	    controllerdictkey = controller_no + actions_list[action] #P1 + actionlist no.
	    controller[controllerdictkey] = True
	    return controller 


# env = MarioEnv()
# check_env(env, warn=True)
# print("RUNNING!")
# checkpoint_callback = CheckpointCallback(save_freq=2500, save_path='./logs/',
#                                          name_prefix='rl_model')

# # model = PPO2(MlpPolicy, env, verbose=1, 
# # 			gamma=GAMMA,
# # 			learning_rate= learning_rate,
# # 			lam=LAMBDA,
# # 			nminibatches=batch_size,
# # 			tensorboard_log="./5_23/"
# # 			)
# gamma = 0.9    # discount rate
# #self.epsilon_decay = 0.99
# learning_rate = 0.00025
# target_network_update_freq = 1000
# #import pdb
# #pdb.set_trace()

# model = DQN(MlpPolicy, env, verbose=1,
# 			learning_rate = learning_rate,
# 			target_network_update_freq = target_network_update_freq,
# 			gamma=gamma,
# 			tensorboard_log="./tensorlog6_16/"
# 			)


# model.learn(total_timesteps=int(1e5),
# 			callback=checkpoint_callback)

# print('done simulation')