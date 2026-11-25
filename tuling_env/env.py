"""
env.py - 斗地主自定义环境（适配图灵云 Game AI 标准路由接口）
接口文档: https://www.tulingyun.com/docs_game_ai.html

对外接口用字符串位置: 'landlord' / 'landlord_down' / 'landlord_up'
内部自动转为图灵要求的 0 / 1 / 2 后再发请求。
牌面: 外部仍用内部 int(3~14,17,20,30)，发接口时自动转单字符(3~9,T,J,Q,K,A,2,X,D)。
"""

from collections import Counter
from my_env import web_client_mod

import pickle
import os

# ======================== 牌面编码 ========================
CARD_NAMES = {3: '3',  4: '4',  5: '5',  6: '6',  7: '7',
              8: '8',  9: '9', 10: 'T', 11: 'J', 12: 'Q',
              13: 'K', 14: 'A', 17: '2', 20: 'X', 30: 'D'}
CARD_VALUES = {v: k for k, v in CARD_NAMES.items()}

FULL_DECK = ([c for c in range(3, 15) for _ in range(4)]
            + [17] * 4
            + [20, 30])

all_cards_default = [3,3,3,3,4,4,4,4,5,5,5,5,6,6,6,6,7,7,7,7,8,8,8,8,9,9,9,9,10,10,10,10,11,11,11,11,12,12,12,12,13,13,13,13,14,14,14,14,17,17,17,17,20,30]

# ======================== 位置 ========================
# 对外字符串 <-> 图灵 int
POS_STR2INT = {'landlord': 0, 'landlord_down': 1, 'landlord_up': 2}
POS_INT2STR = {v: k for k, v in POS_STR2INT.items()}

POSITIONS = ('landlord', 'landlord_down', 'landlord_up')

# 每个字符串位置对应的上下家(字符串)
OTHER_POSITIONS = {'landlord':      {'up': 'landlord_up',   'down': 'landlord_down'},
                   'landlord_down': {'up': 'landlord',      'down': 'landlord_up'},
                   'landlord_up':   {'up': 'landlord_down', 'down': 'landlord'}}

HAND_SIZE = {'landlord': 20, 'landlord_down': 17, 'landlord_up': 17}

# 字符串位置的下一位
NEXT_PLAYER = {'landlord': 'landlord_down',
               'landlord_down': 'landlord_up',
               'landlord_up': 'landlord'}

# 图灵云标准路由
TLY_BASE = "https://www.tulingyun.com"
ROUTE_BEST_ACTION = "/api/game_ai/doudizhu/best_action"
ROUTE_CALL        = "/api/game_ai/doudizhu/can_be_landlord"
ROUTE_DOUBLE      = "/api/game_ai/doudizhu/can_double"


# ======================== 工具函数 ========================
def cards_to_str(cards):
    """内部 int 列表 -> 接口字符串; 空列表返回空串(表示 PASS)"""
    if not cards:
        return ''
    return ''.join(CARD_NAMES.get(c, '?') for c in sorted(cards))


def str_to_cards(s):
    """接口字符串 -> 内部 int 列表; 空串或 'PASS' 返回空列表"""
    if not s or str(s).upper() == 'PASS':
        return []
    return [CARD_VALUES[ch] for ch in s]


def validate_cards(cards):
    counter = Counter(cards)
    full_counter = Counter(FULL_DECK)
    for card, count in counter.items():
        if card not in CARD_NAMES:
            return False, f"非法牌值: {card}"
        if count > full_counter[card]:
            return False, f"牌 {CARD_NAMES[card]} 数量超限: {count} > {full_counter[card]}"
    return True, ""


def save_tmp(file, info):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file)
    with open(path, "wb") as f:
        pickle.dump(info, f)


def load_tmp(file):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file)
    with open(path, "rb") as f:
        return pickle.load(f)


