from my_env import env
from my_env import web_client_mod

# AI 服务器设置
# 帐号注册链接 http://ai.go129.com:8000/register
server_info = {"url": "ai.go129.com",
               "port": 8000,
               "username": "",
               "password": "",
               "token": ""}


# env转字符串，与douzero的str不同!
EnvCard2RealCard = {3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: 'T', 11: 'J', 12: 'Q',
                    13: 'K', 14: 'A', 17: '2', 20: 'X', 30: 'D'}



# env转手牌内容
def env_to_cards(slist):
    cards = ''.join([EnvCard2RealCard[c] for c in slist[::-1]])  # 先反转列表再拼接
    return cards


class My_Agent:
    def __init__(self):
        # 三个位置的对象
        self.agent_dict = {}
        self.login_state = False
        self.agent_dict["landlord"] = env.My_Env(position="landlord", server_info=server_info)
        self.agent_dict["landlord_up"] = env.My_Env(position="landlord_up", server_info=server_info)
        self.agent_dict["landlord_down"] = env.My_Env(position="landlord_down", server_info=server_info)
        self.login_server()                    # GoAi 服务器登录


    def login_server(self):
        global server_info
        # API调用示例
        url = "http://" + server_info['url'] + ":" + str(server_info['port'])
        client = web_client_mod.Http_Client(url)
        post_data = {"username": server_info['username'],
                     "password": server_info['password']}

        result = client.post("/login", post_data)
        if result.get("error"):
            print("GoAi 帐号认证失败! ErrorCode:", result.get("error"))
            self.login_state = False
            return False
        else:
            server_info['token'] = result["message"]
            self.agent_dict["landlord"].update_server_info(server_info)
            self.agent_dict["landlord_up"].update_server_info(server_info)
            self.agent_dict["landlord_down"].update_server_info(server_info)
            print("GoAi 帐号认证成功! token:", server_info['token'])
            self.login_state = True
            return True

        # 全新开始一个位置的游戏
    def new_game(self, position="landlord", cards="", three_cards=""):
        self.agent_dict[position].new_game(cards, three_cards)

    def get_up_position(self,position_name="landlord"):
        return self.agent_dict[position_name].up_position

    def get_down_position(self,position_name="landlord"):
        return self.agent_dict[position_name].down_position

    # 返回我当前全部手牌
    def get_my_hand_cards(self,position_name="landlord"):
        return self.agent_dict[position_name].my_hand_cards

    # 获取指定位置上次出牌内容
    def get_last_action(self, position_name="landlord", position=""):
        return self.agent_dict[position_name].player_last_action[position]

    # 获取指定位置当前手牌数量
    def get_cards_count(self, position_name="landlord", position=""):
        return self.agent_dict[position_name].player_cards_count[position]

    # 检测是否结束，否返回False,是返回最后出牌位置
    def game_over(self, position_name="landlord"):
        return self.agent_dict[position_name].game_over()

    # 计算另外两家当前合计手牌内容
    def get_other_cards(self, position_name="landlord", my_cards="", my_action_all="", up_action_all="", down_action_all=""):
        return self.agent_dict[position_name].get_other_cards(my_cards, my_action_all, up_action_all, down_action_all)

    # 记录玩家动作,AI出牌
    def step(self, position_name="landlord", position="", action=None):
        if self.login_state == False:
            print("step_请先登录帐号再执行操作!")
            return None

        back = self.agent_dict[position_name].step(position,action)                     # GoAi预测
        if back == -1:                                                                  # 出错
            print("预测出错啦!")
            return None

        return back
