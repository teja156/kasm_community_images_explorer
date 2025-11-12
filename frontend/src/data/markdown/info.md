This explorer automatically discovers community Kasm workspaces from GitHub repositories. Your workspace might not be listed for several reasons:

## 1. Repository Not Discoverable
Make sure your repository includes the discovery identifier `KASM-REGISTRY-DISCOVERY-IDENTIFIER` in the README.md file (This comes by default if you created the template from the [Kasm Workspaces Registry Template](https://github.com/kasmtech/workspaces_registry_template)). Also, make sure your repository is public.

## 2. Images Not Pullable
All Docker images defined in your workspace.json must be publicly accessible and pullable. Private or inaccessible images are filtered out and only publicly pullable images are listed.

## 3. Profanity
If your workspace name, description, or categories contain profanity, it will be filtered out.

## 4. Recently Added
The explorer updates every 24 hours. If you just added your workspace, it will not appear until the next update cycle.

For more information, check out [how this app works](https://github.com/teja156/kasm_community_images_explorer/blob/main/README.md).