# ======================== 环境 ========================
class My_Env:
    """
    斗地主环境（适配图灵云 Game AI 标准路由）。

    对外位置参数统一用字符串:
        'landlord' / 'landlord_down' / 'landlord_up'
    内部自动转 0/1/2 发给图灵接口。
    """

    def __init__(self, position):
        if position not in POSITIONS:
            raise ValueError(f"非法位置: {position}，合法值: {POSITIONS}")

        self.position = position                                    # 字符串位置
        self.position_int = POS_STR2INT[position]                   # 图灵 int 位置
        self.up_position = OTHER_POSITIONS[position]['up']
        self.down_position = OTHER_POSITIONS[position]['down']

        self.my_hand_cards = []
        self.my_default_hand_cards = []
        self.three_landlord_cards = []
        self.all_action_list = []                                   # [(字符串位置, int牌列表)]
        self.player_last_action = {}
        self.player_all_actions = {}
        self.player_cards_count = {}
        self.current_player = 'landlord'                            # 字符串位置

        self.web_client = web_client_mod.Http_Client(TLY_BASE)

    # ---------- 历史序列 ----------
    def build_action_seq(self):
        """完整出牌序列, PASS 保留空项, 逗号分隔, 例 '3,,'"""
        return ','.join(cards_to_str(a) for _, a in self.all_action_list)

    # ---------- 开局 ----------
    def new_game(self, hand_cards, three_landlord_cards):
        hand_cards = sorted(list(hand_cards))
        three_landlord_cards = sorted(list(three_landlord_cards))

        if len(three_landlord_cards) != 3:
            raise ValueError(f"地主底牌必须是 3 张，但传入了 {len(three_landlord_cards)} 张")

        expected_size = HAND_SIZE[self.position]
        if len(hand_cards) != expected_size:
            raise ValueError(f"位置 {self.position} 需要 {expected_size} 张手牌，"
                             f"但传入了 {len(hand_cards)} 张")

        ok, msg = validate_cards(hand_cards)
        if not ok:
            raise ValueError(f"手牌校验失败: {msg}")
        ok2, msg2 = validate_cards(three_landlord_cards)
        if not ok2:
            raise ValueError(f"地主底牌校验失败: {msg2}")

        if self.position == 'landlord':
            for c in three_landlord_cards:
                if c not in hand_cards:
                    raise ValueError(f"地主底牌 {cards_to_str([c])} 不在地主手牌中")

        self.my_hand_cards = hand_cards
        self.my_default_hand_cards = list(hand_cards)
        self.three_landlord_cards = three_landlord_cards
        self.all_action_list = []
        self.player_last_action = {'landlord': [], 'landlord_down': [], 'landlord_up': []}
        self.player_all_actions = {'landlord': [], 'landlord_down': [], 'landlord_up': []}
        self.player_cards_count = {'landlord': 20, 'landlord_down': 17, 'landlord_up': 17}
        self.current_player = 'landlord'

    # ---------- 叫/抢地主 ----------
    def call_landlord(self, phase='call', current_role=None):
        """
        POST /api/game_ai/doudizhu/can_be_landlord
        phase: 'call' | 'rob'
        current_role: 抢地主时传字符串 'landlord_down' / 'landlord_up'（内部直接透传给接口）
        """
        payload = {
            "player_hand_cards": cards_to_str(self.my_hand_cards),
            "phase": phase,
        }
        if current_role:
            payload["current_role"] = current_role

        back = self.web_client.post(ROUTE_CALL, payload)
        if back.get('status') == 0:
            return back['data']
        print(f"叫/抢地主预测出错: {back.get('message')}")
        return None

    # ---------- 加倍 ----------
    def can_double(self):
        """
        POST /api/game_ai/doudizhu/can_double
        返回 data: {'factor','action','action_name','wp','adp'}
        """
        payload = {
            "player_position": self.position_int,               # 转 int 发接口
            "player_hand_cards": cards_to_str(self.my_hand_cards),
            "three_landlord_cards": cards_to_str(self.three_landlord_cards),
        }
        back = self.web_client.post(ROUTE_DOUBLE, payload)
        if back.get('status') == 0:
            return back['data']
        print(f"加倍预测出错: {back.get('message')}")
        return None

    # ---------- 出牌 ----------
    def step(self, position=None, action=None):
        """
        记录一步动作。轮到我时自动调 best_action 接口。

        position: 字符串位置; 传 None 表示 current_player
        action: 其他位置的动作(内部 int 列表), 轮到我时忽略
        返回: (saction, info) 若轮到我; 否则 None
        """
        if position is None:
            position = self.current_player
        elif position != self.current_player:
            raise ValueError(f"当前轮到 {self.current_player}，但传入了 {position}")

        info = None
        if position == self.position:
            payload = {
                "player_position": self.position_int,           # 转 int 发接口
                "player_hand_cards": cards_to_str(self.my_hand_cards),
                "three_landlord_cards": cards_to_str(self.three_landlord_cards),
                "card_play_action_seq": self.build_action_seq(),
            }
            back = self.web_client.post(ROUTE_BEST_ACTION, payload)
            if back.get('status') != 0:
                print(f"预测出错: {back.get('message')}")
                return -1

            data = back['data']
            info = data
            saction = str_to_cards(data['action'])

            self.my_hand_cards = list((Counter(self.my_hand_cards)
                                       - Counter(saction)).elements())
        else:
            saction = list(action) if action else []

        saction = sorted(saction)
        is_pass = len(saction) == 0
        self.all_action_list.append((position, saction))
        self.player_last_action[position] = saction

        if not is_pass:
            self.player_all_actions[position].extend(saction)
            self.player_cards_count[position] -= len(saction)

        self.current_player = NEXT_PLAYER[position]

        return (saction, info) if info is not None else None

    # ---------- 查询 ----------
    def get_up_position(self):
        return self.up_position

    def get_down_position(self):
        return self.down_position

    def get_my_hand_cards(self):
        return self.my_hand_cards

    def get_last_action(self, position):
        """position: 字符串位置"""
        return self.player_last_action[position]

    def get_cards_count(self, position):
        """position: 字符串位置"""
        return self.player_cards_count[position]

    def get_all_game_action_list(self):
        return self.all_action_list

    def get_other_cards(self):
        remain = (Counter(all_cards_default)
                  - Counter(self.my_hand_cards)
                  - Counter(self.player_all_actions['landlord'])
                  - Counter(self.player_all_actions['landlord_down'])
                  - Counter(self.player_all_actions['landlord_up']))
        return list(remain.elements())

    def game_over(self):
        for position in POSITIONS:
            if self.player_cards_count[position] == 0:
                return position
        return False