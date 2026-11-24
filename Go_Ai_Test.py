"""
关键变量说明
go_ai_position   斗地主中Go_Ai控制的位置(字符串)
play_count       进行测试的游戏局数(整数)
"""



import datetime
import time

from loguru import logger

import sys
import BidModel
import LandlordModel
import FarmerModel
from douzero.env.game import GameEnv
from douzero.evaluation.deep_agent import DeepAgent

import threading
import copy

# GoAi
import my_agent
import random

# 全部手牌env
AllEnvCard = [3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 8, 9, 9, 9, 9, 10, 10, 10, 10,
              11, 11, 11, 11, 12, 12, 12, 12, 13, 13, 13, 13, 14, 14, 14, 14, 17, 17, 17, 17, 20, 30]

# 已经被人挑选的手牌字典
use_cards = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0, 14:0, 15:0, 16:0, 17:0, 18:0,
            19:0, 20:0, 21:0, 22:0, 23:0, 24:0, 25:0, 26:0, 27:0, 28:0, 29:0, 30:0, 31:0, 32:0, 33:0, 34:0, 35:0, 36:0,
            37:0, 38:0, 39:0, 40:0, 41:0, 42:0, 43:0, 44:0, 45:0, 46:0, 47:0, 48:0, 49:0, 50:0, 51:0, 52:0, 53:0}

RealCard2EnvCard = {'3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10,
                    'J': 11, 'Q': 12, 'K': 13, 'A': 14, '2': 17, 'X': 20, 'D': 30}

# DouZero env编码对照字典
EnvCard2RealCard = {3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',10: 'T', 11: 'J', 12: 'Q', 13: 'K',
                    14: 'A', 17: '2',20: 'X', 30: 'D'}

# 配置日志
key = "log"
logger.remove()
my_logger = logger.bind(type=key)
now = datetime.datetime.now()
sdate = now.strftime("%Y%m%d")
stime = now.strftime("%H%M%S")
logpath = 'log/' + sdate + stime + ".log"
logger.add(logpath,format="{message}",filter=lambda record: record["extra"].get("type") == key)

# 写入日志
def logwrite(sinfo=""):
    my_logger.info(sinfo)

# env转手牌内容
def env_to_cards(slist):
    cards = str(''.join([EnvCard2RealCard[c] for c in slist]))[::-1]
    return cards

# 手牌内容转env
def cards_to_env(slist):
    if len(slist) == 0:
        return []

    cards_env = [RealCard2EnvCard[c] for c in slist]
    return cards_env

# env 手牌字典转手牌内容字典
def env_dict_to_cards(player_cards):
    my_player_cards = {}
    for i in range(0,4):
        my_player_cards[i] = env_to_cards(player_cards[i])
    return my_player_cards

# 随机返回一张还没有被人挑选的手牌序号
def random_poker_index(now_use_cards):
    while True:
        index = random.randint(0, 53)  # 随机手牌序号
        if now_use_cards[index] == 0:         # 没有被人挑选
            now_use_cards[index] = 1          # 标记已经被挑选中
            return index                      # 返回序号


# 根据手牌抢地主，分配三家位置
def get_player_position(player_cards):
    score_list = {}
    player_cards_new = {}

    for i in range(0, 3):
        score_list[i] = round(BidModel.predict_score(env_to_cards(player_cards[i])), 4)  # 根据手牌获取分值评价

    max_player_id, max_score = max(score_list.items(), key=lambda item: item[1])         # 最高分玩家index

    player_cards_new['landlord'] = player_cards[max_player_id]                           # 定义地主手牌
    player_cards_new['landlord'] += player_cards[3]                                      # 合并3张地主牌
    player_cards_new['landlord'].sort(reverse=False)                                     # 手牌排序
    player_cards_new['three_cards'] = player_cards[3]                                    # 定义三张地主牌

    if max_player_id == 0:  # 根据地主位置分配三家位置
        player_cards_new['landlord_down'] = player_cards[1]
        player_cards_new['landlord_up'] = player_cards[2]
    elif max_player_id == 1:
        player_cards_new['landlord_up'] = player_cards[0]
        player_cards_new['landlord_down'] = player_cards[2]
    elif max_player_id == 2:
        player_cards_new['landlord_down'] = player_cards[0]
        player_cards_new['landlord_up'] = player_cards[1]

    return player_cards_new

