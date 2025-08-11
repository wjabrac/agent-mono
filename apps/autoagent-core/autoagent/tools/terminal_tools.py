
import os
import socket
import json
import base64
import math
# from autoagent.util import run_command_in_container
from autoagent.environment.docker_env import DockerEnv, DockerConfig
from autoagent.registry import register_tool
from autoagent.environment.markdown_browser.requests_markdown_browser import RequestsMarkdownBrowser
from typing import Tuple, Optional, Dict, Union
import time
import tiktoken
from datetime import datetime
from functools import wraps
from rich.console import Console
from pathlib import Path
from autoagent.environment.local_env import LocalEnv
from autoagent.environment.docker_env import DockerEnv
import inspect

terminal_env = RequestsMarkdownBrowser(local_root=os.getcwd(), workplace_name="terminal_env", viewport_size=1024 * 8)

def _get_browser_state(env: RequestsMarkdownBrowser) -> Tuple[str, str]:
    """
    Get the current state of the browser, including the header and content.
    """
    # print(env.address)
    address = env.address
    tool_name = address.split('/')[-1].split('.')[0].split('___')[-1]
    header = f"[The output of the tool `{tool_name}` showing in the interactive terminal]\n"

    current_page = env.viewport_current_page
    total_pages = len(env.viewport_pages)

    
    for i in range(len(env.history) - 2, -1, -1):  # Start from the second last
        if env.history[i][0] == address:
            header += f"You previously visited this page of terminal {round(time.time() - env.history[i][1])} seconds ago.\n"
            break
    prefix = f"[Your terminal is currently open to the page '{env.page_title}']\n" if env.page_title is not None else ""
    
    header = prefix + header
    header += f"Terminal viewport position: Showing page {current_page+1} of {total_pages}.\n"
    if total_pages > 1:
        header += f"[NOTE] The output of the tool `{tool_name}`, you can use `terminal_page_up` to scroll up and `terminal_page_down` to scroll down. If there are many pages with meaningless content like progress bar or output of generating directory structure when there are many datasets in the directory, you can use `terminal_page_to` to move the viewport to the end of terminal where the meaningful content is.\n"
    return (header, env.viewport)

def open_local_terminal_output(path: str):
    """
    Open a local file at a path in the text-based browser and return current viewport content.

    Args:
        path: The absolute path of a local file to visit.
    """
    try: 
        # assert DOCKER_WORKPLACE_NAME in path, f"The path must be a absolute path from `/{DOCKER_WORKPLACE_NAME}/` directory"
        # local_path = path.replace('/' + DOCKER_WORKPLACE_NAME, LOCAL_ROOT + f'/{DOCKER_WORKPLACE_NAME}')
        # print(local_path)
        terminal_env.open_local_file(path)
        header, content = _get_browser_state(terminal_env)
        final_response = header.strip() + "\n==============================================\n" + content + "\n==============================================\n"
        return final_response
    except Exception as e:
        return f"Error in `open_local_terminal_output`: {e}"
    
@register_tool("terminal_page_up")
def terminal_page_up():
    """
    Scroll the viewport UP one page-length in the current terminal. Use this function when the terminal is too long and you want to scroll up to see the previous content.
    """
    try: 
        terminal_env.page_up()
        header, content = _get_browser_state(terminal_env)
        final_response = header.strip() + "\n==============================================\n" + content + "\n==============================================\n"
        return final_response
    except Exception as e:
        return f"Error in `page_up`: {e}"
    
@register_tool("terminal_page_down")
def terminal_page_down():
    """
    Scroll the viewport DOWN one page-length in the current terminal. Use this function when the terminal is too long and you want to scroll down to see the next content.
    """
    try: 
        terminal_env.page_down()
        header, content = _get_browser_state(terminal_env)
        final_response = header.strip() + "\n==============================================\n" + content + "\n==============================================\n"
        return final_response
    except Exception as e:
        return f"Error in `page_down`: {e}"
@register_tool("terminal_page_to")
def terminal_page_to(page_idx: int):
    """
    Move the viewport to the specified page index. The index starts from 1.
    Use this function when you want to move the viewport to a specific page, especially when the middle of terminal output are meaningless, like the output of progress bar or output of generating directory structure when there are many datasets in the directory, you can use this function to move the viewport to the end of terminal where the meaningful content is.
    """
    try:
        terminal_env.page_to(page_idx - 1)
        header, content = _get_browser_state(terminal_env)
        final_response = header.strip() + "\n==============================================\n" + content + "\n==============================================\n"
        return final_response
    except Exception as e:
        return f"Error in `page_to`: {e}"

