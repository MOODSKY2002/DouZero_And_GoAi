import socket
import urllib.request
import urllib.parse
import urllib.error
import json

class Http_Client:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def _send_request(self, url: str, method: str = 'GET', data: dict = None) -> dict:
        """发送请求并返回结果"""
        try:
            post_data = None
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                       'Accept': 'application/json',
                       'Content-Type': 'application/json',
                       'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                       'Connection': 'keep-alive'}

            if data and method == 'POST':  # 处理POST数据
                post_data = json.dumps(data).encode('utf-8')

            request = urllib.request.Request(url, data=post_data, headers=headers, method=method)  # 创建请求
            with urllib.request.urlopen(request, timeout=self.timeout) as response:                # 发送请求
                content = response.read()                         # 尝试不同的编码方式解析
                try:
                    raw_data = content.decode('gb2312')           # GB2312
                except UnicodeDecodeError:
                    try:
                        raw_data = content.decode('gbk')          # GBK
                    except UnicodeDecodeError:
                        try:
                            raw_data = content.decode('utf-8')    # UTF-8
                        except UnicodeDecodeError:
                            raw_data = content.decode('gb18030')  # GB18030

                return json.loads(raw_data)

        except urllib.error.URLError as e:
            return {'error': f'URL错误: {str(e)}'}
        except socket.timeout:
            return {'error': '请求超时'}
        except json.JSONDecodeError:
            return {'type':'text','data:':raw_data}
        except Exception as e:
            return {'error': f'未知错误: {str(e)}'}

    def get(self, path: str, params: dict = None) -> dict:
        """发送GET请求"""
        url = self.base_url + path  # 构建URL
        if params:
            url += '?' + urllib.parse.urlencode(params)
        return self._send_request(url, 'GET')

    def post(self, path: str, data: dict = None) -> dict:
        """发送POST请求"""
        url = self.base_url + path
        return self._send_request(url, 'POST', data)
