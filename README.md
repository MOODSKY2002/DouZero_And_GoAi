# 基于DouZero_For_HLDDZ_FullAuto示例，展示、演示GoAi效果。参考DouZero原理全新开发的MOE构架的斗地主模型。
* 本项目DouZero相关代码基于[DouZero](https://github.com/kwai/DouZero) 和  [DouZero_For_Happy_DouDiZhu](https://github.com/tianqiraf/DouZero_For_HappyDouDiZhu)
* 感谢 girgle（QQ群马云）对新版欢乐斗地主进行了适配，现在仓库代码已支持新版欢乐斗地主
* 环境配置请移步项目DouZero

* main.py --- 将DouZero替换为Go_Ai
* main_old.py --- 原版主文件
* Go_Ai_Test.py --- Go_Ai与DouZero对战测试程序，直接运行即可观察胜率对比数据。

* my_agent.py --- Go_Ai Agent模块,正式使用前需要先注册自己的帐号，并且帐号密码填入server_info字典中，注册网址http://ai.go129.com:8000/register，注册免开通直接使用。
                  每个帐号禁止并发连接，禁止重复登录，切记!







Go_Ai Agent极简说明
创建Agent
go_env = my_agent.My_Agent()

全新开始一局，传入Go_Ai位置,初始手牌env,三张地主牌env
go_env.new_game(go_ai_position,user_hand_cards_env,three_cards_env)

获取自己当前手牌内容，传入(env位置)，在Go_Ai中一个Agent可以同时扮演三个位置，所以获取自己当前手牌时需要传入位置。
my_cards = go_env.get_my_hand_cards(go_ai_position) 

兼容DouZero的Step,唯一区别要传入两个位置。传入(env位置，当前出牌位置，出牌动作内容env)
记录别家出牌时传入: (env位置，当前出牌位置，出牌动作内容env)
AI出牌时传入: (env位置，当前出牌位置，None)
action_message, action_list = go_env.step(go_ai_position, position=now_pos, action=action) 

检测对局是否结束,未结束返回False,结束返回最后出完的位置(landlord/landlord_down/landlord_up)，注意需传入env位置。
game_over = go_env.game_over(go_ai_position)