def process_terminal_agent_response(func):
    """
    装饰器函数，用于处理命令执行的响应结果
    - 如果结果是包含 status 和 result 的字典，返回格式化后的结果
    - 如果结果是错误字符串，直接返回
    """
    # original_func = func  # 保存原始函数引用
    @wraps(func)  # 保持原函数的签名和文档
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # 如果返回值是字典且包含 status 和 result
        if isinstance(result, dict) and 'status' in result and 'result' in result:
            try:
                res_output = result['result']
                if res_output == "": res_output = " "
                if result['status'] != 0:
                    res_output = f"[ERROR] {res_output}"
                else: 
                    res_output = f"[SUCCESS] {res_output}"
                tmp_file = os.path.join(os.getcwd(), "terminal_tmp", "terminal_output_{}___{}.txt".format(datetime.now().strftime("%Y%m%d_%H%M%S"), func.__name__))
                with open(tmp_file, "w") as f:
                    f.write(res_output)
                return open_local_terminal_output(tmp_file)
            except Exception as e:
                return f"Error in the post-processing of `{func.__name__}`: {e}"
            
        elif isinstance(result, str):
            return result
        else:
            return f"Error in `{func.__name__}`: {result}"
    # 复制原始函数的签名到包装函数
    # 保持原始函数的属性
    return wrapper

def process_terminal_response(func):
    """
    装饰器函数，用于处理命令执行的响应结果
    - 如果结果是包含 status 和 result 的字典，返回格式化后的结果
    - 如果结果是错误字符串，直接返回
    """
    # original_func = func  # 保存原始函数引用
    @wraps(func)  # 保持原函数的签名和文档
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # 如果返回值是字典且包含 status 和 result
        if isinstance(result, dict) and 'status' in result and 'result' in result:
            try:
                res_output = result['result']
                if res_output == "": res_output = " "
                if result['status'] != 0:
                    res_output = f"[ERROR] {res_output}"
                else: 
                    res_output = f"[SUCCESS] {res_output}"
                tmp_file = os.path.join(os.getcwd(), "terminal_tmp", "terminal_output_{}___{}.txt".format(datetime.now().strftime("%Y%m%d_%H%M%S"), func.__name__))
                Path(tmp_file).parent.mkdir(parents=True, exist_ok=True)
                with open(tmp_file, "w") as f:
                    f.write(res_output)
                return open_local_terminal_output(tmp_file)
            except Exception as e:
                return f"Error in the post-processing of `{func.__name__}`: {e}"
            
        elif isinstance(result, str):
            return result
        else:
            return f"Error in `{func.__name__}`: {result}"
    # 复制原始函数的签名到包装函数
    # 保持原始函数的属性
    return wrapper
@register_tool("read_file")
@process_terminal_response
def read_file(file_path: str, context_variables) -> str:
    """
    Read the contents of a file and return it as a string. Use this function when there is a need to check an existing file.
    Args:
        file_path: The path of the file to read.
    Returns:
        A string representation of the contents of the file.
    """
    env: Union[DockerEnv, LocalEnv] = context_variables.get("code_env", LocalEnv())
    try:
        command = f"cat {file_path}"
        response = env.run_command(command) # status, result
        # res_output = truncate_by_tokens(env, response['result'], 10000)
        # return f"Exit code: {response['status']} \nOutput: \n{res_output}"
        return response
    except FileNotFoundError:
        return f"[ERROR] Error in reading file: {file_path}"

def write_file_in_chunks(file_content, output_path, env: DockerEnv, chunk_size=100000):
    encoded_content = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')
    total_chunks = math.ceil(len(encoded_content) / chunk_size)
    
    for i in range(total_chunks):
        start = i * chunk_size
        end = (i + 1) * chunk_size
        chunk = encoded_content[start:end]
        
        # use cat command
        if i == 0:
            command = f"echo \"{chunk}\" | base64 -d > {output_path}"
        else:
            command = f"echo \"{chunk}\" | base64 -d >> {output_path}"
        
        response = env.run_command(command)
        
        if response["status"] != 0:
            return f"Error creating file {output_path}: " + response["result"]
        
        # print(f"Successfully written block {i+1}/{total_chunks}")
    
    return f"File created at: {output_path}"

