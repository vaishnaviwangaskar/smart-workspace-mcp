# main.py
# main.py
import os
from pathlib import Path
from fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("Smart Workspace")

# Define a safe root directory the AI is allowed to access
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", os.getcwd())).resolve()

def is_safe_path(target_path: Path) -> bool:
    """Ensure the AI cannot break out of the designated directory."""
    try:
        target_path.resolve().relative_to(WORKSPACE_ROOT)
        return True
    except ValueError:
        return False

@mcp.tool()
def list_workspace_files(relative_path: str = ".") -> str:
    """Lists all files and directories in the workspace or a subdirectory."""
    target_dir = (WORKSPACE_ROOT / relative_path).resolve()
    
    if not is_safe_path(target_dir) or not target_dir.exists():
        return "Error: Access denied or path does not exist."
    
    try:
        items = os.listdir(target_dir)
        output = [f"Contents of {relative_path}:"]
        for item in items:
            if item.startswith('.'):  # Skip hidden files like .git
                continue
            path = target_dir / item
            display_type = "[DIR]" if path.is_dir() else "[FILE]"
            output.append(f"  {display_type} {item}")
        return "\n".join(output)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@mcp.tool()
def read_workspace_file(relative_file_path: str) -> str:
    """Reads the full text contents of a specific file in the workspace."""
    target_file = (WORKSPACE_ROOT / relative_file_path).resolve()
    
    if not is_safe_path(target_file) or not target_file.is_file():
        return "Error: Access denied or file does not exist."
    
    try:
        with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def write_workspace_file(relative_file_path: str, content: str) -> str:
    """Creates a new file or overwrites an existing file with content inside the workspace."""
    target_file = (WORKSPACE_ROOT / relative_file_path).resolve()
    
    if not is_safe_path(target_file):
        return "Error: Access denied. Cannot write outside the workspace root."
    
    try:
        # Create directories if they don't exist
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote file to: {relative_file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
def search_workspace_text(query: str) -> str:
    """Searches for a specific text string case-insensitively inside all files in the workspace."""
    results = []
    
    for root, _, files in os.walk(WORKSPACE_ROOT):
        # Skip hidden folders like .git or .venv
        if any(part.startswith('.') for part in Path(root).parts):
            continue
            
        for file in files:
            file_path = Path(root) / file
            if not file_path.is_file():
                continue
                
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if query.lower() in line.lower():
                            rel_path = file_path.relative_to(WORKSPACE_ROOT)
                            results.append(f"{rel_path}:{line_num}: {line.strip()}")
            except Exception:
                continue  # Skip unreadable binary files
                
    if not results:
        return f"No matches found for '{query}'."
    
    return "\n".join(results[:50])  # Limit output to top 50 matches

if __name__ == "__main__":
    mcp.run(transport="stdio")
