"""
Author: Vincent Young
Date: 2023-04-27 00:44:01
LastEditors: Vincent Young
LastEditTime: 2023-05-21 03:58:18
FilePath: /PyDeepLX/PyDeepLX/PyDeepLX.py
Telegram: https://t.me/missuo

Copyright © 2023 by Vincent, All Rights Reserved. 
"""
import random
import time
import json
import httpx
import threading
import os

deeplAPI = "https://www2.deepl.com/jsonrpc"
headers = {
    "Content-Type": "application/json",
    "Accept": "*/*",
    "x-app-os-name": "iOS",
    "x-app-os-version": "16.3.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "x-app-device": "iPhone13,2",
    "User-Agent": "DeepL-iOS/2.9.1 iOS 16.3.0 (iPhone13,2)",
    "x-app-build": "510265",
    "x-app-version": "2.9.1",
    "Connection": "keep-alive",
}

class TooManyRequestsException(Exception):
    "Raised when there is a 429 error"
    def __str__(self):
        return "PyDeepLX Error: Too many requests, your IP has been blocked by DeepL temporarily, please don't request it frequently in a short time."

def getICount(translateText) -> int:
    return translateText.count("i")

def getRandomNumber() -> int:
    random.seed(time.time())
    num = random.randint(8300000, 8399998)
    return num * 1000

def getTimestamp(iCount: int) -> int:
    ts = int(time.time() * 1000)
    if iCount == 0:
        return ts
    iCount += 1
    return ts - ts % iCount + iCount

lock = threading.Lock()
delay = 1
max_delay = 60

def update_delay(error_condition):
    global delay
    with lock:
        if error_condition in error_conditions:
            delay = min(delay * 2, max_delay)
        else:
            error_conditions.append(error_condition)
            with open("error_conditions.txt", "a") as f:
                f.write(f"{error_condition}\n")

def translate(
    text,
    sourceLang="auto",
    targetLang="en",
    numberAlternative=0,
    printResult=False,
    proxies=None,
):
    global delay
    iCount = getICount(text)
    id = getRandomNumber()
    numberAlternative = max(min(3, numberAlternative), 0)
    postData = {
        "jsonrpc": "2.0",
        "method": "LMT_handle_texts",
        "id": id,
        "params": {
            "texts": [{"text": text, "requestAlternatives": numberAlternative}],
            "splitting": "newlines",
            "lang": {
                "source_lang_user_selected": sourceLang,
                "target_lang": targetLang,
            },
            "timestamp": getTimestamp(iCount),
            "commonJobParams": {
                "wasSpoken": False,
                "transcribe_as": "",
            },
        },
    }
    postDataStr = json.dumps(postData, ensure_ascii=False)
    if (id + 5) % 29 == 0 or (id + 3) % 13 == 0:
        postDataStr = postDataStr.replace('"method":"', '"method" : "', -1)
    else:
        postDataStr = postDataStr.replace('"method":"', '"method": "', -1)
    while True:
        try:
            with httpx.Client(proxies=proxies) as client:
                resp = client.post(url=deeplAPI, data=postDataStr, headers=headers)
                respStatusCode = resp.status_code
                if respStatusCode == 429:
                    raise TooManyRequestsException
                if respStatusCode != 200:
                    print("Error", respStatusCode)
                    return
                respText = resp.text
                respJson = json.loads(respText)
                if numberAlternative <= 1:
                    targetText = respJson["result"]["texts"][0]["text"]
                    if printResult:
                        print(targetText)
                    return targetText
                targetTextArray = []
                for item in respJson["result"]["texts"][0]["alternatives"]:
                    targetTextArray.append(item["text"])
                    if printResult:
                        print(item["text"])
                return targetTextArray
        except TooManyRequestsException:
            error_condition = f"Delay: {delay}, Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            update_delay(error_condition)
            print(f"429 error occurred. Retrying in {delay} seconds...")
            time.sleep(delay)

if __name__ == "__main__":
    if os.path.exists("error_conditions.txt"):
        with open("error_conditions.txt", "r") as f:
            error_conditions = f.read().splitlines()
    else:
        error_conditions = []


# Example Call
# translate("明天你好", "ZH", "EN", True, True, "socks5://127.0.0.1:7890")
# translate("明天你好", "ZH", "EN", 3, True)
