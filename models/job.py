from dataclasses import dataclass
from datetime import datetime


@dataclass
class Job:

    id: str

    type: str

    provider: str

    model: str

    status: str

    progress: int

    created_on: str = datetime.now().isoformat()

    started_on: str = ""

    completed_on: str = ""

    result = None

    error = ""