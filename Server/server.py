import logging
import asyncio
from fastapi import FastAPI
from gmqtt import Client as MQTTClient
from contextlib import asynccontextmanager
import json
import numpy as np
import pandas as pd
from portenta_data import portenta_data
from datetime import datetime
import random
import string

from AI_Model.CNN.predict_cnn import predict_dt


obj_dict = {} #id : 데이터 
app = FastAPI()
logging.basicConfig(level=logging.INFO)  # 로그 레벨 설정
logger = logging.getLogger(__name__)

MQTT_HOST = "54.180.165.1"
MQTT_PORT = 1883
KEEPALIVE = 60
MQTT_TOPIC = "KST/DATA"
RESPONSE_TOPIC = "KST/REQUEST"
TIMEOUT_SECONDS = 30  #초
count = 1

mqtt_client = None

message_received_event = asyncio.Event()
'''
정상 연결 시 호출되는 콜백 함수
: MQTT TOPIC 구독
'''
async def on_connect(client, flags, rc, properties):
    logger.info("Connected")
    client.subscribe(MQTT_TOPIC, qos=1)


'''
브로커로부터 메시지를 수신했을 때 호출되는 콜백 함수 
KST/request 
KST/DATA
: kingo/response 주제로 "ok"메시지 발행
'''
async def on_message(client, topic, payload, qos, properties):
    message = payload.decode()
    logger.info(f"Received message on topic {topic}: {message}")

    message_received_event.set()

    try:
        data = json.loads(message)    

        #초기 데이터 저장
        req_time = str(data.get("req_time"))
        req_type = str(data.get("req_type")) #0이면 학습용 1이면 추론용   
        frequencies = data.get("frequency")
        target_frequency = data.get("target_freq")
        v_0 = data.get("v_0")
        v_1 = data.get("v_1")
        time = data.get("time")
        temperature = data.get("temperature")
        resistance = data.get("resistance")
        client_id = req_time + '_' + req_type



        #아이디 확인해서 이미 존재하면 데이터 넣기 / 존재하지 않으면 새로운 객체 생성 후 데이터 넣기
        if client_id not in obj_dict:
            #존재하지 않으면
            obj_dict[client_id] = portenta_data(req_time, req_type, frequencies)
        portenta_obj = portenta_obj = obj_dict.get(client_id)
        result = portenta_obj.add_data(target_frequency, v_0, v_1, temperature, resistance, time)


        #끝까지 처리 완료 -> json(raw데이터) / 처리 완료 X -> None
        if result:
            #데이터 저장
            final_freq = result[0]
            final_v0 = result[1]
            final_v1 = result[2]
            final_temperature = result[3]
            final_resistance = 103.3 #todo: 저항값 변환하기
            #final_resistance = result[4]
            final_time = result[5]

            #데이터 처리
            final_magnitude, final_phase, final_source_voltage, fianl_water_voltage, final_resistance_voltage, final_circuit_current = portenta_obj.process_data()
            if portenta_obj.req_type == "1":
                print(f"Complete data(1) for client_id {client_id}: {result}")
                filename = "../data/inference/"
                for i in range(10):
                    filename = filename + str(random.choice(string.ascii_uppercase))
                filename = filename + ".csv"
                
                df_test = pd.DataFrame(final_freq, columns=['frequency'])
                df_test['phase'] = final_phase
                df_test['magnitude'] = final_magnitude

                df_test.to_csv(filename, index=False, mode='a')

                predict_label = predict_dt(filename)
                #예측 수행 : CNN(분류)
                print("prediction_suc")
                client.publish(RESPONSE_TOPIC, json.dumps({"prediction":predict_label}), qos=1)

            elif portenta_obj.req_type == "0":
                print(f"Complete data(0) for client_id {client_id}")

                #raw 데이터 저장
                #raw_filename = "./AI_Model/data/" + client_id + "_rawdata.csv"
                raw_filename = "./AI_Model/data/rawdata" + count + ".csv" #todo
                df_raw = pd.DataFrame(final_freq, columns=['frequency'])
                df_raw['v_0'] = final_v0
                df_raw['v_1'] = final_v1
                df_raw['temperature'] = final_temperature
                df_raw['resistance'] = final_resistance
                df_raw['time'] = final_time
                df_raw.to_csv(raw_filename, index=False, mode='a')


                #가공된 데이터 저장
                #filename = "./AI_Model/data/" + client_id + "_dataset.csv"
                filename = "./AI_Model/data/dataset" + count + ".csv" #todo
                df = pd.DataFrame(final_freq, columns=['frequency'])
                df['phase'] = final_phase
                df['magnitude'] = final_magnitude
                df['temperature'] = final_temperature
                df['source_voltage'] = final_source_voltage
                df['water_voltage'] = fianl_water_voltage
                df['resistance_voltage'] = final_resistance_voltage
                df['circuit_current'] = final_circuit_current

                df.to_csv(filename, index=False, mode='a')
                count += 1
            del obj_dict[client_id] # 데이터 처리가 완료되었으므로 객체 삭제

    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        client.publish("kingo/response", json.dumps({"error": str(e)}), qos=1)
