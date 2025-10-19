import json
import requests
import time
import subprocess
import shutil
from better_profanity import profanity

# dotenv for local development
from dotenv import load_dotenv
import os
load_dotenv()

# Load profanity filter word list
profanity.load_censor_words()



GITHUB_PAT = os.getenv('GH_PAT')

# if running locally, automatically set DEBUG mode
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'

if not GITHUB_PAT:
    raise ValueError("GH_PAT environment variable not set. Please set it in the .env file or Secret Manager.")

SEARCH_URL = "https://api.github.com/search/repositories"
SEARCH_QUERY = 'in:readme sort:updated -user:kasmtech "KASM-REGISTRY-DISCOVERY-IDENTIFIER"'


REPOS = []
REPO_STATS = {}
EXPORT_JSON_CONTENT = {}


def make_request(url, params=None):
    time.sleep(0.5)  # Rate limiting
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": "Bearer " + GITHUB_PAT
    }
    response = requests.get(url, headers=headers, params=params)
    return response


def skopeo_inspect(image_full_name, docker_registry=None):
    # very hacky, could be improved
    cmd = ["skopeo", "inspect", "--raw", f"docker://{image_full_name}"]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error inspecting image {image_full_name}: {result.stderr}")
        print("Trying with registry prefix..")
        if docker_registry:
            cmd = ["skopeo", "inspect", "--raw", f"docker://{docker_registry}/{image_full_name}"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error inspecting image {docker_registry}/{image_full_name}: {result.stderr}")
                return False
            return True
        return False
    return True


def check_profanity_in_workspace(workspace_json, workspace_name):
    """
    Check workspace data for profanity in name, description, and categories.
    
    Args:
        workspace_json: The workspace.json content as a dict
        workspace_name: The folder name of the workspace
    
    Returns:
        bool: True if profanity found, False otherwise
    """
    # Fields to check for profanity
    fields_to_check = {
        'workspace_name': workspace_name,
        'friendly_name': workspace_json.get('friendly_name', ''),
        'description': workspace_json.get('description', ''),
        'categories': ' '.join(workspace_json.get('categories', []))
    }
    
    for field_name, field_value in fields_to_check.items():
        if field_value and profanity.contains_profanity(str(field_value)):
            print(f"Profanity detected in {field_name}: {field_value}")
            return True
    
    return False
 

def check_image_pullability(workspace_json):
    """
    Extract docker_registry and images from workspace.json and check pullability.
    
    Args:
        workspace_json: The workspace.json content as a dict

    Returns:
        The workspace_json content with only images that are pullable, if none are pullable, return None
    """
    workspace_json = workspace_json.copy()
    docker_registry = workspace_json.get('docker_registry')
    # remove https:// or http:// from docker_registry if present
    if docker_registry:
        docker_registry = docker_registry.replace('https://', '').replace('http://', '')
    
    if docker_registry.endswith('/'):
        docker_registry = docker_registry[:-1]

    compatibility = workspace_json.get('compatibility', [])
    
    # Validate that compatibility is a list
    if not isinstance(compatibility, list):
        print(f"  ⚠ Invalid compatibility format (not a list): {type(compatibility)}")
        return None
    
    pullable_images = []

    for entry in compatibility:
        # Handle both dict and non-dict entries
        if not isinstance(entry, dict):
            print(f"  ⚠ Invalid compatibility entry format (not a dict): {type(entry)}")
            return None
            
        image = entry.get('image')
        if image:
            # if not image.startswith(f"{docker_registry}/"):
            #     image = f"{docker_registry}/{image}"
            result = skopeo_inspect(image, docker_registry=docker_registry)
            if not result:
                print(f"Image {image} is not pullable")
                continue

            print(f"Image {image} is pullable")
            # if pullable, add to pullable_images
            pullable_images.append(entry)

    if pullable_images:
        workspace_json['compatibility'] = pullable_images
        return workspace_json
    return None




stop_after = 100
per_page = 100

if DEBUG:
    stop_after = 1
    per_page = 5

# get all search results
def get_search_results():
    results = []
    page = 1
    print(f"Searching for repositories matching query: {SEARCH_QUERY}")
    while True:
        if stop_after and page > stop_after:
            break
        # print(f"Page: {page}")
        params = {
            'q': SEARCH_QUERY,
            'per_page': per_page,
            'page': page
        }
        # response = requests.get(SEARCH_URL, params=params)
        response = make_request(SEARCH_URL, params=params)
        if response.status_code != 200:
            print(f"Error fetching page {page}: {response.status_code}")
            break
        data = response.json()
        items = data.get('items', [])
        if not items:
            break
        REPOS.extend(item['full_name'] for item in items)
        # also track stars and latest commit timestamp
        for item in items:
            REPO_STATS[item['full_name']] = {
                'stars': item['stargazers_count'],
                'last_commit': item.get('pushed_at', 'Unknown')
            }
        page += 1
    print(f"Total repositories found: {len(REPOS)}")
    return REPOS

def parse_repo(repo_full_name):
    # go through the repo and go to "workspaces" folder
    contents_url = f"https://api.github.com/repos/{repo_full_name}/contents/workspaces"
    response = make_request(contents_url)
    # print(response.json())
    if response.status_code != 200:
        print(f"Skipping {repo_full_name}: No 'workspaces' folder found")
        return []
    
    # in the workspaces folder, find all folders
    items = response.json()
    workspace_folders = [item for item in items if item['type'] == 'dir']
    # print("FOLDERS: \n", workspace_folders)
    
    # Skip repo if workspaces folder has no subfolders
    if not workspace_folders:
        print(f"Skipping {repo_full_name}: 'workspaces' folder has no subfolders")
        return []

    workspace_data = []
    # in each folder, get workspace.json file
    for folder in workspace_folders:
        folder_url = folder['url']
        # folder_response = requests.get(folder_url)
        folder_response = make_request(folder_url)
        if folder_response.status_code != 200:
            print(f"Skipping folder {folder['name']}: Unable to access folder contents")
            continue
        folder_items = folder_response.json()
        workspace_file = next((item for item in folder_items if item['name'] == 'workspace.json'), None)
        if not workspace_file:
            print(f"Skipping subfolder {folder['name']}: No workspace.json file found")
            continue
        
        # file_response = requests.get(workspace_file['download_url'])
        file_response = make_request(workspace_file['download_url'])
        if file_response.status_code == 200:
            try:
                workspace_json = file_response.json()
                
                # Check for profanity first
                if check_profanity_in_workspace(workspace_json, folder['name']):
                    print(f"Skipping subfolder {folder['name']}: Profanity detected in workspace data")
                    continue
                
                # Then check image pullability
                pullable_workspace_json = check_image_pullability(workspace_json)
                if pullable_workspace_json is None:
                    print(f"Skipping subfolder {folder['name']}: No pullable images found in workspace.json")
                    continue
                workspace_json = pullable_workspace_json
                # print("WORKSPACE JSON: \n", workspace_json)
                temp = {}
                temp[folder['name']] = workspace_json
                workspace_data.append(temp)
            except json.JSONDecodeError:
                print(f"Skipping subfolder {folder['name']}: Invalid JSON in workspace.json")
                continue

    return workspace_data

def parse_workspace_json(workspace_json):
    # get all json as it is
    return workspace_json


def get_github_pages_url(repo_full_name):
    pages_url = f"https://api.github.com/repos/{repo_full_name}/pages"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": "Bearer " + GITHUB_PAT
    }
    response = make_request(pages_url)
    if response.status_code == 200:
        data = response.json()
        return data.get('html_url', None)
    return None

