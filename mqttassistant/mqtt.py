import asyncio
from amqtt import client
from .log import get_logger


class MQTTClient(client.MQTTClient):
    pass
    def __init__(self, *args, on_connect=None, **kwargs):
        self.on_connect = on_connect
        super().__init__(*args, **kwargs)

    async def _do_connect(self):
        await super()._do_connect()
        if self.on_connect:
            await self.on_connect()


class Mqtt:
    def __init__(self, **config):
        self.log = get_logger('Mqtt')
        # Config
        self.name = config.get('mqtt_name', 'mqttassistant')
        self.host = config.get('mqtt_host', 'localhost')
        self.port = config.get('mqtt_port', 1883)
        self.username = config.get('mqtt_username', '')
        self.password = config.get('mqtt_password', '')
        self.keep_alive = config.get('mqtt_keep_alive', 5)
        self.client_id = self.name
        self.last_will_topic = '{}/state'.format(self.name)
        self.client = self.get_client()
        self.connect_parameters = self.get_connect_parameters()

    def get_client(self):
        return MQTTClient(
            client_id=self.client_id,
            config=self.get_client_config(),
            on_connect=self.on_connect,
        )

    def get_client_config(self):
        return dict(
            keep_alive=self.keep_alive,
            ping_delay=1,
            default_qos=2,
            default_retain=False,
            auto_reconnect=True,
            reconnect_max_interval=5,
            reconnect_retries=-1,
            will=dict(
                retain=True,
                topic=self.last_will_topic,
                message=b'offline',
                qos=1,
            )
        )

    def get_connect_parameters(self):
        auth = ''
        if self.username:
            auth = '{}:{}@'.format(self.username, self.password)
        return dict(
            uri='mqtt://{}{}:{}/'.format(auth, self.host, self.port),
        )

    async def run(self):
        self.log.info('Started. Server: {}'.format(self.host))
        return await self.connect()

    async def stop(self, **kwargs):
        if self.client.session.transitions.is_connected():
            await self.client.publish(self.last_will_topic, b'offline')
            await self.client.disconnect()
        self.log.info('Stopped')

    async def connect(self):
        await self.client.connect(**self.connect_parameters)
        asyncio.create_task(self.read_messages())

    async def on_connect(self):
        await self.client.publish(self.last_will_topic, b'online')
        # Subscribe
        # topic = 'topic_name'
        # await self.client.subscribe([(topic, 2)])
        self.log.info('Connected')

    def _on_message(self, topic, payload, retained):
        asyncio.create_task(self.on_message(topic, payload, retained))

    async def read_messages(self):
        while True:
            try:
                message = await self.client.deliver_message()
                print(message)
                if message:
                    packet = message.publish_packet
                    topic = packet.variable_header.topic_name
                    payload = packet.payload.data.decode('utf-8')
                    await self.on_message(topic, payload)
            except Exception as error:
                self.log.exception('read_messages', error)

    async def on_message(self, topic, payload):
        self.log.debug('message received: {} {}'.format(topic, payload))
