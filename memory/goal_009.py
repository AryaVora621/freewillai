# Goal: Create a web dashboard for Raspberry Pi projects using Flask
def create_dashboard():
    import flask
    app = flask.Flask(__name__)
    @app.route('/dashboard')
    def dashboard():
        return "Welcome to my Raspberry Pi project dashboard!"
    
    if __name__ == '__main__':
        app.run(port=5000)

class Dashboard:
    def __init__(self):
        self.port = 5000
        self.app = None

def start_dashboard(app, port=5000):
    create_dashboard()
    app.run(port=port)