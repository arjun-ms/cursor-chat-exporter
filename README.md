# claude-chat-exporter

### changes to be done

- know the OS of user 
- Either fetch user's cursor workspace storage automatically or get input from the user
    - On Windows,  %APPDATA%\Cursor\User\workspaceStorage
    - On Mac,  /Users/YOUR_USERNAME/Library/Application Support/Cursor/User/workspaceStorage
    - On Linux,  /home/YOUR_USERNAME/.config/Cursor/User/workspaceStorage
- similarly for the output location
- format the response neatly
    - either in a markdown format or in simple raw text but more legible
