import socket
import urllib.request
import urllib.parse
import urllib.error
import json


class Http_Client:
    def __init__(self, base_url: str, timeout: int = 30):
        # base_url 直接是完整根地址, 如 https://www.tulingyun.com
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def _send_request(self, url: str, method: str = 'GET', data: dict = None) -> dict:
        try:
            post_data = None
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
            }

            if data and method == 'POST':
                post_data = json.dumps(data).encode('utf-8')

            request = urllib.request.Request(url, data=post_data, headers=headers, method=method)
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                content = response.read()
                try:
                    raw_data = content.decode('utf-8')
                except UnicodeDecodeError:
                    raw_data = content.decode('gb18030')
                return json.loads(raw_data)

        except urllib.error.HTTPError as e:
            # 图灵失败时返回 HTTP 状态码 + 提示 + request_id, 尽量解析出来
            try:
                body = json.loads(e.read().decode('utf-8'))
            except Exception:
                body = {'message': str(e)}
            return {'status': e.code, 'message': body.get('message', str(e))}
        except urllib.error.URLError as e:
            return {'status': -1, 'message': f'URL错误: {str(e)}'}
        except socket.timeout:
            return {'status': -1, 'message': '请求超时'}
        except json.JSONDecodeError:
            return {'status': -1, 'message': '返回非JSON', 'raw': raw_data}
        except Exception as e:
            return {'status': -1, 'message': f'未知错误: {str(e)}'}

    def get(self, path: str, params: dict = None) -> dict:
        url = self.base_url + path
        if params:
            url += '?' + urllib.parse.urlencode(params)
        return self._send_request(url, 'GET')

    def post(self, path: str, data: dict = None) -> dict:
        url = self.base_url + path
        return self._send_request(url, 'POST', data)