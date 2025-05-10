from django.db.models import Model
from simple_history.models import HistoricalRecords


class BaseModel(Model):
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True
