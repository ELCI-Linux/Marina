import subprocess

def print_logo(llm_name):
    logos = {
        "gpt": """
   ░░░░░░░░░░
  ░░  GPT  ░░
   ░░░░░░░░░░
        """,

        "gemini": """
   ╭──────────╮
   │ GEMINI ☄  │
   ╰──────────╯
        """,

        "claude": """
  ╔════════════╗
  ║  CLAUDE 🤖  ║
  ╚════════════╝
        """,

        "deepseek": """
  ▄▄▄▄▄▄▄▄▄▄▄▄▄▄
  ▀ DEEPSEEK 🔎 ▀
  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀
        """
    }

    colors = {
        "gpt": "cyan",
        "gemini": "blue",
        "claude": "magenta",
        "deepseek": "green"
    }

    logo = logos.get(llm_name.lower(), f"[{llm_name.upper()}]")
    color = colors.get(llm_name.lower(), "white")

    try:
        subprocess.run(["lolcat", f"--force", f"--color={color}"], input=logo.encode(), check=False)
    except FileNotFoundError:
        print(logo)
