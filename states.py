"""FSM состояния"""
from aiogram.fsm.state import State, StatesGroup

class AddArtistForm(StatesGroup):
    project_name = State()
    description = State()
    links = State()
    genre = State()
    about = State()

class CreateArtistForm(StatesGroup):
    project_name = State()
    description = State()
    links = State()
    genre = State()
    about = State()

class EditArtistForm(StatesGroup):
    artist_id = State()
    field = State()
    value = State()

class RejectForm(StatesGroup):
    app_id = State()
    reason = State()

class IdeaForm(StatesGroup):
    text = State()

class IdeaReplyForm(StatesGroup):
    idea_id = State()
    message = State()

class AddReleaseForm(StatesGroup):
    selecting_artist = State()
    release_name = State()
    description = State()
    genre = State()
    links = State()

class RejectReleaseForm(StatesGroup):
    release_id = State()
    reason = State()
