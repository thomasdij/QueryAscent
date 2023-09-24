def truncate_content(content, length=500):
    return content[:length] + "..." if len(content) > length else content
