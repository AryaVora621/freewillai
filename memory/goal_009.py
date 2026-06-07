# Goal: Create a web dashboard for Raspberry Pi projects using Flask

class Dashboard:
    def __init__(self):
        self.port = 5000
        self.app = None

    def create_app(self):
        import flask
        app = flask.Flask(__name__)
        @app.route('/dashboard')
        def dashboard():
            return "Welcome to my Raspberry Pi project dashboard!"
        self.app = app
        if __name__ == '__main__':
            app.run(port=self.port)

def start_dashboard():
    dashboard = Dashboard()
    dashboard.create_app()