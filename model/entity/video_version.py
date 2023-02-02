from typing import Dict

from sqlalchemy import Integer, Column, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from database.db import Base


class VideoVersion(Base):
    __tablename__ = "video_version"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(1024), nullable=False)
    content_type = Column(String(64), nullable=False)
    bit_rate = Column(Integer, nullable=True)

    video_key = Column(String(32), ForeignKey("media.id", ondelete="CASCADE"), nullable=False)
    video = relationship("Media", back_populates="variants", lazy="raise")

    downloaded = Column(Boolean, nullable=False, default=False)
    file_path = Column(String(512), nullable=True)

    def __init__(self, data: Dict, video_key: int):
        self.url = data['url']
        self.content_type = data['content_type']
        bit_rate = data.get('bit_rate')
        if bit_rate is not None:
            self.bit_rate = int(bit_rate)
        self.video_key = video_key

    def __repr__(self) -> str:
        return f"VideoVersion({self.id}, video_key: {self.video_key})"
