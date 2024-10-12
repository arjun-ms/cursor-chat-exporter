import os
import sqlite3
import json
from pathlib import Path
import platform
from pprint import pprint

# # Define the path to the workspaceStorage directory
# workspace_storage_path = Path(r"C:\Users\arjun\AppData\Roaming\Cursor\User\workspaceStorage")

# # Define the output directory where exported chats and prompts will be saved
# output_directory = Path(r"C:\Users\arjun\Documents\ExportedCursorChats")
# output_directory.mkdir(parents=True, exist_ok=True)

# Define the SQL query to extract prompts and chat data
sql_query = """
SELECT
    rowid,
    [key],
    value
FROM
    ItemTable
WHERE
    [key] IN ('aiService.prompts', 'workbench.panel.aichat.view.aichat.chatdata')
"""

def get_default_workspace_storage_path():
    system = platform.system()
    home = Path.home()
    
    if system == "Windows":
        return home / "AppData" / "Roaming" / "Cursor" / "User" / "workspaceStorage"
    elif system == "Darwin":  # macOS
        return home / "Library" / "Application Support" / "Cursor" / "User" / "workspaceStorage"
    elif system == "Linux":
        return home / ".config" / "Cursor" / "User" / "workspaceStorage"
    else:
        return None

def get_user_input(prompt, default):
    user_input = input(f"{prompt} (default: {default}): ").strip()
    return user_input if user_input else default

# Get the default workspace storage path
default_workspace_storage_path = get_default_workspace_storage_path()

# Get user input for workspace storage path
workspace_storage_path = Path(get_user_input(
    "Enter the path to the workspaceStorage directory",
    str(default_workspace_storage_path)
))

# Get user input for output directory
default_output_directory = Path.home() / "Documents" / "ExportedCursorChats"
output_directory = Path(get_user_input(
    "Enter the path for the output directory",
    str(default_output_directory)
))
output_directory.mkdir(parents=True, exist_ok=True)

# Modify the get_user_input for output format
output_format = get_user_input(
    "Choose output format (markdown/raw/json)",
    "markdown"
).lower()

def extract_user_and_ai_conversation(data):
    """
    Extract user queries and AI responses from chat data.
    """
    extracted_data = []
    
    for tab in data.get("tabs", []):
        for bubble in tab.get("bubbles", []):
            if bubble.get("type") == "user":
                user_message = bubble.get("text", "").strip()
            elif bubble.get("type") == "ai":
                ai_message = bubble.get("text", "").strip()
                if user_message or ai_message:  # Only add non-empty conversations
                    extracted_data.append({"user_query": user_message, "ai_response": ai_message})
    
    return extracted_data

def format_conversation(conversation, format_type):
    if format_type == "markdown":
        formatted = "# Exported Chat\n\n"
        for entry in conversation:
            formatted += f"## User Query\n\n{entry['user_query']}\n\n"
            formatted += f"## AI Response\n\n{entry['ai_response']}\n\n"
            formatted += "---\n\n"
    elif format_type == "raw":
        formatted = "Exported Chat\n\n"
        for entry in conversation:
            formatted += f"User Query:\n{entry['user_query']}\n\n"
            formatted += f"AI Response:\n{entry['ai_response']}\n\n"
            formatted += "---\n\n"
    elif format_type == "json":
        return json.dumps(conversation, indent=2)
    return formatted

def export_chats_from_state_db(state_db_path, output_dir, format_type):
    """
    Connect to the state.vscdb SQLite database and extract chats and prompts.
    Save the extracted data as JSON files in the output directory.
    """
    try:
        conn = sqlite3.connect(state_db_path)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        
        print(f"\n--------------------\n\nProcessing {state_db_path}")
        print(f"Found {len(rows)} relevant entries")

        # Process each row
        for row in rows:
            rowid, key, value = row
            try:
                data = json.loads(value)
            except json.JSONDecodeError:
                print(f"Warning: JSON decode error in {state_db_path} for key '{key}'. Skipping.")
                continue

            # Extract user queries and AI responses if key matches chat data
            if key == 'workbench.panel.aichat.view.aichat.chatdata':
                extracted_conversation = extract_user_and_ai_conversation(data)
                
                # Only save if there's non-empty content
                if extracted_conversation:
                    # Define a subdirectory based on the key
                    key_dir = output_dir / key.replace('.', '_')
                    key_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Define the output file extension based on the format type
                    file_extension = {
                        "markdown": "md",
                        "raw": "txt",
                        "json": "json"
                    }.get(format_type, "txt")
                    
                    output_file = key_dir / f"{state_db_path.parent.name}_{key}_extracted.{file_extension}"
                    
                    # Format the conversation based on the chosen format
                    formatted_content = format_conversation(extracted_conversation, format_type)
                    
                    # Write the formatted content to the file
                    with open(output_file, 'w', encoding='utf-8') as f:
                        if format_type == "json":
                            json.dump(extracted_conversation, f, ensure_ascii=False, indent=2)
                        else:
                            f.write(formatted_content)
                    
                    print(f"Exported to {output_file}")
                else:
                    print(f"No conversations with content found in {state_db_path}.\nSkipping file creation.")
        
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error while processing {state_db_path}: {e}")
    except Exception as e:
        print(f"Unexpected error while processing {state_db_path}: {e}")

def main():
    # Check if workspace_storage_path exists
    if not workspace_storage_path.exists() or not workspace_storage_path.is_dir():
        print(f"Error: The workspaceStorage directory does not exist at {workspace_storage_path}")
        return
    
    print(f"\nStarting export process...")
    print(f"Workspace storage path: {workspace_storage_path}")
    print(f"Output directory: {output_directory}")
    print(f"Output format: {output_format}")

    # Iterate through each subfolder (MD5 hash named)
    for subfolder in workspace_storage_path.iterdir():
        if subfolder.is_dir():
            state_db_path = subfolder / "state.vscdb"
            if state_db_path.exists():
                # print(f"Processing {state_db_path}")
                export_chats_from_state_db(state_db_path, output_directory, output_format)
            else:
                print(f"state.vscdb not found in {subfolder}. Skipping.")
    
    print("\n-----\nExport completed.")

    print(f"Exported data can be found in: {output_directory}\n-----\n")

if __name__ == "__main__":
    main()
