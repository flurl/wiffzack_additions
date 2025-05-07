from dataclasses import dataclass
import pathlib

MESSAGEDIR: pathlib.Path = pathlib.Path("./assets/messages")


@dataclass
class Message:
    path: str
    name: str
    type: str
    content: str = ""


def get_messages_list() -> list[Message]:
    messages: list[Message] = []
    for folder in MESSAGEDIR.iterdir():
        if folder.is_dir():
            for file in folder.iterdir():
                if file.suffix in [".txt", ".html"]:
                    messages.append(
                        Message(
                            path=folder.name,
                            name=file.stem,
                            type=file.suffix[1:]
                        )
                    )
                    break
    return messages


def get_message(path: str) -> Message:
    folder: pathlib.Path = MESSAGEDIR / path
    if folder.is_dir():
        for file in folder.iterdir():
            if file.suffix in [".txt", ".html"]:
                with open(file, "r", encoding="utf-8") as f:
                    content: str = f.read()
                return Message(
                    path=folder.name,
                    name=file.stem,
                    type=file.suffix[1:],
                    content=content
                )
    raise FileNotFoundError
