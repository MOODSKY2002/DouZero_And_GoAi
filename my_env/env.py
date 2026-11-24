"""
env.py - 斗地主自定义环境（完全独立，零外部依赖）
"""

from collections import Counter
from my_env import web_client_mod

# 调试
import pickle
import os


# ======================== 牌面编码 ========================
# 数值 = 牌力，直接比较大小
# 3~14 → 3~A；17 → 2；20 → 小王；30 → 大王

CARD_NAMES = {3: '3',  4: '4',  5: '5',  6: '6',  7: '7',
              8: '8',  9: '9', 10: 'T', 11: 'J', 12: 'Q',
              13: 'K', 14: 'A', 17: '2', 20: 'X', 30: 'D'}

FULL_DECK = ([c for c in range(3, 15) for _ in range(4)]
            + [17] * 4
            + [20, 30])

# 默认全部手牌列表
all_cards_default = [3,3,3,3,4,4,4,4,5,5,5,5,6,6,6,6,7,7,7,7,8,8,8,8,9,9,9,9,10,10,10,10,11,11,11,11,12,12,12,12,13,13,13,13,14,14,14,14,17,17,17,17,20,30]

# 位置
POSITIONS = ('landlord', 'landlord_down', 'landlord_up')

# 每个位置对应的上下家位置
OTHER_POSITIONS = {'landlord': {'up':'landlord_up','down':'landlord_down'},
                   'landlord_down': {'up':'landlord','down':'landlord_up'},
                   'landlord_up': {'up':'landlord_down','down':'landlord'}}
# 每个角色的手牌数量
HAND_SIZE = {'landlord': 20, 'landlord_down': 17, 'landlord_up': 17}

# 轮到下一个玩家
NEXT_PLAYER = {'landlord': 'landlord_down', 'landlord_down': 'landlord_up', 'landlord_up': 'landlord'}


# ======================== 工具函数 ========================

def cards_to_str(cards):
    if not cards:
        return 'Pass'
    return ''.join(CARD_NAMES.get(c, '?') for c in sorted(cards))


def validate_cards(cards):
    counter = Counter(cards)
    full_counter = Counter(FULL_DECK)
    for card, count in counter.items():
        if card not in CARD_NAMES:
            return False, f"非法牌值: {card}"
        if count > full_counter[card]:
            return False, f"牌 {CARD_NAMES[card]} 数量超限: {count} > {full_counter[card]}"
    return True, ""

# 调试临时数据保存与载入
def save_tmp(file,info):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file)
    with open(path, "wb") as f:
        pickle.dump(info, f)

def load_tmp(file):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file)
    with open(path, "rb") as f:
        return pickle.load(f)

# ======================== 自定义环境 ========================

