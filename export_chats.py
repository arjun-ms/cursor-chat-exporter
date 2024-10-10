import os
import sqlite3
import json
from pathlib import Path

# Define the path to the workspaceStorage directory
workspace_storage_path = Path(r"C:\Users\arjun\AppData\Roaming\Cursor\User\workspaceStorage")

# Define the output directory where exported chats and prompts will be saved
output_directory = Path(r"C:\Users\arjun\Documents\ExportedCursorChats")
output_directory.mkdir(parents=True, exist_ok=True)

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

def export_chats_from_state_db(state_db_path, output_dir):
    """
    Connect to the state.vscdb SQLite database and extract chats and prompts.
    Save the extracted data as JSON files in the output directory.
    """
    try:
        conn = sqlite3.connect(state_db_path)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        
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
                    
                    # Define the output file path
                    output_file = key_dir / f"{state_db_path.parent.name}_{key}_extracted.json"
                    
                    # Write the extracted conversation to the file
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(extracted_conversation, f, ensure_ascii=False, indent=4)
                    
                    print(f"Exported extracted user and AI conversations from {state_db_path} to {output_file}")
                else:
                    print(f"No non-empty conversations found in {state_db_path}. Skipping file creation.")
        
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
    
    # Iterate through each subfolder (MD5 hash named)
    for subfolder in workspace_storage_path.iterdir():
        if subfolder.is_dir():
            state_db_path = subfolder / "state.vscdb"
            if state_db_path.exists():
                print(f"Processing {state_db_path}")
                export_chats_from_state_db(state_db_path, output_directory)
            else:
                print(f"state.vscdb not found in {subfolder}. Skipping.")
    
    print("Export completed.")

if __name__ == "__main__":
    main()