@register_tool("create_file")
def create_file(path: str, content: str, context_variables) -> str:
    """
    Create a file with the given path and content. Use this function when there is a need to create a new file with initial content.
    Args:
        path: The path to the file to create.
        content: The initial content to write to the file.
    Returns:
        A string representation of the result of the file creation.
    """
    env: Union[DockerEnv, LocalEnv] = context_variables.get("code_env", LocalEnv())
    try:
        msg = write_file_in_chunks(content, path, env)
        return msg
    except Exception as e:
        return f"Error creating file: {str(e)}"

@register_tool("write_file")
def write_file(path: str, content: str, context_variables) -> str:
    """
    Write content to a file. Use this function when there is a need to write content to an existing file.
    Args:
        path: The path to the file to write to.
        content: The content to write to the file.
    Returns:
        A string representation of the result of the file writing.
    """
    env: Union[DockerEnv, LocalEnv] = context_variables.get("code_env", LocalEnv())
    try:
        msg = write_file_in_chunks(content, path, env)
        return msg
    except Exception as e:
        return f"Error writing to file: {str(e)}"

@register_tool("list_files")
@process_terminal_response
def list_files(path: str, context_variables) -> str:
    """
    List all files and directories under the given path if it is a directory. Use this function when there is a need to list the contents of a directory.
    Args:
        path: The file system path to check and list contents from.
    Returns:
        A string representation of the contents of the directory.
    """
    env: Union[DockerEnv, LocalEnv] = context_variables.get("code_env", LocalEnv())
    if os.path.isfile(path):
        return "[ERROR] The given path is a file. Please provide a path of a directory."
    command = f"ls -1 {path}"
    response = env.run_command(command)
    if response["status"] != 0:
        return f"[ERROR] Error listing files: {response['result']}"
    return response

@register_tool("create_directory")
def create_directory(path: str, context_variables) -> str:
    """
    Create a directory if it does not exist. Use this function when there is a need to create a new directory.
    Args:
        path: The path of the directory to create.
    Returns:
        A string representation of the result of the directory creation.
    """
    env: Union[DockerEnv, LocalEnv] = context_variables.get("code_env", LocalEnv())
    try:
        command = f"mkdir -p {path}"
        response = env.run_command(command)
        if response["status"] != 0:
            return f"Error creating directory: {response['result']}"
        return f"Directory '{path}' created successfully."
    except OSError as error:
        return f"Creation of the directory '{path}' failed due to: {error}"

@register_tool("gen_code_tree_structure")
@process_terminal_response
def gen_code_tree_structure(directory: str, context_variables) -> str:
    """Generate a tree structure of the code in the specified directory. Use this function when you need to know the overview of the codebase and want to generate a tree structure of the codebase.
    Args:
        directory: The directory to generate the tree structure for.
    Returns:
        A string representation of the tree structure of the code in the specified directory.
    """
    env: Union[DockerEnv, LocalEnv] = context_variables.get("code_env", LocalEnv())
    try:
        command = f"tree {directory}"
        response = env.run_command(command)
        return response
    except Exception as e:
        return f"[ERROR] Error running tree {directory}: {str(e)}"
    
def print_stream(text):
    console = Console()
    console.print(f"[grey42]{text}[/grey42]")
@register_tool("execute_command")
@process_terminal_response
def execute_command(command: str, context_variables) -> str:
    """
    Execute a command in the system shell. Use this function when there is a need to run a system command, and execute programs.
    Args:
        command: The command to execute in the system shell.
    Returns:
        A string representation of the exit code and output of the command.
    """
    env: Union[DockerEnv, LocalEnv] = context_variables.get("code_env", LocalEnv())
    try:
        response = env.run_command(command, print_stream)
        return response
    except Exception as e:
        return f"[ERROR] Error running command: {str(e)}"