class My_Env:
    """
    斗地主自定义环境。

    Parameters
    ----------
    hand_cards : list[int]
        我的手牌。地主 20 张，农民 17 张。
    position : str
        我的位置：'landlord' | 'landlord_down' | 'landlord_up'
    three_landlord_cards : list[int]
        地主三张底牌（公开信息）。
    """
    def __init__(self, position,server_info):
        if position not in POSITIONS:
            raise ValueError(f"非法位置: {position}，合法值: {POSITIONS}")

        self.position = position                                    # 我的位置
        self.up_position = OTHER_POSITIONS[position]['up']          # 上家位置
        self.down_position = OTHER_POSITIONS[position]['down']      # 下家位置

        self.my_hand_cards = []                                     # 我的当前手牌
        self.my_default_hand_cards = []                             # 我的初始手牌
        self.three_landlord_cards = []                              # 地主三张牌
        self.all_action_list = []                                   # 全局所有位置出牌动作列表
        self.player_last_action = []                                # 每个位置最后一次出牌动作字典
        self.player_all_actions = []                                # 每个位置最后一次出牌动作字典
        self.player_cards_count = []                                # 每个位置的当前手牌数量
        self.current_player = ""                                    # 当前轮到谁出牌

        # AI 服务器连接信息
        self.url = server_info['url']
        self.port = server_info['port']
        self.token = server_info['token']

        # AI查询接口
        self.web_client = web_client_mod.Http_Client(("http://" + self.url + ":" + str(self.port)))

    def update_server_info(self,server_info):
        # AI 服务器连接信息
        self.url = server_info['url']
        self.port = server_info['port']
        self.token = server_info['token']

    def new_game(self,hand_cards, three_landlord_cards):
        hand_cards = sorted(list(hand_cards))
        three_landlord_cards = sorted(list(three_landlord_cards))

        # 检查底牌数量
        if len(three_landlord_cards) != 3:
            raise ValueError(f"地主底牌必须是 3 张，但传入了 {len(three_landlord_cards)} 张")

        # 核对我的位置手牌数量
        expected_size = HAND_SIZE[self.position]
        if len(hand_cards) != expected_size:
            raise ValueError(f"位置 {self.position} 需要 {expected_size} 张手牌，"
                             f"但传入了 {len(hand_cards)} 张")

        # 检查手牌
        ok, msg = validate_cards(hand_cards)
        if not ok:
            raise ValueError(f"手牌校验失败: {msg}")

        # 检查底牌
        ok2, msg2 = validate_cards(three_landlord_cards)
        if not ok2:
            raise ValueError(f"地主底牌校验失败: {msg2}")

        # 如果我是地主检查底牌是否在我手中
        if self.position == 'landlord':
            for c in three_landlord_cards:
                if c not in hand_cards:
                    raise ValueError(f"地主底牌 {cards_to_str([c])} 不在地主手牌中")

        self.my_hand_cards = hand_cards                             # 我的当前手牌
        self.my_default_hand_cards = hand_cards                     # 我的初始手牌
        self.three_landlord_cards = three_landlord_cards            # 地主三张牌
        self.all_action_list = []                                   # 全局所有位置出牌动作列表

        self.player_last_action = {'landlord': [], 'landlord_down': [], 'landlord_up': []}        # 每个位置最后一次出牌动作字典
        self.player_all_actions = {'landlord': [], 'landlord_down': [], 'landlord_up': []}        # 每个位置全部累计出牌动作内容
        self.player_cards_count = {'landlord': 20, 'landlord_down': 17, 'landlord_up': 17}        # 每个位置的当前手牌数量
        self.current_player = "landlord"                            # 当前轮到谁出牌

    # 计算另外两家当前合计手牌内容
    def get_other_cards(self,my_cards, my_action_all, up_action_all, down_action_all):
        remain_counter = (Counter(all_cards_default)
                          - Counter(my_cards)
                          - Counter(my_action_all)
                          - Counter(up_action_all)
                          - Counter(down_action_all))
        return list(remain_counter.elements())

    def get_up_position(self):
        return self.up_position

    def get_down_position(self):
        return self.down_position

    # 返回我当前全部手牌
    def get_my_hand_cards(self):
        return self.my_hand_cards

    # 获取指定位置上次出牌内容
    def get_last_action(self, position):
        return self.player_last_action[position]

    # 获取指定位置当前手牌数量
    def get_cards_count(self, position):
        return self.player_cards_count[position]

    # 记录玩家动作,AI出牌
    def step(self, position="", action=None):
        info = []
        saction = action # 记录动作

        # 出牌位置校验检查
        if not position:
            position = self.current_player
            print("当前传入空位置，给值:",position)
        elif position != self.current_player:
            print(f"当前轮到 {self.current_player}，但传入了 {position} 我的位置:{self.position}")
            raise ValueError(f"当前轮到 {self.current_player}，但传入了 {position}")

        # 轮到我出牌
        if position == self.position:
            # 全部原始局势信息
            my_action_all = self.player_all_actions[self.position]             # 我的信息
            my_cards = self.my_hand_cards
            my_action = self.player_last_action[self.position]

            up_action_all = self.player_all_actions[self.up_position]          # 上家信息
            up_action = self.player_last_action[self.up_position]

            down_action_all = self.player_all_actions[self.down_position]      # 下家信息
            down_action = self.player_last_action[self.down_position]

            other_cards = self.get_other_cards(my_cards, my_action_all, up_action_all, down_action_all)     # 上下家当前手牌合计信息

            info = {"my_cards_count": 0,
                    "up_cards_count": 0,
                    "down_cards_count": 0,
                    "my_action_all": my_action_all,
                    "my_cards": my_cards,
                    "my_action": my_action,
                    "up_action_all": up_action_all,
                    "up_action": up_action,
                    "down_action_all": down_action_all,
                    "down_action": down_action,
                    "other_cards": other_cards}

            post_data = {"token": self.token,
                         "position": self.position,
                         "gameinfo": info}

            back = self.web_client.post("/predict", post_data)             # 提交原始信息，接收AI返回动作列表
            status = back['status']                                             # 返回状态
            if status == "success":
                # Go_Ai 出牌策略
                data = back['data']                                             # 返回的动作列表
                info = data
                saction = data[0][0]                                            # 最佳动作

                # 从我的手牌中移除出牌内容
                counter1 = Counter(self.my_hand_cards)
                counter2 = Counter(saction)

                # 更新出牌后剩余手牌
                result_counter = counter1 - counter2
                self.my_hand_cards = list(result_counter.elements())

            else:
                print(f"预测出错 ErrorCode: {back['message']}")
                return -1 # AI服务器预测报错
        else:
            # 记录其它位置出牌内容
            pass

        is_pass = False
        saction = sorted(list(saction))
        action_count = len(saction)
        if action_count == 0:                           # 如果是不出牌
            is_pass = True

        # 出牌记录
        self.all_action_list.append((position, saction))
        self.player_last_action[position] = saction

        # 不出牌
        if is_pass != True:
            self.player_all_actions[position].extend(saction)
            self.player_cards_count[position] -= len(saction)

        self.current_player = NEXT_PLAYER[position]        # 下一个出牌位置

        if len(info) > 0:
            return info[0],info

    # 检测是否结束，否返回False,是返回最后出牌位置
    def game_over(self):
        for position in POSITIONS:
            cards_count = self.player_cards_count[position]
            if cards_count == 0:
                return position

        return False

    def get_all_game_action_list(self):
        return self.all_action_list
