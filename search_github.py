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

# load whitelist
with open('profanity_whitelist.json', 'r') as f:
    profanity_whitelist = json.load(f)

# Load profanity filter word list
profanity.load_censor_words(whitelist_words=profanity_whitelist)

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

IMAGE_NAME_PREFIX_FILTERS = [
    "kasmweb/"
]


def should_skip_image(image_name, docker_registry=None):
    """Return True when the image belongs to a blocked registry prefix."""
    if not image_name:
        return False

    image_name = image_name.strip()
    candidates = [image_name]

    if docker_registry:
        docker_registry = docker_registry.strip()
        if docker_registry and not image_name.startswith(f"{docker_registry}/"):
            candidates.append(f"{docker_registry}/{image_name}")

    for candidate in candidates:
        if any(candidate.startswith(prefix) for prefix in IMAGE_NAME_PREFIX_FILTERS):
            return True

    return False

# Statistics tracking
STATS = {
    'total_repos': 0,
    'profanity_filtered_workspaces': 0,
    'pullable_workspaces': 0,
    'unpullable_workspaces': 0,
    'blocked_registry_images': 0,
    'invalid_registry_urls': 0,
    'truncated_compatibility_workspaces': 0,
    'skopeo_timeouts': 0,
    'cached_image_hits': 0
}

# Security and performance limits
MAX_COMPATIBILITY_ENTRIES = 10