# 随机洗牌，返回三个玩家的手牌以及地主牌
def shuffle_the_cards(env_mode=True):
    player_cards = {0: [], 1: [], 2: [], 3: []}         # 三个玩家(0,1,2)初始手牌，以及地主(3)初始手牌
    now_use_cards = use_cards.copy()                    # 初始化已经被挑选的手牌字典

    while len(player_cards[2]) < 17:                    # 每个玩家均挑选到17张手牌
        for i in range(0, 3):                           # 轮流随机挑选手牌
            index = random_poker_index(now_use_cards)   # 随机挑选一张手牌
            player_cards[i].append(AllEnvCard[index])   # 保存随机挑选的手牌牌面

    player_cards[3] = [AllEnvCard[index] for index, used in now_use_cards.items() if used == 0]  # 三张地主牌
    for i in range(0, 4):
        player_cards[i].sort(reverse=False)                                                      # 手牌排序，从小到大
        if not env_mode:
            player_cards[i] = env_to_cards(player_cards[i])
    return player_cards


# 随机生成对局手牌局面数据文件
def create_game(count=1):
    player_data = []
    player_cards_env = {0: [], 1: [], 2: [], 3: []}

    for i in range(0,count):
        player_cards_env = shuffle_the_cards()               # 随机手牌内容env
        player_cards = get_player_position(player_cards_env) # 抢地主分配手牌
        player_data.append(player_cards)
    return player_data

# 根据自己手牌计算出另外两家手牌合计
def calc_other_cards_from_env(slist):
    other_cards = []
    for i in set(AllEnvCard):
        other_cards.extend([i] * (AllEnvCard.count(i) - slist.count(i)))
    return other_cards


# 创建DouzeroAI
def create_douzero_env(player_cards,env_dict_now):
    position_index_dict = {"landlord_up": 0, "landlord": 1, "landlord_down": 2}                 # 位置相对应的位置序号
    card_play_model_path_dict = {'landlord': "baselines/resnet/resnet_landlord.ckpt",           # 三种位置的模型列表
                                 'landlord_up': "baselines/resnet/resnet_landlord_up.ckpt",
                                 'landlord_down': "baselines/resnet/resnet_landlord_down.ckpt"}

    if len(env_dict_now) == 0:
        env_dict = {}                                                    # 创建AI空字典
    else:
        env_dict = env_dict_now                                          # 重置AI字典

    for position in ['landlord','landlord_up','landlord_down']:
        user_position_code = position_index_dict[position]                # 当前玩家位置序号
        use_hand_cards_env = player_cards[position]                       # 玩家手牌
        three_landlord_cards_env = player_cards['three_cards']            # 三张地主牌
        other_hand_cards = calc_other_cards_from_env(use_hand_cards_env)  # 其它两家的手牌

        card_play_data_list = {}
        card_play_data_list.update({                                      # 创建游戏对局参数
            'three_landlord_cards': three_landlord_cards_env,
            ['landlord_up', 'landlord', 'landlord_down'][(user_position_code + 0) % 3]: use_hand_cards_env,
            ['landlord_up', 'landlord', 'landlord_down'][(user_position_code + 1) % 3]: other_hand_cards[0:17] if (user_position_code + 1) % 3 != 1 else other_hand_cards[17:],
            ['landlord_up', 'landlord', 'landlord_down'][(user_position_code + 2) % 3]: other_hand_cards[0:17] if (user_position_code + 1) % 3 == 1 else other_hand_cards[17:]
        })

        if len(env_dict_now) == 0:    # 创建AI
            players = [0, 0]
            players[0] = position
            players[1] = DeepAgent(position, card_play_model_path_dict[position])
            env_dict[position] = GameEnv(players)
        else:                        # 重置AI
            env_dict[position].reset()
        env_dict[position].card_play_init(card_play_data_list)
    return env_dict




# 测试与Douzero局对战
env_dict = {}
put_list = ['landlord', 'landlord_down', 'landlord_up']
win_data1 = {"landlord_up":0,"landlord":0,"landlord_down":0}    # 胜率统计1
win_data2 = {"landlord_up":0,"landlord":0,"landlord_down":0}    # 胜率统计2
play_count = 20                                                 # 测试对局数量
play_data = create_game(play_count)                             # 随机发牌创建指定对局数据

