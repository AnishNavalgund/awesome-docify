import os
import re
import subprocess
import time
from threading import Timer

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Updated regex to include main.py, schemas.py, and all .py files in app/routes
WATCHER_REGEX_PATTERN = re.compile(
    r"(main\.py|schemas\.py|routes/.*\.py|ai_engine_service/.*\.py|prompts\.py)$"
)
APP_PATH = "app"


class MyHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.debounce_timer = None
        self.last_modified = 0
        self.uvicorn_process = None

    def on_modified(self, event):
        if not event.is_directory and WATCHER_REGEX_PATTERN.search(
            os.path.relpath(event.src_path, APP_PATH)
        ):
            current_time = time.time()
            if current_time - self.last_modified > 1:
                self.last_modified = current_time
                if self.debounce_timer:
                    self.debounce_timer.cancel()
                self.debounce_timer = Timer(1.0, self.execute_command, [event.src_path])
                self.debounce_timer.start()

    def execute_command(self, file_path):
        print(f"File {file_path} has been modified and saved.")
        self.run_mypy_checks()
        self.run_openapi_schema_generation()
        self.restart_application()

    def run_mypy_checks(self):
        """Run mypy type checks and print output."""
        print("Running mypy type checks...")
        result = subprocess.run(
            ["uv", "run", "mypy", "app"],
            capture_output=True,
            text=True,
            check=False,
        )
        print(result.stdout, result.stderr, sep="\n")
        print(
            "Type errors detected! We recommend checking the mypy output for "
            "more information on the issues."
            if result.returncode
            else "No type errors detected."
        )

    def run_openapi_schema_generation(self):
        """Run the OpenAPI schema generation command."""
        print("Proceeding with OpenAPI schema generation...")
        try:
            subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    "-m",
                    "commands.generate_openapi_schema",
                ],
                check=True,
            )
            print("OpenAPI schema generation completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while generating OpenAPI schema: {e}")

    def restart_application(self):
        """Restart the uvicorn application."""
        print("Restarting application...")
        try:
            # Find and kill existing uvicorn processes
            subprocess.run(
                ["pkill", "-f", "uvicorn.*app.main:app"],
                capture_output=True,
                text=True,
                check=False,
            )

            # Wait a moment for the process to stop
            time.sleep(2)

            # Start a new uvicorn process
            self.uvicorn_process = subprocess.Popen(
                [
                    "uv",
                    "run",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "8000",
                    "--reload",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            print("Application restarted successfully.")
        except Exception as e:
            print(f"Error restarting application: {e}")


if __name__ == "__main__":
    observer = Observer()
    observer.schedule(MyHandler(), APP_PATH, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
