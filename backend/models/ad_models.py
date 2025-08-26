from pydantic import BaseModel
from typing import Optional

class Ad(BaseModel):
    id: Optional[str]
    name: str
    description: str
    imageUrl: str
    videoUrl: str
