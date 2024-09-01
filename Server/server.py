import logging
import asyncio
from fastapi import FastAPI
from gmqtt import Client as MQTTClient
from contextlib import asynccontextmanager
import json
import numpy as np
import pandas as pd
from portenta_data import portenta_data
from calculate_impedance import calculate_impedance
from process_and_process import process_and_predict

from AI_Model.RandomForest.predict_model import predict_rf

obj_dict = {} #id : 데이터 

app = FastAPI()
logging.basicConfig(level=logging.INFO)  # 로그 레벨 설정
logger = logging.getLogger(__name__)

MQTT_HOST = "54.180.165.1"
MQTT_PORT = 1883
KEEPALIVE = 60
MQTT_TOPIC = "KST/request"

mqtt_client = None

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

    try:
        data = json.loads(message)    
        req_time = str(data.get("req_time"))
        req_type = str(data.get("req_type")) #0이면 학습용 1이면 추론용   
        frequencies = data.get("frequencies")
        target_frequency = data.get("target_frequency")
        v_0 = data.get("v_0")
        v_1 = data.get("v_1")
        time = data.get("times")
        temperature = data.get("temperatures")
        resistance = data.get("resistances")
        client_id = req_time + '_' + req_type

        #아이디 확인해서 이미 존재하면 데이터 넣기 / 존재하지 않으면 새로운 객체 생성
        if client_id in obj_dict:
            #이미 존재하면
            portenta_obj = obj_dict.get(client_id)
            result = portenta_obj.add_data(target_frequency, v_0, v_1, temperature, resistance, time)
        else:
            #존재하지 않으면
            obj_dict[client_id] = portenta_data(req_time, req_type, frequencies)
            portenta_obj = obj_dict[client_id]
            result = portenta_obj.add_data(target_frequency, v_0, v_1, temperature, resistance, time)
        #끝까지 처리 완료 -> json / 처리 완료 X -> None
        if req_type == "1" and result:
            print("start_1")
            print(f"Complete data(1) for client_id {client_id}: {result}")
            del obj_dict[client_id]  # 데이터 처리가 완료되었으므로 객체 삭제
            #데이터 변환 및 예측 처리 
            prediction = process_and_predict(result[3], result[0], result[1], result[2], result[5], result[4])
            print("prediction_suc")
            client.publish("kingo/response", json.dumps(prediction), qos=1)
        elif req_type == "0" and result:
            print("start_2")
            print(f"Complete data(2) for client_id {client_id}")
            #원래 데이터 저장
            frequencies_list, v_0_list, v_1_list, temperatures_list, resistances_list, times_list = portenta_obj.return_rawdata()
            raw_filename = "./AI_Model/data/" + client_id + "_rawdata.csv"
            df_raw = pd.DataFrame(frequencies_list, columns=['frequency'])
            df_raw['v_0'] = v_0_list
            df_raw['v_1'] = v_1_list
            df_raw['temperature'] = temperatures_list
            df_raw['resistance'] = resistances_list
            df_raw['time'] = times_list
            df_raw.to_csv(raw_filename, index=False, mode='a')
            #데이터 가공
            magnitude_list = []
            phase_list = []
            for i in range(len(frequencies)):
                magnitude, phase = calculate_impedance(frequencies_list[i], v_0_list[i], v_1_list[i], resistances_list[i], times_list[i])
                magnitude_list.append(magnitude)
                phase_list.append(phase)
            #가공된 데이터 저장
            filename = "./AI_Model/data/" + client_id + "_dataset.csv"
            df = pd.DataFrame(result[0], columns=['frequency'])
            df['phase'] = phase_list
            df['magnitude'] = magnitude_list
            df['temperature'] = result[3]
            del obj_dict[client_id] # 데이터 처리가 완료되었으므로 객체 삭제 -> csv 파일에 저장
            df.to_csv(filename, index=False, mode='a')

        '''
        #학습용
        if type == 0: 
            #csv 파일로 변환
            df = pd.DataFrame(frequencies, columns=['frequency'])
            df['phase'] = phases
            df['magnitude'] = magnitudes
            df['temperature'] = temperatures

            df.to_csv("./AI_Model/data/dataset.csv", index=False, mode='a') #덮어쓰기가 안됨 
            client.publish("kingo/response", json.dumps({"request_time" : request_time, "type" : type, "frequencies" : frequencies}), qos=1)
        elif type == 1:
            #추론
            client.publish("kingo/response", json.dumps("results"), qos=1)

        # 모델 예측 
        # KNN 모델 사용
        #prediction = predict_knn(frequency, phase, magnitude, temperature)

        # 예측 결과를 JSON 형식으로 변환하여 kingo/response로 발행
        #client.publish("kingo/response", json.dumps("results"), qos=1)
        '''
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
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


'''
테스트
curl http://127.0.0.1:8000/publish
mosquitto_sub -h 54.180.165.1 -t kingo/response
mosquitto_pub -h 54.180.165.1 -t KST/request -m "{\"temperatures\": [25, 30], \"frequencies\": [5000, 6000], \"v_0\": [1.1, 1.2], \"v_1\": [0.9, 1.0], \"times\": [1000, 2000], \"resistances\": [10, 20], \"K_percent\": [10, 15], \"N_percent\": [5, 10], \"P_percent\": [3, 7]}
'''