'''
MQTT클라이언트 초기화 및 연결
'''
async def start_mqtt_client():
    global mqtt_client
    mqtt_client = MQTTClient("client_id")

    mqtt_client.on_connect = lambda *args: asyncio.create_task(on_connect(*args))
    mqtt_client.on_message = lambda *args: asyncio.create_task(on_message(*args))

    try:
        await mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=KEEPALIVE)
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")
        return None

    return mqtt_client

'''
메시지를 기다리는 함수
'''
async def wait_for_message(timeout: int):
    try:
        # 타임아웃 설정
        await asyncio.wait_for(message_received_event.wait(), timeout)
        logger.info("Message received within timeout.")
        mqtt_client.publish(RESPONSE_TOPIC, "Received success", qos=1)
    except asyncio.TimeoutError:
        logger.warning(f"No message received in {timeout} seconds, sending alert message.")
        await send_alert_message()

'''
타임아웃 시 발행할 메시지
'''
async def send_alert_message():
    for client_id, portenta_obj in obj_dict.items():
        time_diff = datetime.now() - portenta_obj.last_edit_time
        if time_diff.total_seconds() > TIMEOUT_SECONDS:
            mqtt_client.publish(RESPONSE_TOPIC, json.dumps({"request_time": portenta_obj.req_time, "request_type": portenta_obj.req_type, "frequencies": portenta_obj.frequencies_list}), qos=1)
        logger.info(f"Alert message sent: {client_id}")


'''
Lifespan 이벤트 핸들러
: FastAPI 애플리케이션의 시작과 종료 시 특정 작업을 수행하기 위해 사용하는 비동기 컨텍스트 매니저
'''
@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_mqtt_client()  # 서버 시작 시 MQTT 클라이언트 연결
    yield  # 서버가 실행 중일 때 여기서 멈춤
    await mqtt_client.disconnect()  # 서버 종료 시 MQTT 클라이언트 연결 해제

app.router.lifespan_context = lifespan #시작과 종료시점 제어

'''
HTTP GET: root('/')
'''
@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI with MQTT"}

'''
HTTP GET: ('/publish')
요청 들어오면 "Triggered by Server" 메시지를 kingo/response로 발행
메시지가 발행되었다는 상태 반환
'''
@app.get("/publish")
async def publish_message():
    mqtt_client.publish("kingo/response", "Triggered by Server", qos=1)
    return {"status": "Message published"}

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

'''
테스트
curl http://127.0.0.1:8000/publish
mosquitto_sub -h 54.180.165.1 -t kingo/response

-- type: 0 --
mosquitto_pub -h 54.180.165.1 -t KST/request -m "{\"req_time\": \"2024-09-01\", \"req_type\": 0, \"frequencies\": [100, 200], \"target_frequency\": 100, \"v_0\": [1.0, 2.0, 3.0, 4.0], \"v_1\": [1.1, 2.1, 3.1, 4.1], \"times\": 1000, \"temperatures\": 25, \"resistances\": 10}"


mosquitto_pub -h 54.180.165.1 -t KST/request -m "{\"req_time\": \"2024-09-01\", \"req_type\": 0, \"frequencies\": [100, 200], \"target_frequency\": 200, \"v_0\": [1.0, 2.0, 3.0, 4.0], \"v_1\": [1.1, 2.1, 3.1, 4.1], \"times\": 2000, \"temperatures\": 26, \"resistances\": 20}"


-- type: 1 --
mosquitto_pub -h 54.180.165.1 -t KST/request -m "{\"req_time\": \"2024-09-01\", \"req_type\": 1, \"frequencies\": [100, 200], \"target_frequency\": 100, \"v_0\": [1.0, 2.0, 3.0, 4.0], \"v_1\": [1.1, 2.1, 3.1, 4.1], \"times\": 1000, \"temperatures\": 25, \"resistances\": 10}"


mosquitto_pub -h 54.180.165.1 -t KST/request -m "{\"req_time\": \"2024-09-01\", \"req_type\": 1, \"frequencies\": [100, 200], \"target_frequency\": 200, \"v_0\": [1.0, 2.0, 3.0, 4.0], \"v_1\": [1.1, 2.1, 3.1, 4.1], \"times\": 2000, \"temperatures\": 26, \"resistances\": 20}"


'''