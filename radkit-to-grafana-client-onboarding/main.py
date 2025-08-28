import os
import shutil
import yaml
from radkit_client.sync import Client

CONFIG_YAML = "/radkit-to-grafana-config/config.yaml"
IDENTITIES_FOLDER = ".radkit/identities"

def enroll_radkit_client():
    """
    Enrolls the provided user into the RADKit cloud.
    The corresponding certificates are generated in the location /current_user/.radkit/identities of the host
    """
    with open(CONFIG_YAML, 'r') as f:
        config_data = yaml.safe_load(f)
        
    radkit_config_yaml = config_data.get('radkit-config', {})
    target_user = radkit_config_yaml.get('radkit-service-username')
    print(f"\n--- ✨🔑✨ Onboarding user ({target_user}) into the RADKit Cloud for non-interactive authentication ---\n")
    
    with Client.create() as rk_client:
        print("---⚠️👇 A link will appear down below on short. Please click it or copy/paste in your web browser 👇⚠️ ---\n")
        client = rk_client.sso_login(target_user)
        client.enroll_client()
        
def copy_radkit_identities_to_test():
    """
    Finds the current user directory, constructs the source path for .radkit/identities,
    and copies it to a 'radkit-to-grafana-config/identity-files' directory one level up from the current working directory.
    """
    try:
        user_home_dir = os.path.expanduser('~')
        source_path = os.path.join(user_home_dir, IDENTITIES_FOLDER)

        # Check if the source folder exists
        if not os.path.isdir(source_path):
            print(f"Error: Source folder '{source_path}' does not exist.")
            return

        current_working_dir = os.getcwd()
        destination_parent_dir = os.path.abspath(os.path.join(current_working_dir, '..'))
        destination_path = os.path.join(destination_parent_dir, '/radkit-to-grafana-config/identity-files', 'identities')
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)

        if os.path.exists(destination_path):
            print(f"📁🔑 Removing existing destination folder: {destination_path}")
            shutil.rmtree(destination_path)

        shutil.copytree(source_path, destination_path)
        print("\n---------------------------------------------------------------------------------------")
        print(f"✅📁🔑 Successfully copied '{source_path}' to '{destination_path}' in this repository!")
        print("You are now ready to mount the radkit-to-grafana environment.")
        print("👉 Issue the command `make` to build and run the system. Provide the password that you used in this setup.")
        print("---------------------------------------------------------------------------------------\n")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    enroll_radkit_client()
    copy_radkit_identities_to_test()
