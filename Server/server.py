import logging
import asyncio
import os

from fastapi import FastAPI
from gmqtt import Client as MQTTClient
from contextlib import asynccontextmanager
import json
import numpy as np
import pandas as pd

from utils.portenta_data import portenta_data
from datetime import datetime
import random
import string

from AI_Model.CNN.predict_cnn import predict_dt
from AI_Model.CNN.CNN import CNN, CNN_LITE
import torch

from utils.irrigation_control import irrigation_control

obj_dict = {}  # 데이터 객체 저장용 딕셔너리 {id : 데이터}

app = FastAPI()  # FastAPI 애플리케이션 생성
logging.basicConfig(level=logging.INFO)  # 로그 레벨 설정
logger = logging.getLogger(__name__)  # 로거 설정

model_name = 'cnn_lite_model.pth'

# 현재 작업 디렉토리 얻기
current_dir = os.getcwd()
model_path = os.path.join(current_dir, 'AI_Model', 'CNN', model_name)

# CNN 모델 초기화 및 가중치 로드
model = CNN_LITE()
state_dict = torch.load(model_path, map_location=torch.device('cpu'), weights_only=True)
model.load_state_dict(state_dict)
model.eval()

MQTT_HOST = "HOST"
MQTT_PORT = 1883
KEEPALIVE = 60
MQTT_TOPIC = "KST/DATA"  # 예측 결과 데이터 발신 토픽
IRRIGATION_TOPIC = "KST/IRRIGATION"  # 관개 제어 발신 토픽
RESPONSE_TOPIC = "KST/REQUEST"  # 양액 분석 데이터 수신 토픽
DISPLAY_TOPIC = "KST/DISPLAY"  # 디스플레이, 디버그 용 발신 토픽
TIMEOUT_SECONDS = 30  # 타임아웃 시간 설정(30초)

mqtt_client = None  # MQTT 클라이언트 변수

message_received_event = asyncio.Event()  # 메시지 수신을 감지하는 이벤트

'''
정상적으로 MQTT 서버에 연결되었을 때 호출되는 함수
: KST/DATA 구독
'''


async def on_connect(client, flags, rc, properties):
    logger.info("Connected")
    client.subscribe(MQTT_TOPIC, qos=1)


'''
MQTT 브로커로부터 메시지를 수신했을 때 호출되는 함수
: 수신한 데이터에 대해 전처리 및 CNN 모델을 사용한 예측 수행
'''


async def on_message(client, topic, payload, qos, properties):
    message = payload.decode()
    data = json.loads(message)
    # 초기 데이터 저장
    req_time = str(data.get("req_time"))
    req_type = str(data.get("req_type"))  # 0: 학습용, 1: 추론용 데이터 구분
    frequencies = data.get("frequency")
    target_frequency = data.get("target_freq")
    logger.info(f"Received message on topic {topic}: {req_time, req_type, frequencies, target_frequency}")

    message_received_event.set()

    try:
        # JSON 형식의 메시지 파싱
        data = json.loads(message)

        # 초기 데이터 저장
        req_time = str(data.get("req_time"))
        req_type = str(data.get("req_type"))  # 0: 학습용, 1: 추론용 데이터 구분
        frequencies = data.get("frequency")
        target_frequency = data.get("target_freq")
        v_0 = data.get("v_0")
        v_1 = data.get("v_1")
        time = data.get("time")
        temperature = data.get("temperature")
        # resistance = data.get("resistance")
        resistance = 640  # 포텐셔미터 제작 보류로 인한 저항값 세팅

        # 구분용 client id
        client_id = req_time + '_' + req_type

        # 새로운 데이터 클라이언트가 오면 객체 생성, 기존 클라이언트면 추가
        if client_id not in obj_dict:
            client.publish(RESPONSE_TOPIC, json.dumps({"status": "0"}), qos=1)
            obj_dict[client_id] = portenta_data(req_time, req_type, frequencies)
        portenta_obj = obj_dict.get(client_id)

        # 데이터를 추가하고 완료 여부 확인
        result = portenta_obj.add_data(target_frequency, v_0, v_1, temperature, resistance, time)

        # 데이터가 모두 모이면 처리 시작
        if result:
            client.publish(RESPONSE_TOPIC, json.dumps({"status": "1"}), qos=1)
            # 데이터 저장
            final_freq = result[0]
            final_v0 = result[1]
            final_v1 = result[2]
            final_temperature = result[3]
            final_resistance = result[4]
            final_time = result[5]

            # 측정된 데이터를 통해 임피던스 계산
            final_magnitude, final_phase, final_source_voltage, fianl_water_voltage, final_resistance_voltage, final_circuit_current = portenta_obj.process_data()

            # req_type이 "1"일 때 (추론용 데이터 처리)
            if portenta_obj.req_type == "1":
                global model

                print(f"Complete data(1) for client_id {client_id}")

                # 원시 데이터(raw data)를 저장
                raw_filename = "./AI_Model/data/inference/" + client_id + "_rawdata.csv"
                df_raw = pd.DataFrame(final_freq, columns=['frequency'])
                df_raw['v_0'] = final_v0
                df_raw['v_1'] = final_v1
                df_raw['temperature'] = final_temperature
                df_raw['resistance'] = final_resistance
                df_raw['time'] = final_time
                df_raw.to_csv(raw_filename, index=False, mode='a')

                # 추론용 데이터를 저장할 파일 생성
                filename = "./AI_Model/data/inference/" + client_id + "_dataset.csv"

                # 데이터를 pandas DataFrame에 저장 후 CSV 파일로 저장
                df_test = pd.DataFrame(final_freq, columns=['frequency'])
                df_test['phase'] = final_phase
                df_test['magnitude'] = final_magnitude
                df_test.to_csv(filename, index=False, mode='a')

                # CNN 모델을 통해 예측 수행
                predict_label = predict_dt(model, filename)
                print("prediction success")  # 예측 성공 로그 출력
                # predict 정보를 바탕으로 관개(양액 농도 조절)
                irrigation_times = irrigation_control(predict_label)

                # client.publish(RESPONSE_TOPIC, json.dumps(irrigation_times), qos=1)

                client.publish(IRRIGATION_TOPIC, json.dumps({
                    "N": irrigation_times["N"],
                    "P": irrigation_times["P"],
                    "K": irrigation_times["K"]
                }))

                client.publish(DISPLAY_TOPIC, json.dumps({
                    "status": "2",
                    "N": predict_label["N"],
                    "P": predict_label["P"],
                    "K": predict_label["K"],
                    "irrigation_times": irrigation_times
                }))

                client.publish(RESPONSE_TOPIC, json.dumps(irrigation_times), qos=1)

            # req_type이 "0"일 때 (학습용 데이터 처리)
            elif portenta_obj.req_type == "0":
                print(f"Complete data(0) for client_id {client_id}")

                # 원시 데이터(raw data)를 저장
                raw_filename = "./AI_Model/data/" + client_id + "_rawdata.csv"
                df_raw = pd.DataFrame(final_freq, columns=['frequency'])
                df_raw['v_0'] = final_v0
                df_raw['v_1'] = final_v1
                df_raw['temperature'] = final_temperature
                df_raw['resistance'] = final_resistance
                df_raw['time'] = final_time
                df_raw.to_csv(raw_filename, index=False, mode='a')

                # 가공된 데이터 저장
                filename = "./AI_Model/data/" + client_id + "_dataset.csv"
                df = pd.DataFrame(final_freq, columns=['frequency'])
                df['phase'] = final_phase
                df['magnitude'] = final_magnitude
                df['temperature'] = final_temperature
                df['source_voltage'] = final_source_voltage
                df['water_voltage'] = fianl_water_voltage
                df['resistance_voltage'] = final_resistance_voltage
                df['circuit_current'] = final_circuit_current
                df.to_csv(filename, index=False, mode='a')
            del obj_dict[client_id]  # 데이터 처리가 완료된 객체는 삭제

    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        client.publish("KST/ERROR", json.dumps({"error": str(e)}), qos=1)


