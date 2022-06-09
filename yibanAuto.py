#!/usr/local/bin/python3
import datetime
import json
import time
import pandas as pd
import pymysql
import pymssql
from sqlalchemy import create_engine
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service



class YiBanHelper:
    def __init__(self, **args):
        # 使用用户名或密码或者cookie初始化,优先使用cookie
        assert ('phpsessid' and 'csrf_token' in args.keys()) or ('username' and 'password' in args.keys()), "参数错误"
        # 初始化未完成的任务
        self.uncompletedTasks = None
        # self.wf_id = ""
        if 'phpsessid' and 'csrf_token' in args.keys():
            self.cookie = {"phpsessid": args.get('phpsessid'), "csrf_token": args.get('csrf_token')}
            return
        elif 'username' and 'password' in args.keys():
            # 添加chrome的参数
            option = webdriver.ChromeOptions()
            # 使用无头模式
            option.add_argument('--headless')
            # 禁用GPU
            option.add_argument('--no-sandbox')
            option.add_argument('--disable-gpu')
            option.add_argument('--disable-dev-shm-usage')
            # 添加请求头，这一项很重要
            option.add_argument(
                'user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, '
                'like Gecko) '
                'Mobile/15E148 yiban_iOS/5.0')

            # 或者  使用下面的设置, 提升速度
            option.add_argument('blink-settings=imagesEnabled=false')
            # 版本匹配
            option.add_experimental_option("detach", True)
            driver = webdriver.Chrome(executable_path="C:Users/15364/Desktop/Fast/chromedriver.exe", options=option)
            driver.get("https://c.uyiban.com/#/")
            # 等待出现指定的元素，最多等待10s
            WebDriverWait(driver, 50).until(
                lambda d: d.find_element(By.ID, "oauth_uname_w"))

            un = driver.find_element(By.ID, "oauth_uname_w")
            # 填写用户名和密码，点击登陆按钮
            un.send_keys(args.get('username'))
            password = driver.find_element(By.ID, "oauth_upwd_w")
            password.send_keys(args.get('password'))
            btn = driver.find_element(By.CSS_SELECTOR, "button.oauth_check_login")
            btn.click()
            # 等待页面跳转完成
            WebDriverWait(driver, 30).until(
                lambda d: str(driver.current_url).startswith("https://c.uyiban.com")
            )
            # 稍稍等待1s,目的是等待页面的js执行完成，cookie才能正确的更新
            time.sleep(10)
            # 获取cookie
            phpsessid = driver.get_cookie("PHPSESSID").get('value')
            token = driver.get_cookie("csrf_token").get('value')
            self.cookie = {"phpsessid": phpsessid, "csrf_token": token}
            if args.pop("show_cookie", False):
                print("PHPSESSID的值是: " + phpsessid)
                print("CSRF_TOKEN的值是: " + token)
            driver.close()

    # 查询未完成的任务
    def query_completed_tasks(self, **args):
        assert 'phpsessid' and 'csrf_token' in self.cookie
        today = datetime.date.today()
        tomorrow = str(today + datetime.timedelta(days=1))
        before = str(today - datetime.timedelta(days=14))
        # 向接口发送请求
        res = requests.get("https://api.uyiban.com/officeTask/client/index/uncompletedList",
                           params={"StartTime": args.pop("start_time", before),
                                   "EndTime": args.pop("end_time", tomorrow),
                                   "CSRF": self.cookie.get('csrf_token')},
                           cookies={"PHPSESSID": self.cookie.get('phpsessid'),
                                    "csrf_token": self.cookie.get('csrf_token')},
                           headers={"Origin": "https://app.uyiban.com",
                                    "User-Agent": 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS '
                                                  'X) AppleWebKit/605.1.15 (KHTML, '
                                                  'like Gecko) '
                                                  'Mobile/15E148 yiban_iOS/5.0'})

        # 尝试将结果json化
        try:
            result = json.loads(res.text)
            if result.get("code") == 0:
                self.uncompletedTasks = result.get('data')
            if result.get('code') == 999:
                print("登陆失败")
                # 下面这个是为了在提交信息的时候报错
                self.uncompletedTasks = []
        except ValueError:
            print("Cookies或许出现错误, 可能需要重新获取Cookie")

    # 提交任务，info是个人的日报信息，extend会自动生成
    def submit_task(self,info: dict = None, **kwargs):
        assert 'wf_id' and "auto_wf_id" in kwargs, "缺少工作流ID"
        # 首先查询完成的信息，初始化必要的参数
        self.query_completed_tasks(**kwargs)
        if len(self.uncompletedTasks) == 0:
            print("没有需要完成任务")
            return
        for task in self.uncompletedTasks:
            start_time = task.get('StartTime')
            if int(time.time()) < int(start_time):
                print("任务尚未开始")
                continue
            else:
                task_id = task.get('TaskId')
                task_title = task.get("Title")
                extent = {
                    "TaskId": task_id,
                    "title": "任务信息",
                    "content": [{"label": "任务名称", "value": task_title}, {
                        "label": "发布机构", "value": "学生工作处"
                    }]
                }
                print("任务id: " + task_id)
                data = f"data={quote(json.dumps(info))}&extend={quote(json.dumps(extent))}"
                wf_id = ""
                if 'wf_id' in kwargs:
                    wf_id = kwargs.get("wf_id")
                elif kwargs.get('auto_wf_id'):
                    wf_id = self.get_task_wf_id(task_id=task_id)
                else:
                    raise ValueError("未初始化WF_ID")
                # print("测试：\n" + requests.post("https://api.uyiban.com/workFlow/c/my/apply/" + wf_id))
                result = requests.post("https://api.uyiban.com/workFlow/c/my/apply/" + wf_id,
                                       params={"CSRF": self.cookie.get("csrf_token")},
                                       headers={"Origin": "https://app.uyiban.com",
                                                "Content-Type": "application/x-www-form-urlencoded",
                                                "sec-ch-ua": "",
                                                "sec-ch-ua-mobile": "?1",
                                                "User-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS "
                                                              "X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
                                                              "Mobile/15E148 yiban_iOS/5.0",
                                                "Sec-Fetch-Site": "same-site",
                                                "Sec-Fetch-Mode": "cors",
                                                "Sec-Fetch-Dest": "empty",
                                                "Referer": "https://app.uyiban.com/",
                                                "Accept-Encoding": "gzip, deflate, br",
                                                "Accept-Language": "zh-CN,zh;q=0.9"},
                                       cookies={"PHPSESSID": self.cookie.get('phpsessid'),
                                                "csrf_token": self.cookie.get('csrf_token')},
                                       data=kwargs.get('cookie'),
                                       )

                if result.json().get('data') != '':
                    print("提交反馈:", result.json())

    # 获取任务id
    def get_task_wf_id(self, task_id: str):
        # requests.DEFAULT_RETRIES = 5
        res = requests.get("https://api.uyiban.com/officeTask/client/index/detail?TaskId=" + task_id,
                           params={"CSRF": self.cookie.get('csrf_token')},
                           cookies={"PHPSESSID": self.cookie.get('phpsessid'),
                                    "csrf_token": self.cookie.get('csrf_token')},
                           headers={"Origin": "https://app.uyiban.com",
                                    "User-Agent": 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS '
                                                  'X) AppleWebKit/605.1.15 (KHTML, '
                                                  'like Gecko) '
                                                  'Mobile/15E148 yiban_iOS/5.0'})
        res_json = res.json()
        if res_json.get('code') == 0:
            return res_json.get('data').get('WFId')
        else:
            raise ValueError("没有成功的获取到返回结果")


