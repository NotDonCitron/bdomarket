"""
File I/O utilities for JSON and CSV files.
"""
import json
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json(file_path: str | Path, default: Any = None) -> Any:
    """
    Load JSON file with error handling.
    
    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or is invalid
        
    Returns:
        Parsed JSON data or default value
        
    Example:
        >>> data = load_json('config.json', default={})
    """
    path = Path(file_path)
    
    if not path.exists():
        return default
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to load {file_path}: {e}")
        return default


def save_json(file_path: str | Path, data: Any, indent: int = 2) -> bool:
    """
    Save data to JSON file.
    
    Args:
        file_path: Path to JSON file
        data: Data to save
        indent: Indentation level (default: 2)
        
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> save_json('config.json', {'region': 'eu'})
    """
    path = Path(file_path)
    
    # Create parent directories if needed
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except (IOError, TypeError) as e:
        print(f"Error: Failed to save {file_path}: {e}")
        return False


def load_csv(file_path: str | Path, has_header: bool = True) -> List[Dict[str, str]]:
    """
    Load CSV file as list of dictionaries.
    
    Args:
        file_path: Path to CSV file
        has_header: Whether first row is header (default: True)
        
    Returns:
        List of dictionaries (one per row)
        
    Example:
        >>> rows = load_csv('portfolio.csv')
        >>> print(rows[0]['item_name'])
    """
    path = Path(file_path)
    
    if not path.exists():
        return []
    
    try:
        with open(path, 'r', encoding='utf-8', newline='') as f:
            if has_header:
                reader = csv.DictReader(f)
                return list(reader)
            else:
                reader = csv.reader(f)
                return [{'col' + str(i): val for i, val in enumerate(row)} for row in reader]
    except (IOError, csv.Error) as e:
        print(f"Warning: Failed to load {file_path}: {e}")
        return []


def save_csv(
    file_path: str | Path,
    data: List[Dict[str, Any]],
    fieldnames: Optional[List[str]] = None
) -> bool:
    """
    Save list of dictionaries to CSV file.
    
    Args:
        file_path: Path to CSV file
        data: List of dictionaries to save
        fieldnames: Column names (inferred from first row if None)
        
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> data = [{'name': 'Item1', 'price': 1000}, {'name': 'Item2', 'price': 2000}]
        >>> save_csv('items.csv', data)
    """
    if not data:
        return True
    
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    
    try:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        return True
    except (IOError, csv.Error) as e:
        print(f"Error: Failed to save {file_path}: {e}")
        return False


def append_csv(
    file_path: str | Path,
    row: Dict[str, Any],
    fieldnames: Optional[List[str]] = None
) -> bool:
    """
    Append single row to CSV file.
    
    Args:
        file_path: Path to CSV file
        row: Dictionary to append
        fieldnames: Column names (required if file doesn't exist)
        
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> append_csv('portfolio.csv', {'timestamp': '2025-10-25', 'item': 'X'})
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    file_exists = path.exists()
    
    if not file_exists and fieldnames is None:
        fieldnames = list(row.keys())
    
    try:
        with open(path, 'a', encoding='utf-8', newline='') as f:
            if fieldnames is None:
                # Read existing fieldnames
                with open(path, 'r', encoding='utf-8') as rf:
                    reader = csv.reader(rf)
                    fieldnames = next(reader)
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(row)
        return True
    except (IOError, csv.Error) as e:
        print(f"Error: Failed to append to {file_path}: {e}")
        return False


def ensure_file_exists(file_path: str | Path, default_content: str = "") -> bool:
    """
    Ensure file exists, create with default content if not.
    
    Args:
        file_path: Path to file
        default_content: Content to write if file doesn't exist
        
    Returns:
        True if file exists or was created successfully
        
    Example:
        >>> ensure_file_exists('data/portfolio.csv', 'timestamp,item_id,qty\\n')
    """
    path = Path(file_path)
    
    if path.exists():
        return True
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(default_content)
        return True
    except IOError as e:
        print(f"Error: Failed to create {file_path}: {e}")
        return False

