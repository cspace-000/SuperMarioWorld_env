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
#from stable_baselines import DQN
from stable_baselines.common.vec_env import SubprocVecEnv
from stable_baselines.common import set_global_seeds, make_vec_env
import pdb
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import math

class MarioEnv(gym.Env):
	def __init__(self, showplot=False):
		super(MarioEnv, self).__init__()
		
		n_actions = 4
		self.HOST='127.0.0.1'
		self.PORT=65432
		self.state_size = 289
		self.action_space = spaces.Discrete(n_actions)
		self.observation_space = spaces.Box(low=-1, high=1, shape=(self.state_size,), dtype=np.float32)
		self.showplot = showplot
		self.fig, self.ax = plt.subplots()

	def step(self, action):
		prev_data_chunk = ''
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.bind((self.HOST,self.PORT))
		sock.listen(1)		
		conn, addr = sock.accept()		
		self.toClient(action, conn)
		msg = conn.recv(1024)
		
		if not msg:
			print('no client msg')
			pass
				
		else:	
			next_state, reward, done, score, curr_data_chunk, recv_action = self.fromClient(msg, prev_data_chunk)
			next_state = np.array(next_state).astype(np.float32)
			
		sock.close()

		if self.showplot==True:
			self.ax.cla()
			self.ax.set_axis_off()
			plotarray = self.update_plot(next_state)
			self.ax.imshow(plotarray)
			plt.pause(0.000000000001)	
		return next_state, reward, done, {}  


	def reset(self):
		state = np.zeros(self.state_size)
		return state

	def render(self, mode='human'):
		pass

	def update_plot(self, state):
		size = state.shape[0]
		size = int(math.sqrt(size))
		plotarray = state.reshape(size,size)
		return plotarray 	


	def close(self):
		pass


	def fromClient(self, msgx, prev_data_chunk):
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

	    try:
	    	data = json.loads(msg)
	    except JSONDecodeError:
	    	print(msg)

	    	
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
	    conn.sendall(act_dict)



	def Controller(self, action): #controller output
	    #lua output{'A': False, 'Up': False, 'Select': False, 'Right': False, 'Left': False, 'Y': False, 'X': False, 'R': False, 'Start': False, 'L': False, 'Down': False, 'B': False}
	    #actions_list = ["A", "Up", "Select", "Right", "Left", "Y", "X", "R", "Start", "L", "Down", "B"]
	    controller = {"P1 A":False, "P1 Up":False, "P1 Right":False, "P1 Left":False, "P1 Y":True, "P1 X":False, "P1 Down":False, "P1 B":False}
	    actions_list = ["A", "Right", "Left", "B"]
	    controller_no = "P1 "
	    controllerdictkey = controller_no + actions_list[action] #P1 + actionlist no.
	    controller[controllerdictkey] = True
	    return controller 
