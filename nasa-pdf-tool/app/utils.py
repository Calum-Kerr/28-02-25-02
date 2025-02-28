# app/utils.py
"""
Utility functions for the NASA PDF Tool.
Includes helper functions for secure file handling, such as scheduling file deletion.
"""

import os
import threading
import time
import logging

def delete_file(file_path):
    """
    Safely deletes the specified file if it exists.
    
    :param file_path: The full path to the file to be deleted.
    :raises: Logs any errors encountered during deletion.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"File successfully deleted: {file_path}")
    except Exception as e:
        logging.error(f"Error deleting file {file_path}: {e}")

def schedule_file_deletion(file_path, delay):
    """
    Schedule the deletion of a file after a given delay (in seconds).
    
    This function starts a background daemon thread that waits for the specified delay
    and then deletes the file. This ensures that uploaded files and their associated
    data are removed promptly, minimizing security risks.
    
    :param file_path: The full path to the file to be deleted.
    :param delay: The delay in seconds before the file is deleted.
    """
    def deletion_task():
        try:
            # Wait for the specified delay before deletion.
            time.sleep(delay)
            delete_file(file_path)
        except Exception as e:
            logging.error(f"Scheduled deletion failed for {file_path}: {e}")

    # Start a daemon thread for deletion so it won't block the main process.
    t = threading.Thread(target=deletion_task, daemon=True)
    t.start()