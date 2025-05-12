# Entry point for dev
#create db only once
from app import create_app
from app.extensions import db
from app import models

app = create_app()

#create DB tables only once
with app.app_context():
    pass
    #COMMENT THIS DURING PRODUCTION
    #db.drop_all()
    #db.create_all()


    #UNCOMMENT THIS DURING PRODUCTION
    db.metadata.create_all(bind=db.engine, checkfirst=True)

if __name__ == '__main__':
    app.run(debug=True)