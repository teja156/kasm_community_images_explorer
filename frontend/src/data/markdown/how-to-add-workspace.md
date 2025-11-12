You can install workspaces on your Kasm in multiple ways

## Method 1: [Add via Registry URL](https://docs.kasm.com/docs/1.18.0/guide/workspace_registry#3rd-party-registry)

1. **Navigate to Workspaces**
   - Log into your Kasm admin panel
   - Go to **Workspaces** in the left sidebar

2. **Add Workspace**
   - Click the **Add Workspace** button
   - Select **Registry** tab

3. **Enter Registry URL**
   - Copy the **Kasm Registry** URL from the workspace card
   - Paste it into the registry field
   - Click **Install** to install the registry and load all workspace entries

4. **Select & Install**
   - Go back to the **Available Workspaces** tab
   - In **Filter by Registry**, click on the Installed Registry to only show workspaces from that registry
   - Click **Install** to add the workspace of your choice


## Method 2: [Manual Import](https://docs.kasm.com/docs/1.18.0/guide/workspaces#add--edit-workspaces)

1. **Copy Image Name**
   - Find the **Image Name** on the workspace card
   - Click the copy icon to copy the Docker image name

2. **Create Workspace Manually**
   - On your Kasm admin panel, Go to **Workspaces** → **Add Workspace**
   - Fill in workspace details:
     - **Name**: Give it a friendly name
     - **Image**: Paste the copied Docker image name
     - Other details from the `workspace.json` file
   - Configure additional settings as needed
   - Click **Submit**

---

## ⚠️ Security Warning

**You should only install registries from 3rd parties that you trust**, and even then before installing a workspace you should check to see what commands are being executed.

There are a couple of ways this can be done:

1. On Kasm, click on a workspace tile and instead of clicking install, click on **edit**.
2. From the Registry page where you got the Workspace Registry Link, clicking on one of the workspaces takes you to a page that displays all the JSON for that workspace (you can also get this JSON from the Explorer app directly).

Either of these 2 options allows you to see everything that is being set. **Pay particular attention to anything in the Docker Run Config Override (JSON) field** (`run_config` in the workspace JSON) **or the Docker Exec Config (JSON) field** (`exec_config` in the workspace JSON) as these fields allow arbitrary commands to be run. If either of these fields are populated and you are unsure of what they are doing, **ask the 3rd party to clarify before blindly installing**.
