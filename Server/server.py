import logging
import asyncio
from fastapi import FastAPI
from gmqtt import Client as MQTTClient
from contextlib import asynccontextmanager

app = FastAPI()
logger = logging.getLogger(__name__)

MQTT_HOST = "54.180.165.1"
MQTT_PORT = 1883
KEEPALIVE = 60
MQTT_TOPIC = "kingo/test"

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
: kingo/response 주제로 "ok"메시지 발행
'''
async def on_message(client, topic, payload, qos, properties):
    message = payload.decode()
    logger.info(f"Received message on topic {topic}: {message}")
    client.publish("kingo/response", "ok", qos=1)

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
curl http://127.0.0.1:8000/publish
mosquitto_sub -h 54.180.165.1 -t kingo/response
'''