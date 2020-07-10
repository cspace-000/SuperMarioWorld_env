import numpy as np
import gym
from gym import spaces
import socket, json
import time
import argparse, os
import random
from collections import deque, OrderedDict
from stable_baselines.common.env_checker import check_env
from stable_baselines.common.policies import MlpPolicy, MlpLstmPolicy
#from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines.common.callbacks import CheckpointCallback
from stable_baselines.common import make_vec_env
from stable_baselines import PPO2
from stable_baselines import DQN
import pdb
from mario_v0 import MarioEnv
from stable_baselines import results_plotter
from stable_baselines.bench import Monitor
from stable_baselines.results_plotter import load_results, ts2xy
from stable_baselines.common.noise import AdaptiveParamNoiseSpec, NormalActionNoise
from stable_baselines.common.callbacks import BaseCallback
from stable_baselines.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines.common.evaluation import evaluate_policy
import argparse

parser = argparse.ArgumentParser()
#parser.add_argument('-t', '--train', action='store_true', help='train neural network')
#required = parser.add_argument_group('required arguments')
parser.add_argument('-f', '--folder', type=str, help='run folder, saves model and outputs here')
parser.add_argument('-l', '--load', type=str, help='load neural network from given path')
parser.add_argument('-r', '--render', action='store_true', help='show the game')
parser.add_argument('-eval', '--evaluate', action='store_true', help='evaluate with low randomness')
args = parser.parse_args()


# Create log dir
if args.folder:
	log_dir = args.folder
else:
	log_dir = "./log_dir/"
	os.makedirs(log_dir, exist_ok=True)

tensorboard_log_dir = os.path.join(log_dir, 'tb_log')
os.makedirs(tensorboard_log_dir, exist_ok=True)

if __name__ == "__main__":
	if args.render:
		env = MarioEnv(showplot=True)
	else:
		env = MarioEnv(showplot=False)

	env = Monitor(env, log_dir)
	#check_env(env, warn=True)
	print("RUNNING!")
	#print('Load lua_mario_v0.lua into Bizhawk client')
	#callback = SaveOnBestTrainingRewardCallback(check_freq=1000, log_dir=log_dir)
	callback = CheckpointCallback(save_freq=10000, save_path=log_dir,
	                                         name_prefix='rl_model')
	if args.load:
		print('Model Loaded')
		load_file = args.load
		env = DummyVecEnv([lambda: env])
		model = PPO2.load(load_file, env=env)
				
	else: 
		print('Training')
		gamma = 0.9   # discount rate
		#self.epsilon_decay = 0.99
		learning_rate = 1e-4
		target_network_update_freq = 1000
		model = PPO2(MlpPolicy, env, verbose=0, 
						gamma=gamma,
						noptepochs=8,
						nminibatches=8,
						learning_rate= learning_rate,
						ent_coef = 0.001,
						tensorboard_log=tensorboard_log_dir
						)

	if args.evaluate:
		if not args.load:
			print('Load a model to evaluate')
		evaluate_policy(model, env, deterministic = False, n_eval_episodes=10)
		
	else:
		model.learn(total_timesteps=int(1e7),
			callback=callback)		

	print('done simulation')