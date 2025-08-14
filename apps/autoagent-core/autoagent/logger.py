from datetime import datetime
from pathlib import Path
import json
import logging
from typing import List

from rich.console import Console
from rich.markup import escape

from constant import (
    DEBUG,
    DEFAULT_LOG,
    LOG_PATH,
    MC_MODE,
    LOG_LEVEL,
    JSON_LOGS,
)

BAR_LENGTH = 60


class JsonFormatter(logging.Formatter):
    """Simple JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        return json.dumps(log_record)


class MetaChainLogger:
    def __init__(
        self, log_path: str, level: str = LOG_LEVEL, json_logs: bool = JSON_LOGS
    ):
        self.log_path = log_path
        self.console = Console()
        self.debug = DEBUG
        self.json_logs = json_logs

        self.logger = logging.getLogger("autoagent")
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self.logger.propagate = False
        self.logger.handlers = []

        formatter = (
            JsonFormatter()
            if json_logs
            else logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

        if self.log_path:
            file_handler = logging.FileHandler(self.log_path)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _write_log(self, message: str):
        if not self.log_path:
            return
        with open(self.log_path, "a") as f:
            f.write(message + "\n")

    def _warp_args(self, args_dict: str):
        args_dict = json.loads(args_dict)
        args_str = ""
        for k, v in args_dict.items():
            args_str += f"{repr(k)}={repr(v)}, "
        return args_str[:-2]

    def _wrap_title(self, title: str, color: str = None):
        single_len = (BAR_LENGTH - len(title)) // 2
        color_bos = f"[{color}]" if color else ""
        color_eos = f"[/{color}]" if color else ""
        return f"{color_bos}{'*'*single_len} {title} {'*'*single_len}{color_eos}"

    def _log(self, level: str, *args: str, **kwargs: dict):
        message = "\n".join(map(str, args))
        log_level = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARN": logging.WARNING,
            "ERROR": logging.ERROR,
        }.get(level.upper(), logging.INFO)
        self.logger.log(log_level, message)

        if self.debug and not self.json_logs:
            color = kwargs.get("color", "white")
            if MC_MODE:
                color = "grey58"
            title = kwargs.get("title", level.upper())
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_str = f"[{timestamp}]\n{message}"
            self.console.print(self._wrap_title(title, f"bold {color}"))
            print_str = escape(log_str)
            if MC_MODE:
                print_str = f"[grey58]{print_str}[/grey58]"
            self.console.print(print_str, highlight=True, emoji=True)

    def debug(self, *args: str, **kwargs: dict):
        self._log("DEBUG", *args, **kwargs)

    def info(self, *args: str, **kwargs: dict):
        self._log("INFO", *args, **kwargs)

    def warn(self, *args: str, **kwargs: dict):
        self._log("WARN", *args, **kwargs)

    def error(self, *args: str, **kwargs: dict):
        self._log("ERROR", *args, **kwargs)

    def _wrap_timestamp(self, timestamp: str, color: bool = True):
        color_bos = "[grey58]" if color else ""
        color_eos = "[/grey58]" if color else ""
        return f"{color_bos}[{timestamp}]{color_eos}"

    def _print_tool_execution(self, message, timestamp: str):
        if MC_MODE:
            colors = ["grey58"] * 3
        else:
            colors = ["pink3", "blue", "purple"]
        self.console.print(self._wrap_title("Tool Execution", f"bold {colors[0]}"))
        self.console.print(self._wrap_timestamp(timestamp, color=True))
        self.console.print(
            f"[bold {colors[1]}]Tool Execution:[/bold {colors[1]}]", end=" "
        )
        self.console.print(
            f"[bold {colors[2]}]{message['name']}[/bold {colors[2]}]\n[bold {colors[1]}]Result:[/bold {colors[1]}]"
        )
        print_str = f"---\n{escape(message['content'])}\n---"
        if MC_MODE:
            print_str = f"[grey58]{print_str}[/grey58]"
        self.console.print(print_str, highlight=True, emoji=True)

    def _save_tool_execution(self, message, timestamp: str):
        self._write_log(self._wrap_title("Tool Execution"))
        self._write_log(
            f"{self._wrap_timestamp(timestamp, color=False)}\ntool execution: {message['name']}\nResult:\n---\n{message['content']}\n---"
        )

    def _print_assistant_message(self, message, timestamp: str):
        if MC_MODE:
            colors = ["grey58"] * 3
        else:
            colors = ["light_salmon3", "blue", "purple"]
        self.console.print(self._wrap_title("Assistant Message", f"bold {colors[0]}"))
        self.console.print(
            f"{self._wrap_timestamp(timestamp, color=True)}\n[bold {colors[1]}]{message['sender']}[/bold {colors[1]}]:",
            end=" ",
        )
        if message["content"]:
            print_str = escape(message["content"])
            if MC_MODE:
                print_str = f"[grey58]{print_str}[/grey58]"
            self.console.print(print_str, highlight=True, emoji=True)
        else:
            print_str = None
            if MC_MODE:
                print_str = "[grey58]None[/grey58]"
            self.console.print(print_str, highlight=True, emoji=True)

    def _save_assistant_message(self, message, timestamp: str):
        self._write_log(self._wrap_title("Assistant Message"))
        content = message["content"] if message["content"] else None
        self._write_log(
            f"{self._wrap_timestamp(timestamp, color=False)}\n{message['sender']}: {content}"
        )

    def _print_tool_call(self, tool_calls: List, timestamp: str):
        if MC_MODE:
            colors = ["grey58"] * 3
        else:
            colors = ["light_pink1", "blue", "purple"]
        if len(tool_calls) >= 1:
            self.console.print(self._wrap_title("Tool Calls", f"bold {colors[0]}"))

        for tool_call in tool_calls:
            f = tool_call["function"]
            name, args = f["name"], f["arguments"]
            arg_str = self._warp_args(args)
            print_arg_str = escape(arg_str)
            if MC_MODE:
                print_arg_str = f"[grey58]{print_arg_str}[/grey58]"
            self.console.print(
                f"{self._wrap_timestamp(timestamp, color=True)}\n[bold {colors[2]}]{name}[/bold {colors[2]}]({print_arg_str})"
            )

    def _save_tool_call(self, tool_calls: List, timestamp: str):
        if len(tool_calls) >= 1:
            self._write_log(self._wrap_title("Tool Calls"))

        for tool_call in tool_calls:
            f = tool_call["function"]
            name, args = f["name"], f["arguments"]
            arg_str = self._warp_args(args)
            self._write_log(
                f"{self._wrap_timestamp(timestamp, color=False)}\n{name}({arg_str})"
            )

    def pretty_print_messages(self, message, **kwargs) -> None:
        # for message in messages:
        if message["role"] != "assistant" and message["role"] != "tool":
            return
        # console = Console()

        # handle tool call
        if message["role"] == "tool":
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if self.log_path:
                self._save_tool_execution(message, timestamp)
            if self.debug:
                self._print_tool_execution(message, timestamp)
            return

        # handle assistant message
        # print agent name in blue
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.log_path:
            self._save_assistant_message(message, timestamp)
        if self.debug:
            self._print_assistant_message(message, timestamp)

        # print tool calls in purple, if any
        tool_calls = message.get("tool_calls") or []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.log_path:
            self._save_tool_call(tool_calls, timestamp)
        if self.debug:
            self._print_tool_call(tool_calls, timestamp)


class LoggerManager:
    _instance = None
    _logger: MetaChainLogger = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = LoggerManager()
        return cls._instance

    @classmethod
    def get_logger(cls):
        return cls.get_instance()._logger

    @classmethod
    def set_logger(cls, new_logger):
        cls.get_instance()._logger = new_logger


if DEFAULT_LOG:
    if LOG_PATH is None:
        log_dir = Path(f'logs/res_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        log_dir.mkdir(
            parents=True, exist_ok=True
        )  # recursively create all necessary parent directories
        log_path = str(log_dir / "agent.log")
        # logger = MetaChainLogger(log_path=log_path)
        LoggerManager.set_logger(MetaChainLogger(log_path=log_path))
    else:
        # logger = MetaChainLogger(log_path=LOG_PATH)
        LoggerManager.set_logger(MetaChainLogger(log_path=LOG_PATH))
    # logger.info("Log file is saved to", logger.log_path, "...", title="Log Path", color="light_cyan3")
    LoggerManager.get_logger().info(
        "Log file is saved to",
        LoggerManager.get_logger().log_path,
        "...",
        title="Log Path",
        color="light_cyan3",
    )
else:
    # logger = None
    LoggerManager.set_logger(None)
logger = LoggerManager.get_logger()


def set_logger(new_logger):
    LoggerManager.set_logger(new_logger)


# if __name__ == "__main__":
#     logger = MetaChainLogger(log_path="test.log")
#     logger.pretty_print_messages({"role": "assistant", "content": "Hello, world!", "tool_calls": [{"function": {"name": "test", "arguments": {"url": "https://www.google.com", "query": "test"}}}], "sender": "test_agent"})

#     logger.pretty_print_messages({"role": "tool", "name": "test", "content": "import requests\n\nurl = 'https://www.google.com'\nquery = 'test'\n\nresponse = requests.get(url)\nprint(response.text)", "sender": "test_agent"})
#     logger.info("test content", color="red", title="test")
