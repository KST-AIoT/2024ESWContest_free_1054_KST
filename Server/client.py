import logging
import asyncio
from gmqtt import Client as MQTTClient
import json
import tkinter as tk
import datetime

request_time = datetime.datetime.now().strftime('%m%d%H%M%S')
frequencies = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 300, 400, 500, 600, 700, 800, 900,
               1000, 2000, 3000, 4000, 5000]
request_type = 1
MESSAGE = {
    "frequencies": frequencies,
    "request_type": request_type,
    "request_time": request_time
}

# UI를 표시하기 위한 토픽 설정
MQTT_HOST = "54.180.165.1"
MQTT_PORT = 1883
DISPLAY_TOPIC = "KST/DISPLAY"
REQUEST_TOPIC = "KST/REQUEST"

# 윈도우 객체 생성 및 설정
window = tk.Tk()
window.geometry("800x600")
window.title("KST Nutrient Solution Analyzer")

# 회색 계열로 창 배경 색상 설정
window.configure(bg='#D3D3D3')  # 밝은 회색 배경

# 상태 표시용 레이블 - 폰트 및 색상 설정
status_label = tk.Label(window, text="Waiting...", font=("Helvetica", 24), fg="#4F4F4F", bg='#D3D3D3')  # 짙은 회색 텍스트
status_label.pack(pady=50)  # 레이블 배치

# 하단 설명 추가 - 폰트 크기 및 색상 조정
info_label = tk.Label(window, text="Monitoring the nutrient solution in real-time.", font=("Helvetica", 14), fg="#696969", bg='#D3D3D3')
info_label.pack(pady=20)

# MQTT 클라이언트 변수
mqtt_client = None

# 분석 시작 버튼
start_button = tk.Button(window, text="Start Analysis", font=("Helvetica", 16), command=lambda: send_analysis_request())
start_button.place(x=300, y=400)  # 버튼 위치 조정

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 상태에 따라 색상을 변경하는 함수
def update_status(message, color):
    status_label.config(text=message, fg=color)
    window.update_idletasks()

# 분석 요청을 보내는 함수
def send_analysis_request():
    global start_button
    start_button.config(state="disabled")  # 버튼 비활성화
    start_button.place_forget()  # 버튼 숨기기
    mqtt_client.publish(REQUEST_TOPIC, json.dumps(MESSAGE), qos=1)
    update_status("Analysis Started...", "#4F4F4F")

'''
MQTT 서버에 연결되었을 때 호출되는 함수
'''
async def on_connect(client, flags, rc, properties):
    logger.info("Connected to MQTT server")
    client.subscribe(DISPLAY_TOPIC, qos=1)  # KST/DISPLAY 토픽 구독

'''
KST/DISPLAY 토픽에서 메시지를 수신할 때 호출되는 함수
'''
async def on_message(client, topic, payload, qos, properties):
    global status_label, start_button
    message = payload.decode()
    print(message)

    try:
        data = json.loads(message)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        return
    
    status = data.get('status')

    # 상태에 따라 메시지 및 색상 변경
    if status == "0":
        update_status("Measuring...", "#4F4F4F")  
    elif status == "1":
        update_status("Measurement Complete. Analyzing...", "#4F4F4F")  
    elif status == "2":
        K = str(data.get('K'))
        N = str(data.get('N'))
        P = str(data.get('P'))
        irrigation_times = data.get('irrigation_times', {})
        irrigation_time_K = irrigation_times.get('K', 'N/A')
        irrigation_time_N = irrigation_times.get('N', 'N/A')
        irrigation_time_P = irrigation_times.get('P', 'N/A')
        update_status(f"Analysis Complete.\nK: {K} ppm\nN: {N} ppm\nP: {P} ppm\n"
                      f"Irrigation time - K: {irrigation_time_K} sec, N: {irrigation_time_N} sec, P: {irrigation_time_P} sec", 
                      "#4F4F4F")
        start_button.place(x=300, y=400)  # 버튼 다시 표시
        start_button.config(state="normal")  # 분석이 완료되면 버튼을 다시 활성화
    else:
        update_status("Unknown status", "red") 
        start_button.place(x=300, y=400)  # 버튼 다시 표시
        start_button.config(state="normal")  # 분석이 완료되면 버튼을 다시 활성화

'''
MQTT 클라이언트 초기화 및 연결 함수
'''
async def start_mqtt_client():
    global mqtt_client
    mqtt_client = MQTTClient("display_client")  # MQTT 클라이언트 생성

    mqtt_client.on_connect = lambda *args: asyncio.create_task(on_connect(*args))
    mqtt_client.on_message = lambda *args: asyncio.create_task(on_message(*args))

    try:
        await mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)  # MQTT 서버에 연결
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")

    return mqtt_client

'''
Tkinter의 메인 이벤트 루프를 처리하면서 asyncio 이벤트 루프도 처리하는 함수
'''
async def tkinter_mainloop():
    while True:
        window.update()  # Tkinter 이벤트 처리
        await asyncio.sleep(0.01)  # asyncio 이벤트 루프와 Tkinter를 함께 실행

'''
메인 실행 함수 (asyncio)
'''
async def main():
    await start_mqtt_client()
    await tkinter_mainloop()  # Tkinter 메인 루프와 asyncio 이벤트 루프를 함께 실행

if __name__ == "__main__":
    asyncio.run(main())
