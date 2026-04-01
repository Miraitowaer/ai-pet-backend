from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class StatusRequest(_message.Message):
    __slots__ = ("pet_id",)
    PET_ID_FIELD_NUMBER: _ClassVar[int]
    pet_id: str
    def __init__(self, pet_id: _Optional[str] = ...) -> None: ...

class StatusResponse(_message.Message):
    __slots__ = ("status", "mood_score")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MOOD_SCORE_FIELD_NUMBER: _ClassVar[int]
    status: str
    mood_score: int
    def __init__(self, status: _Optional[str] = ..., mood_score: _Optional[int] = ...) -> None: ...

class ChatRequest(_message.Message):
    __slots__ = ("user_id", "message")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    message: str
    def __init__(self, user_id: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class ChatResponse(_message.Message):
    __slots__ = ("text_chunk", "agent_state", "is_finish")
    TEXT_CHUNK_FIELD_NUMBER: _ClassVar[int]
    AGENT_STATE_FIELD_NUMBER: _ClassVar[int]
    IS_FINISH_FIELD_NUMBER: _ClassVar[int]
    text_chunk: str
    agent_state: str
    is_finish: bool
    def __init__(self, text_chunk: _Optional[str] = ..., agent_state: _Optional[str] = ..., is_finish: bool = ...) -> None: ...
