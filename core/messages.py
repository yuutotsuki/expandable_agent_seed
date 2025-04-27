# Message templates
MESSAGES = {
    'welcome': "Welcome to File Search Assistant v1.0.0\nType 'exit' or 'quit' to end the session",
    'file_found': "File found:",
    'files_found': "Related files found:",
    'no_files': "No files were found. Please try again with different keywords or check the file extension.",
    'type_open': 'Type "open" to open this file',
    'enter_number': "Please enter the number of the file you want to open.",
    'file_opened': "✓ File opened successfully",
    'file_error': "Error opening file:",
    'no_file_selected': "No file selected.",
    'invalid_number': "Invalid number. Please try again.",
    'search_tips': [
        "Make sure your spelling is correct.",
        "Try different or more general keywords.",
        "Try removing the file extension to broaden the search.",
        "Check if the file exists in the search directory."
    ],
    'error_occurred': "Error occurred:"
}

# Function to get message
def get_message(key: str) -> str:
    return MESSAGES[key]