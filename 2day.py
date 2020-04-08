import asyncio
import time
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport = transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
            self.server.history.append(f"<{self.login}>: {decoded}")
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")

                clone_count = 0
                for user in self.server.clients:
                    if self.login == user.login:
                        clone_count += 1
                        if clone_count == 2:
                            self.transport.write(
                                f"Login {self.login} is already reserved, please try another.".encode())
                            time.sleep(2)
                            self.transport.close()
                self.transport.write(f"Hello, {self.login}!\n".encode())

                self.send_history(self.server.history)
            else:
                self.transport.write("Wrong login\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("New user connected")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("User left the chat")

    def send_message(self, content: str):
        message = f"<{self.login}>: {content}\n"
        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self, history: list):
        if len(history) <= 10:
            for row in history:
                self.transport.write(f"{row}\n".encode())
        else:
            # -20, т.к. не успел решить проблему переносов, а они добавляются в список,хранящий историю, как отдельные элементы
            for row in range(len(history) - 20, len(history) - 1):
                self.transport.write(f"{history[row]}\n".encode())


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()
        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            6253
        )
        print("Server works...")
        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Server has stopped by hand")
