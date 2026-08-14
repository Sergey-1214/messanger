class BrokerException(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class RabbitMQException(BrokerException):
    def __init__(self, detail: str):
        super().__init__(detail=detail)
