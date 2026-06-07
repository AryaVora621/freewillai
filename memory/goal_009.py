# Goal: Create a web dashboard for Raspberry Pi projects using Flask
import threading
from flask import Flask, render_template_string

class Dashboard:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route('/dashboard')
        def dashboard():
            html = """
            <h1>Raspberry Pi Project Dashboard</h1>
            <p>Welcome to your Raspberry Pi projects!</p>
            """
            return render_template_string(html)

    def start(self):
        # Run Flask in a separate thread so it doesn't block the main program
        threading.Thread(target=self.app.run, kwargs={'host': self.host,
                                                     'port': self.port,
                                                     'debug': False},
                         daemon=True).start()

# Example usage
if __name__ == '__main__':
    dash = Dashboard()
    dash.start()
    print(f"Dashboard running at http://{dash.host}:{dash.port}/dashboard")
    # Keep the main thread alive
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Shutting down dashboard.")
# STATUS: complete