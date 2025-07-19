from flask import Flask
from config import LocalDevelopment
from models import db, User, Role
from flask_security import Security, SQLAlchemyUserDatastore, auth_required
from flask_caching import Cache

def createApp():
    app = Flask(__name__, template_folder='frontend', static_folder='frontend', static_url_path='/static')
    app.config.from_object(LocalDevelopment)
    
    # Initialize extensions
    db.init_app(app)
    cache = Cache(app)
    app.cache = cache  # Make cache available to resources
    
    # Initialize Flask-Security
    datastore = SQLAlchemyUserDatastore(db, User, Role)
    app.security = Security(app, datastore=datastore, register_blueprint=False)
    
    # Create app context
    app.app_context().push()
    
    # Register API routes AFTER app context is created
    from resources.child_resources import child_api
    from resources.parent_resources import parent_api
    child_api.init_app(app)
    parent_api.init_app(app)
    
    return app

# Create app instance
app = createApp()

# Import other modules that need app context
import init_data
import routes

if __name__ == '__main__':
    app.run(debug=True)