def do_task(id,username,password,cookie):
    # with open("user.json", 'r', encoding='utf8') as f:
    #     users = json.load(f)
    #     infos = users.get("userInfos")
    #     for user in range(1,10):
            print("当前用户:", id)
            # print("pasword = " + password,"username = " + username,"cookie = " + cookie )
            yiban = YiBanHelper(password=password, username=username, show_cookie=True)
            # person_info = user.get("dataJson")
            # print(person_info)
            yiban.submit_task(info="", auto_wf_id=True , cookie = cookie)

        # Press the green button in the gutter to run the script.
def datebase():
    con = pymysql.connect(host='sh-cynosdbmysql-grp-e9bo3jzs.sql.tencentcdb.com', port=29049, user='admin', passwd='ABC123!@#', db='yiban', charset='utf8')
    cursor = con.cursor()

    ###getCookie
    sqlcookie = "SELECT cookie FROM cookie where id = 1"
    cursor.execute(sqlcookie)
    cookie = cursor.fetchone()
    cookie = str(cookie)[2:-2]
    print(cookie)


    for id in range (1,100)  :
        ###userID
        sql1 = "SELECT userID FROM user where id=" + str(id)
        cursor.execute(sql1)
        # 获得列名
        column = [col[0] for col in cursor.description]
        # 获得数据
        userID = cursor.fetchone()
        # userID = json.dump(userID)
     # 获得DataFrame格式的数据
        data_df = pd.DataFrame(list(userID), columns=column)
        print(data_df)
        data_df.describe()


        ###password
        sql2 = "SELECT password FROM user where id=" + str(id)
        cursor.execute(sql2)
        # 获得列名
        column = [col[0] for col in cursor.description]
        # 获得数据
        password = cursor.fetchone()
        # password = json.dump(password)
        # 获得DataFrame格式的数据
        data_df = pd.DataFrame(list(password), columns=column)
        print(data_df)
        data_df.describe()

        ##传入账密、cookie
        do_task(id,userID,password,cookie)

if __name__ == '__main__':
    datebase()

