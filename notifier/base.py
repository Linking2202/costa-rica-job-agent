from abc import ABC, abstractmethod

class BaseNotifier(ABC):
    @abstractmethod
    def send_message(self, message: str) -> bool:
        """Envía un mensaje de texto. Retorna True si tuvo éxito."""
        pass

    @abstractmethod
    def send_job_alert(self, job: dict) -> bool:
        """Formatea y envía una alerta de empleo."""
        pass

