import logging
import os
import socket
import time

# Configure logging
logging.basicConfig(
    filename='logs/check_db.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def is_container_healthy(container_name):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = os.environ.get("PORT")
    
    try:
        sock.connect((container_name, int(port)))
    except:
        return False
    else:
        sock.close()
        return True

def main():
    container_name = os.environ.get("IP")

    start_time = time.time()
    
    while time.time() - start_time < 120:  # Check for 2 minutes
        if is_container_healthy(container_name):
            logging.info(f"The container '{container_name}' is healthy.")
            return
        else:
            logging.info(f"The container '{container_name}' is not healthy.")
            time.sleep(10)  # Sleep for 10 seconds before the next check
            # Add code here to shut down the current container (e.g., sys.exit())

    logging.info(f"Timeout reached. The container '{container_name}' has not become healthy within 2 minutes. Starting anyway")

if __name__ == "__main__":
    main()
