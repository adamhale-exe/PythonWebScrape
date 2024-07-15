import requests
from bs4 import BeautifulSoup
import credentials

loginurl = ('https://login.mercedes-benz.com/')
secureurl = ('https://the-internet.herokuapp.com/secure')

payload = {
    '_csrf': '8o2Rt34vn9idR9zu8Ro5s90ZJcRvyZXdrV3Y31QcmjxU5CNNxLqkgk9MqOCwceqLkDcNgOR6CP0OqqHwlW-87TUvrARn0kUo',
    'username': credentials.username,
    'password': credentials.password,
    'password-encrypted': 'M/AxJE/PfVo/2gwU2AhUPKOJQ9XjK/HJu+XY2fnzme1UkNliyTRAYFw49rgVZmDT4WMTAVNb10Q2XPTCto8/TJIqKI7wX5mOThOC30+4Bwzfeg/rbg6MES1Qi3CaoQg74Cjj9/eV2xx4B7l0gkPzKnDscZY0x+grbI0k5yH4Pi+sNNneiehfq6fXaKEr3Gglk7WB/tlrlBfi4Cb6Cn6GCUoKEeEQPsyRlvVoof4b5N7yVieuW+e88FUh05Ap06IRnZJAry7MdtzZhP+4OiHyrlnfl+uMPYnwIsCpQYvxv2cv8E0+2lUOehNmyusHrEs0v/wYk3mncBRN9LW31zl7gg=='
}

with requests.session() as s:
    s.post(loginurl, data=payload)
    r = s.get(secureurl)
    soup = BeautifulSoup(r.content, 'html.parser')
    print(soup.prettify())