def save_results_to_file(results, filename='search_results.json'):
    with open(filename, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"Results saved to {filename}")


def parse_categories(all_workspace_data):
    # get all categories from all workspaces
    print("Parsing categories from all workspaces...")
    categories = set()
    for repo, data in all_workspace_data.items():
        workspaces = data.get('workspaces', [])
        for workspace in workspaces:
            for ws_name, ws_data in workspace.items():
                ws_categories = ws_data.get('categories', [])
                categories.update(ws_categories)
    return list(categories)

if __name__ == "__main__":
    # Create directory called "generated" if it doesn't exist
    if not os.path.exists('generated'):
        os.makedirs('generated')
    search_results = get_search_results()
    save_results_to_file(search_results, 'generated/repos.json')
    all_workspace_data = {}
    for repo in search_results:
        print(f"\n------------\nParsing repository: {repo}")
        workspace_data = parse_repo(repo)
        print(f"Found {len(workspace_data)} workspaces in {repo}")
        if workspace_data:
            pages_url = get_github_pages_url(repo)
            if not pages_url:
                pages_url = "No GitHub Pages URL"
                continue
            temp = {}
            temp['github_pages'] = pages_url
            temp['stars'] = REPO_STATS.get(repo, {}).get('stars', 0)
            temp['last_commit'] = REPO_STATS.get(repo, {}).get('last_commit', 'Unknown')
            temp['workspaces'] = workspace_data
            all_workspace_data[repo] = temp
    
    save_results_to_file(all_workspace_data, filename='generated/community_workspaces.json')
    # all_categories = parse_categories(all_workspace_data)
    save_results_to_file(all_categories, filename='generated/categories.json')

    
    