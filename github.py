import os
from google.colab import userdata
import subprocess # Import subprocess module

def secret_to_ssh_key(secret_name='id_rsa_github'):
    """
    Sets up the SSH private key from Colab userdata secret 'id_rsa_github'
    to be used for GitHub access.
    """
    def clean_ssh_key(s):
        return "\n".join([l.strip() for l in s.splitlines()]).strip() + "\n"

    try:
        github_ssh_key = userdata.get('id_rsa_github')
        github_ssh_key = clean_ssh_key(github_ssh_key)
    except Exception as e:
        print(f"Error retrieving 'id_rsa_github' from userdata: {e}")
        print("Please ensure you have added your SSH private key to Colab secrets with the name 'id_rsa_github'.")
        return False

    if not github_ssh_key:
        print("Error: 'id_rsa_github' secret is empty or not found.")
        return False

    # Ensure .ssh directory exists with correct permissions
    ssh_dir = os.path.expanduser('~/.ssh')
    os.makedirs(ssh_dir, mode=0o700, exist_ok=True)

    # Write the private key to a file
    key_path = os.path.join(ssh_dir, 'id_rsa_github')
    with open(key_path, 'w') as f:
        f.write(github_ssh_key)

    # Set correct permissions for the private key
    os.chmod(key_path, 0o600)

    # Add GitHub to known hosts (optional but good practice for first time)
    # This prevents the 'Are you sure you want to continue connecting (yes/no)?' prompt
    known_hosts_path = os.path.join(ssh_dir, 'known_hosts')
    try:
        with open(known_hosts_path, 'a+') as f:
            f.seek(0)
            if 'github.com' not in f.read():
                print("Adding github.com to known_hosts...")
                # Use subprocess for reliable command execution
                subprocess.run(['ssh-keyscan', '-H', 'github.com'], stdout=f, check=True)
            else:
                print("github.com already in known_hosts.")
    except Exception as e:
        print(f"Error managing known_hosts: {e}")
        return False

    # Create/update SSH config to use this key for github.com
    config_path = os.path.join(ssh_dir, 'config')
    config_content = f"""
Host github.com
    HostName github.com
    IdentityFile {key_path}
    User git
"""
    try:
        with open(config_path, 'a+') as f:
            f.seek(0) # Go to the beginning of the file
            current_config = f.read()
            if 'Host github.com' not in current_config:
                f.write(config_content)
            else:
                print("GitHub SSH configuration already exists in ~/.ssh/config.")
    except Exception as e:
        print(f"Error managing SSH config: {e}")
        return False


    # --- Debugging: Verify key validity with ssh-keygen --- 
    print(f"Verifying SSH key at {key_path}...")
    try:
        # Use subprocess to capture output and check return code
        keygen_check = subprocess.run(
            ['ssh-keygen', '-l', '-f', key_path],
            capture_output=True, text=True, check=True
        )
        print("SSH key fingerprint:")
        print(keygen_check.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error verifying SSH key with ssh-keygen: {e}")
        print(f"Stderr: {e.stderr}")
        print("This might indicate an issue with the key's format or content. Please check your 'id_rsa_github' secret.")
        return False
    except Exception as e:
        print(f"Unexpected error during ssh-keygen check: {e}")
        return False

    # --- Start the ssh-agent and add the key using subprocess --- 
    print("Attempting to start ssh-agent and add SSH key...")
    try:
        # Start ssh-agent and capture its output to set env vars
        agent_process = subprocess.run(['ssh-agent', '-s'], capture_output=True, text=True, check=True)
        agent_output_lines = agent_process.stdout.splitlines()

        for line in agent_output_lines:
            if '=' in line and ';' in line:
                # Parse the output to extract key-value pairs (e.g., SSH_AUTH_SOCK=...) 
                parts = line.split(';')[0].split('=', 1)
                if len(parts) == 2:
                    os.environ[parts[0]] = parts[1]
        print("SSH agent started and environment variables set.")

        # Add the key to the agent
        add_result = subprocess.run(['ssh-add', key_path], capture_output=True, text=True, check=True)
        print(f"ssh-add stdout: {add_result.stdout.strip()}")
        if add_result.stderr:
            print(f"ssh-add stderr: {add_result.stderr.strip()}")
        print("SSH key added to agent successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error during ssh-agent or ssh-add: {e}")
        print(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error during ssh-agent/ssh-add setup: {e}")
        return False

    print("SSH key setup complete. You can test it with `!ssh -T git@github.com`.")
    return True
setup_ssh_key_for_github()
