from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.style import Style
from rich.console import Console
from rich.box import DOUBLE
from rich.markdown import Markdown


MC_LOGO = """\
    █████╗ ██╗   ██╗████████╗ ██████╗  █████╗  ██████╗ ███████╗███╗   ██╗████████╗
   ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
███████║██║   ██║   ██║   ██║   ██║███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║      
██╔══██║██║   ██║   ██║   ██║   ██║██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║      
██║  ██║╚██████╔╝   ██║   ╚██████╔╝██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║      
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝      
╔═══ 𝒞𝓇𝑒𝒶𝓉𝑒 𝒜𝑔𝑒𝓃𝓉𝒾𝒸 𝒜ℐ 𝓊𝓈𝒾𝓃𝑔 ℒ𝒶𝓃𝑔𝓊𝒶𝑔𝑒 ═══╗\
"""

version_table = Table(show_header=False, box=DOUBLE, expand=True)
version_table.add_column("Key", style="cyan")
version_table.add_column("Value", style="green")

version_table.add_row("Version", "0.2.0")
version_table.add_row("Author", "AutoAgent Team@HKU")
version_table.add_row("License", "MIT")

NOTES = """\
* Choose `user mode` if you just want to let a general yet powerful AI Assistant to help you
* Choose `agent editor` to create your own AI Agent with language. 
* Choose `workflow editor` to create your own AI Workflow with language. 
* Choose `exit` to exit the program
"""
NOTES = Markdown(NOTES)

GOODBYE_LOGO = """\
███████╗███████╗███████╗    ██╗   ██╗ ██████╗ ██╗   ██╗
██╔════╝██╔════╝██╔════╝    ╚██╗ ██╔╝██╔═══██╗██║   ██║
███████╗█████╗  █████╗       ╚████╔╝ ██║   ██║██║   ██║
╚════██║██╔══╝  ██╔══╝        ╚██╔╝  ██║   ██║██║   ██║
███████║███████╗███████╗       ██║   ╚██████╔╝╚██████╔╝
╚══════╝╚══════╝╚══════╝       ╚═╝    ╚═════╝  ╚═════╝ 
· 𝓜𝓮𝓽𝓪𝓒𝓱𝓪𝓲𝓷-𝓐𝓘 ·           
""".strip()