print(f"使用相同随机开局数据 play_data, 进行两次测试显示各自胜胜率。\n第一次三个位置全部为DouZero。第二次两个位置为DouZero，指定位置为Go_Ai。")
# 第一种胜率,随机对局数据使用3个DouZero对局
for i in range(0,play_count):
    # 构造日志
    stmp = f"DouZero 第 {i+1} 局"
    print(f"\rDouZero 第 {i + 1} 局   ", end='', flush=True)
    logwrite(stmp)

    game_info = copy.deepcopy(play_data[i])
    env_dict = create_douzero_env(game_info, env_dict)                     # 创建DouZero三个位置的Agent

    action = ""
    action_env = []
    game_over = False                                                      # 对局结束状态(Douzero为True/False)

    while game_over == False:
        for now_pos in put_list:
            # DouZero出牌
            my_cards = env_dict[now_pos].info_sets[now_pos].player_hand_cards.copy()  # 获取当前手牌

            action_message, _ = env_dict[now_pos].step(now_pos)                                         # DouZero 最优动作
            action = action_message['action']                                                           # 只取动作
            action_env = cards_to_env(action)

            # 构造日志
            stmp = f"位置: {now_pos.ljust(13)} 手牌: {env_to_cards(my_cards).ljust(20)} 出牌: {action}"
            logwrite(stmp)

            # 通知另两个位置的 DouZero Agent 出牌动作内容
            pos_list = put_list.copy()
            pos_list.remove(now_pos)
            other_pos1 = pos_list[0]
            other_pos2 = pos_list[1]
            env_dict[other_pos1].step(other_pos1, action_env)
            env_dict[other_pos2].step(other_pos2, action_env)

            game_over = env_dict[now_pos].game_over     # 获取对局是否结束(Duozero返回True/False)

            # 判断对局结束
            if game_over != False:
                win_data1[now_pos] += 1                 # 出完的位置胜利次数+1
                logwrite(f"\n\n")
                break

print("DouZero对局(各位置出完牌次数):",win_data1)

pos_list = ['landlord_up', 'landlord', 'landlord_down']
go_ai_position = pos_list[1]                                    # 测试时Go_Ai的角色位置
go_env = my_agent.My_Agent()                                    # Go_Ai agent(自动包含3个位置的env)

# 第二种胜率，指定位置使用Go_Ai与另外两个DouZero对局
for i in range(0,play_count):
    # 构造日志
    stmp = f"Go_Ai 第 {i+1} 局 位置: {go_ai_position}"
    print(f"\rGo_Ai 第 {i + 1} 局   ", end='', flush=True)
    logwrite(stmp)

    game_info = copy.deepcopy(play_data[i])
    env_dict = create_douzero_env(game_info, env_dict)                    # 创建DouZero三个位置的Agent

    # 初始Go_Ai对局
    user_hand_cards_env = play_data[i][go_ai_position]                     # Go_Ai 位置初始手牌
    three_cards_env = play_data[i]['three_cards']                          # 三张地主牌
    go_env.new_game(go_ai_position,user_hand_cards_env,three_cards_env)    # 全新开局

    action = ""
    action_env = []
    game_over = False                                                      # 对局结束状态(Douzero为True/False, Go_Ai为False/出完位置)

    while game_over == False:
        for now_pos in put_list:
            if go_ai_position == now_pos:
                my_cards = go_env.get_my_hand_cards(go_ai_position)                                         # 获取当前手牌

                # Go_Ai出牌
                action_message, action_list = go_env.step(go_ai_position, position=now_pos, action=action)  # Go_Ai 最优动作
                action = my_agent.env_to_cards(action_message[0])                                           # 只取动作

                # 构造日志
                stmp = f"位置: {go_ai_position.ljust(13)} 手牌: {env_to_cards(my_cards).ljust(20)} 出牌: {action}"
                logwrite(stmp)

                # 通知 DouZero 出牌动作内容
                action_env = cards_to_env(action)
                pos_list = put_list.copy()
                pos_list.remove(go_ai_position)
                other_pos1 = pos_list[0]
                other_pos2 = pos_list[1]
                env_dict[other_pos1].step(other_pos1, action_env)
                env_dict[other_pos2].step(other_pos2, action_env)

            else:
                # DouZero出牌
                my_cards = env_dict[now_pos].info_sets[now_pos].player_hand_cards.copy()                    # 获取当前手牌

                action_message, _ = env_dict[now_pos].step(now_pos)                                         # DouZero 最优动作
                action = action_message['action']                                                           # 只取动作
                action_env = cards_to_env(action)

                # 构造日志
                stmp = f"位置: {now_pos.ljust(13)} 手牌: {env_to_cards(my_cards).ljust(20)} 出牌: {action}"
                logwrite(stmp)

                # 通知另一个 DouZero Agent 出牌动作内容
                pos_list = put_list.copy()
                pos_list.remove(go_ai_position)
                pos_list.remove(now_pos)
                other_pos = pos_list[0]
                env_dict[other_pos].step(other_pos, action_env)

                # 通知 Go_Ai 出牌动作内容
                go_env.step(go_ai_position, position=now_pos, action=action_env)

            game_over = go_env.game_over(go_ai_position)  # 获取对局是否结束(Go_Ai返回出完牌的位置: landlord/landlord_down/landlord_up)

            # 判断对局结束
            if game_over != False:
                win_data2[game_over] += 1                 # 出完的位置胜利次数+1
                logwrite(f"\n\n")
                break

print(f"Go_Ai 对局({go_ai_position})(各位置出完牌次数):",win_data2)





