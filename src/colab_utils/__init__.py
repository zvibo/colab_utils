from .github import secret_to_ssh_key


def setup_git_ssh(*args):
    secret_to_ssh_key(*args)

def hello() -> str:
    return "Hello from colab-utils!"
