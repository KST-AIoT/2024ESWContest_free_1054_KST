import logging
import asyncio
from gmqtt import Client as MQTTClient
import json
import tkinter as tk
import datetime


def update_request_time():
    """
    현재 시간을 요청 시간 형식으로 반환하는 함수
    """
    return datetime.datetime.now().strftime('%m%d%H%M%S')


frequencies = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 300, 400, 500, 600, 700, 800, 900,
               1000, 2000, 3000, 4000, 5000]
request_type = 1

# MQTT 관련 설정
MQTT_HOST = "54.180.165.1"
MQTT_PORT = 1883
DISPLAY_TOPIC = "KST/DISPLAY"
REQUEST_TOPIC = "KST/REQUEST"

# 윈도우 객체 생성 및 설정
window = tk.Tk()
window.geometry("800x600")
window.title("KST Nutrient Solution Analyzer")
window.configure(bg='#D3D3D3')  # 밝은 회색 배경

# 상태 표시용 레이블 - 폰트 및 색상 설정
status_label = tk.Label(window, text="Waiting...", font=("Helvetica", 24), fg="#4F4F4F", bg='#D3D3D3')  # 짙은 회색 텍스트
status_label.pack(pady=50)  # 레이블 배치

# 하단 설명 추가 - 폰트 크기 및 색상 조정
info_label = tk.Label(window, text="Monitoring the nutrient solution in real-time.", font=("Helvetica", 14),
                      fg="#696969", bg='#D3D3D3')
info_label.pack(pady=20)

# MQTT 클라이언트 변수
mqtt_client = None

# 분석 시작 버튼
start_button = tk.Button(window, text="Start Analysis", font=("Helvetica", 16), command=lambda: send_analysis_request())
start_button.place(x=300, y=400)  # 버튼 위치 조정

# Retry 버튼을 미리 정의하지만 숨김
retry_button = tk.Button(window, text="Retry", font=("Helvetica", 16), command=lambda: send_analysis_request())
retry_button.place(x=300, y=450)  # Retry 버튼 위치 조정 (아래에 위치)
retry_button.place_forget()  # 초기에는 숨김

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 상태에 따라 색상을 변경하는 함수
def update_status(message, color):
    status_label.config(text=message, fg=color)
    window.update_idletasks()


# 분석 요청을 보내는 함수
def send_analysis_request():
    global start_button, retry_button
    # request_time을 매번 새로 업데이트
    request_time = update_request_time()
    MESSAGE = {
        "frequencies": frequencies,
        "request_type": request_type,
        "request_time": request_time
    }

    # 버튼 비활성화
    start_button.config(state="disabled")
    start_button.place_forget()  # Start Analysis 버튼 숨기기

    retry_button.place_forget()  # Retry 버튼도 숨기기 (이전에 나와 있었다면)

    # MQTT로 요청 전송
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
    global status_label, start_button, retry_button
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
        irrigation_time_K = int(irrigation_times.get('K', 'N/A')) / 1000
        irrigation_time_N = int(irrigation_times.get('N', 'N/A')) / 1000
        irrigation_time_P = int(irrigation_times.get('P', 'N/A')) / 1000

        # 세로로 관개 시간 정보를 표시
        update_status(f"Analysis Complete.\n질산칼슘: {N} ppm\n제이인산암모늄: {P} ppm\n황산칼륨: {K} ppm\n\n\n"
                      f"Irrigation Times:\n"
                      f"질산칼슘: {irrigation_time_N} sec\n"
                      f"제이인산암모늄: {irrigation_time_P} sec\n"
                      f"황산칼륨: {irrigation_time_K} sec", "#4F4F4F")

        # 분석이 완료되면 Retry 버튼 표시 및 활성화
        retry_button.place(x=300, y=450)  # Retry 버튼 위치
        retry_button.config(state="normal")
    else:
        update_status("Unknown status", "red")
        retry_button.place(x=300, y=450)  # Retry 버튼 표시
        retry_button.config(state="normal")


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
