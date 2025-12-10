

from flask import Flask
from flask_cors import CORS


#use blueprint to use functions in other files
from user import user_bp
from admin_event import admin_event_bp
from ticket_booking import ticket_booking_bp
from admin_order import admin_order_bp
# instantiate the app
app = Flask(__name__)
#app.config.from_object(__name__)


# enable CORS
#CORS(app, resources={r'/*': {'origins': '*'}})
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Session-ID"])
app.config['SECRET_KEY'] = 'admin'


# register blueprint
app.register_blueprint(user_bp)
app.register_blueprint(admin_event_bp)
app.register_blueprint(ticket_booking_bp)
app.register_blueprint(admin_order_bp)

if __name__ == '__main__':
    app.run(port=5001)