def print_stream(text):
    console = Console()
    def escape_inner_tags(text):
        # 先保护[grey42]标签
        text = text.replace("[grey42]", "###GREY42_START###")
        text = text.replace("[/grey42]", "###GREY42_END###")
        
        # 转义所有其他的[]标签
        text = text.replace("[", "\\[")
        text = text.replace("]", "\\]")
        
        # 恢复[grey42]标签
        text = text.replace("###GREY42_START###", "[grey42]")
        text = text.replace("###GREY42_END###", "[/grey42]")
        
        return text
    escaped_text = escape_inner_tags(text)
    console.print(f"[grey42]{escaped_text}[/grey42]")
def set_doc(doc_template):
    def decorator(func):
        func.__doc__ = doc_template
        return func
    return decorator

@register_tool("run_python")
@process_terminal_response
def run_python(
    context_variables,
    code_path: str,
    cwd: str = None,
    env_vars: Optional[Dict[str, str]] = None,
) -> str:
    """
    Run a python script. 
    Args:
        code_path: The absolute or relative path (the relative path is from the root of the workplace `/workplace`) to the python script file.
        cwd: The working directory of the python script. If not provided, will regard the directory of the script as the working directory. If there is a command `cd ...` in the instruction for running the script, you should provide the cwd and not use the default value. (Optional)
        env_vars: The environment variables to be set before running the python script. (Optional)
    Returns:
        A string representation of the exit code and output of the python script.
    """
    env: Union[DockerEnv, LocalEnv] = context_variables.get("code_env", LocalEnv())
    try:
        # 转换为绝对路径
        # abs_path = str(Path(code_path).resolve())
        if Path(code_path).is_absolute():
            if env.run_command(f"ls {code_path}")['status'] != 0: return f"[ERROR] File {code_path} does not exist"
            code_abs_path = code_path
        else: 
            code_abs_path = f"{env.docker_workplace}/{code_path}"
            if env.run_command(f"ls {code_abs_path}")['status'] != 0: return f'[ERROR] You use a relative path, so we regard the `{env.docker_workplace}` as the root of the workplace, but `{code_abs_path}` does not exist'
        
        
        if cwd:
            # 使用指定的项目根目录
            if Path(cwd).is_absolute():
                if env.run_command(f"ls {cwd}")['status'] != 0: return f"[ERROR] Working directory {cwd} does not exist"
            else: 
                cwd = f"{env.docker_workplace}/{cwd}"
                if env.run_command(f"ls {cwd}")['status'] != 0: return f"[ERROR] You use a relative path for `cwd`, so we regard the `{env.docker_workplace}` as the working directory, but `{cwd}` does not exist"
        else:
            cwd = str(Path(code_abs_path).parent)
            
        
        # 设置PYTHONPATH
        pythonpath = str(cwd)
        
        # 获取Python解释器路径
        env_str = f"PYTHONPATH={pythonpath}"
        
        if env_vars:
            env_str += " " + " ".join([f"{k}={v}" for k, v in env_vars.items()])
        # print(env_str)
        
        # 构建相对模块路径
        try:
            rel_path = Path(code_abs_path).relative_to(cwd)
            module_path = str(rel_path.with_suffix('')).replace(os.sep, '.')
            
            command = f"cd {cwd} && {env_str} python -m {module_path}"
        except ValueError:
            # 如果无法构建相对路径，使用完整路径
            command = f"cd {cwd} && {env_str} python {code_path}"
            
        # print(f"Executing: {command}")
        
        result = env.run_command(command, print_stream)
        return result
        
    except Exception as e:
        return f"[ERROR] Error when running the python script: {e}"


if __name__ == "__main__":
    env_config = DockerConfig(
        container_name = "paper_eval_dit", 
    workplace_name = "workplace", 
    communication_port = 12347, 
    conda_path = "/home/user/micromamba", 
    local_root = "/home/tjb/llm/agent/Inno-agent/workplace_paper/task_dit/workplace"
    )
    env = DockerEnv(env_config)
    
    # print(read_file("/workplace/lucidrains_denoising_diffusion/denoising_diffusion_pytorch/denoising_diffusion_pytorch.py", env))
    # print(terminal_page_to(3))
    sig = inspect.signature(execute_command)
    print("Parameters from signature:", list(sig.parameters.keys()))
    # print(terminal_page_down())
    # print(terminal_page_down())
    # print(terminal_page_down())
    # print(terminal_page_down())
    # print(execute_command("cp project/configs.py ./", env))
    