'''
MQTT클라이언트 초기화 및 연결
'''


async def start_mqtt_client():
    global mqtt_client
    mqtt_client = MQTTClient("client_id")  # MQTT 클라이언트 생성

    mqtt_client.on_connect = lambda *args: asyncio.create_task(on_connect(*args))  # 연결 시 on_connect 호출
    mqtt_client.on_message = lambda *args: asyncio.create_task(on_message(*args))  # 메시지 수신 시 on_message 호출

    try:
        await mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=KEEPALIVE)  # MQTT 서버에 연결
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")  # 연결 실패 시 예외 처리
        return None

    return mqtt_client


'''
메시지를 기다리는 함수 (타임아웃 설정)
'''


async def wait_for_message(timeout: int):
    try:
        # 타임아웃 설정
        await asyncio.wait_for(message_received_event.wait(), timeout)  # 타임아웃 시간 동안 메시지 대기
        logger.info("Message received within timeout.")  # 메시지를 정상적으로 수신한 경우
        # mqtt_client.publish(RESPONSE_TOPIC, "Received success", qos=1)  # 성공 메시지 전송
    except asyncio.TimeoutError:
        logger.warning(f"No message received in {timeout} seconds, sending alert message.")  # 타임아웃 발생 시 로그 출력
        # await send_alert_message()


'''
타임아웃 시 발행할 메시지
'''


async def send_alert_message():
    for client_id, portenta_obj in obj_dict.items():
        time_diff = datetime.now() - portenta_obj.last_edit_time
        if time_diff.total_seconds() > TIMEOUT_SECONDS:
            mqtt_client.publish(RESPONSE_TOPIC, json.dumps(
                {"request_time": portenta_obj.req_time, "request_type": portenta_obj.req_type,
                 "frequencies": portenta_obj.frequencies_list}), qos=1)
        logger.info(f"Alert message sent: {client_id}")


'''
Lifespan 이벤트 핸들러: FastAPI 애플리케이션 시작 및 종료 시 실행되는 비동기 컨텍스트 매니저
'''


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_mqtt_client()  # 서버 시작 시 MQTT 클라이언트 연결
    yield  # 서버가 실행 중일 때 여기서 멈춤
    await mqtt_client.disconnect()  # 서버 종료 시 MQTT 클라이언트 연결 해제


app.router.lifespan_context = lifespan  # 시작과 종료시점 제어

'''
실행
'''


async def main():
    await start_mqtt_client()
    while True:
        # 이벤트 초기화
        message_received_event.clear()

        # 메시지를 5초 동안 기다림
        await wait_for_message(TIMEOUT_SECONDS)

        # 다음 메시지를 기다리기 전에 잠시 대기
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
