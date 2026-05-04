def read_sql_file(file_path):
    """
    Reads an SQL query from a file and returns it as a string.
    
    Parameters:
    file_path (str): The path to the SQL file.
    
    Returns:
    str: The SQL query read from the file.
    """
    try:
        with open(file_path, 'r') as file:
            sql_query = file.read()
        return sql_query
    except Exception as e:
        print(f"Error reading SQL file: {e}")
        return None