# Cache for skopeo image inspections (persists during script execution)
INSPECTED_IMAGES = {}


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
    # Check cache first to avoid redundant inspections
    cache_key = f"{docker_registry}/{image_full_name}" if docker_registry else image_full_name
    if cache_key in INSPECTED_IMAGES:
        STATS['cached_image_hits'] += 1
        return INSPECTED_IMAGES[cache_key]
    
    # very hacky, could be improved
    cmd = ["skopeo", "inspect", "--raw", f"docker://{image_full_name}"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if result.returncode != 0:
            print(f"Error inspecting image {image_full_name}")
            print("Trying with registry prefix..")
            if docker_registry:
                cmd = ["skopeo", "inspect", "--raw", f"docker://{docker_registry}/{image_full_name}"]
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
                    if result.returncode != 0:
                        print(f"Error inspecting image {docker_registry}/{image_full_name}")
                        INSPECTED_IMAGES[cache_key] = False
                        return False
                    INSPECTED_IMAGES[cache_key] = True
                    return True
                except subprocess.TimeoutExpired:
                    print(f"Timeout inspecting image {docker_registry}/{image_full_name}")
                    STATS['skopeo_timeouts'] += 1
                    INSPECTED_IMAGES[cache_key] = False
                    return False
            INSPECTED_IMAGES[cache_key] = False
            return False
        INSPECTED_IMAGES[cache_key] = True
        return True
    except subprocess.TimeoutExpired:
        print(f"Timeout inspecting image {image_full_name}")
        STATS['skopeo_timeouts'] += 1
        INSPECTED_IMAGES[cache_key] = False
        return False


def normalize_workspace_json(workspace_json, folder_name):
    """
    Normalize workspace.json to handle both structure types.
    This is ONLY for validation purposes - returns a normalized copy for checking.
    
    Structure 1: Single object with compatibility as array of {version, image, uncompressed_size_mb}
    Structure 2: Single object with 'name' field and compatibility as array of version strings
    
    Args:
        workspace_json: The workspace.json content (should be a dict)
        folder_name: The folder name to use as workspace name
    
    Returns:
        dict: Normalized workspace data for validation, or None if invalid format
    """
    # workspace.json should be a dict (single workspace object)
    if not isinstance(workspace_json, dict):
        return None
    
    # Check if it's Structure 2 (has 'name' field and compatibility is array of strings)
    if 'name' in workspace_json and 'friendly_name' in workspace_json:
        compatibility = workspace_json.get('compatibility', [])
        
        # Check if compatibility is a list of strings (Structure 2)
        if compatibility and isinstance(compatibility, list) and len(compatibility) > 0:
            if isinstance(compatibility[0], str):
                # Structure 2 - convert to Structure 1 format for validation
                workspace_copy = workspace_json.copy()
                image_name = workspace_copy.get('name', '')
                uncompressed_size = workspace_copy.get('uncompressed_size_mb', 0)
                
                converted_compatibility = []
                for version in compatibility:
                    converted_compatibility.append({
                        'version': version,
                        'image': image_name,
                        'uncompressed_size_mb': uncompressed_size
                    })
                workspace_copy['compatibility'] = converted_compatibility
                
                # Wrap with folder name as key
                return {folder_name: workspace_copy}
    
    # Structure 1: Standard format with compatibility as array of dicts
    # Return as-is, wrapped with folder name
    return {folder_name: workspace_json}


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
            STATS['profanity_filtered_workspaces'] += 1
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
        print(f"Invalid compatibility format (not a list): {type(compatibility)}")
        return None
    
    # Limit compatibility entries to prevent DoS
    original_count = len(compatibility)
    if original_count > MAX_COMPATIBILITY_ENTRIES:
        print(f"Limiting compatibility entries from {original_count} to {MAX_COMPATIBILITY_ENTRIES}")
        compatibility = compatibility[:MAX_COMPATIBILITY_ENTRIES]
        STATS['truncated_compatibility_workspaces'] += 1
    
    pullable_images = []
    unpullable_count = 0

    for entry in compatibility:
        # Handle both dict and non-dict entries
        if not isinstance(entry, dict):
            print(f"Invalid compatibility entry format (not a dict): {type(entry)}")
            return None
            
        image = entry.get('image')
        if image:
            if should_skip_image(image, docker_registry=docker_registry):
                print(f"Skipping image {image}: matches blocked registry prefix")
                STATS['blocked_registry_images'] += 1
                continue
            # if not image.startswith(f"{docker_registry}/"):
            #     image = f"{docker_registry}/{image}"
            result = skopeo_inspect(image, docker_registry=docker_registry)
            if not result:
                print(f"Image {image} is not pullable")
                unpullable_count += 1
                continue

            # print(f"Image {image} is pullable")
            # if pullable, add to pullable_images
            pullable_images.append(entry)

    if pullable_images:
        workspace_json['compatibility'] = pullable_images
        STATS['pullable_workspaces'] += 1
        return workspace_json
    
    if unpullable_count > 0:
        STATS['unpullable_workspaces'] += 1
    return None


def filter_original_workspace_json(original_workspace_json, pullable_workspace_json):
    """
    Filter the original workspace JSON to only include pullable compatibility entries.
    Preserves the original format (old or new structure).
    
    Args:
        original_workspace_json: The original workspace.json (any format)
        pullable_workspace_json: The normalized workspace.json with filtered compatibility (new format)
    
    Returns:
        dict: Filtered original workspace JSON, or None if no pullable entries
    """
    if pullable_workspace_json is None:
        return None
    
    # Create a copy of the original to avoid modifying it
    filtered = original_workspace_json.copy()
    
    # Get pullable images from normalized format
    pullable_compatibility = pullable_workspace_json.get('compatibility', [])
    if not pullable_compatibility:
        return None
    
    # Extract the image names/versions from pullable entries
    pullable_images = {entry.get('image') for entry in pullable_compatibility if entry.get('image')}
    pullable_versions = {entry.get('version') for entry in pullable_compatibility if entry.get('version')}
    
    # Check original format type
    original_compatibility = original_workspace_json.get('compatibility', [])
    
    if not original_compatibility:
        return None
    
    # Determine format: old (string array) or new (object array)
    if isinstance(original_compatibility[0], str):
        # Old format: compatibility is array of version strings
        # Filter by matching versions
        filtered_compat = [v for v in original_compatibility if v in pullable_versions]
        if not filtered_compat:
            return None
        filtered['compatibility'] = filtered_compat
    else:
        # New format: compatibility is array of objects with version/image
        # Filter by matching images
        filtered_compat = [
            entry for entry in original_compatibility 
            if entry.get('image') in pullable_images
        ]
        if not filtered_compat:
            return None
        filtered['compatibility'] = filtered_compat
    
    return filtered


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
                original_workspace_json = file_response.json()
                
                # Normalize workspace.json format for validation only
                normalized_workspace = normalize_workspace_json(original_workspace_json, folder['name'])
                if normalized_workspace is None:
                    print(f"Skipping subfolder {folder['name']}: Unrecognized workspace.json format")
                    continue
                
                # normalized_workspace is a dict: {folder_name: workspace_data}
                # Extract the workspace name and data
                ws_name = list(normalized_workspace.keys())[0]
                ws_data = normalized_workspace[ws_name]
                
                # Check for profanity
                if check_profanity_in_workspace(ws_data, ws_name):
                    print(f"Skipping workspace {ws_name}: Profanity detected in workspace data")
                    continue
                
                # Check image pullability on normalized data
                pullable_workspace_json = check_image_pullability(ws_data)
                if pullable_workspace_json is None:
                    print(f"Skipping workspace {ws_name}: No pullable images found in workspace.json")
                    continue
                
                # Filter the original workspace.json to only include pullable entries
                filtered_workspace_json = filter_original_workspace_json(original_workspace_json, pullable_workspace_json)
                if filtered_workspace_json is None:
                    print(f"Skipping workspace {ws_name}: No pullable compatibility entries after filtering")
                    continue
                
                # Save the FILTERED original workspace.json (preserves original format)
                temp = {}
                temp[ws_name] = filtered_workspace_json
                workspace_data.append(temp)
                        
            except json.JSONDecodeError:
                print(f"Skipping subfolder {folder['name']}: Invalid JSON in workspace.json")
                continue

    return workspace_data

def parse_workspace_json(workspace_json):
    # get all json as it is
    return workspace_json


def is_valid_http_url(url_string):
    """
    Validate that URL is HTTP or HTTPS only (prevents XSS via javascript:, data:, etc.)
    
    Args:
        url_string: The URL string to validate
    
    Returns:
        bool: True if valid HTTP/HTTPS URL, False otherwise
    """
    if not url_string or not isinstance(url_string, str):
        return False
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url_string)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except Exception:
        return False


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
        html_url = data.get('html_url', None)
        
        # Validate URL to prevent XSS attacks
        if html_url and is_valid_http_url(html_url):
            return html_url
        else:
            if html_url:
                print(f"Invalid GitHub Pages URL for {repo_full_name}: {html_url}")
                STATS['invalid_registry_urls'] += 1
            return None
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
    STATS['total_repos'] = len(search_results)
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

    # Print summary statistics
    print("\n" + "="*60)
    print("EXECUTION SUMMARY")
    print("="*60)
    print(f"Total repositories found: {STATS['total_repos']}")
    print(f"Workspaces filtered out due to profanity: {STATS['profanity_filtered_workspaces']}")
    print(f"Pullable workspaces: {STATS['pullable_workspaces']}")
    print(f"Unpullable workspaces: {STATS['unpullable_workspaces']}")
    print(f"Images skipped due to blocked registries: {STATS['blocked_registry_images']}")
    print(f"Invalid registry URLs: {STATS['invalid_registry_urls']}")
    print(f"Workspaces with truncated compatibility entries: {STATS['truncated_compatibility_workspaces']}")
    print(f"Skopeo inspect timeouts: {STATS['skopeo_timeouts']}")
    print(f"Cached image hits (avoided redundant checks): {STATS['cached_image_hits']}")
    print("="*60)