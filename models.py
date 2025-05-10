from app import db

class User(db.Model):
    User_id = db.Column(db.Integer, primary_key=True)
    First_Name = db.Column(db.String(80), nullable=False)
    Last_Name =  db.Column(db.String(80), nullable=False)
    Phone_Number = db.Column(db.String(80), nullable=False)
    
def __repr__(self):
    return f"<User {self.First_Name} {self.Last_Name} {self.Phone_Number}>"


class items(db.Model):
    Item_Id =db.Column(db.Integer, primary_key=True)
    Item_Name = db.Column(db.String(80), nullable=False)
    Item_Price= db.Column(db.Integer, nullable=False)
    Item_Description = db.Column(db.String(500), nullable=False)

def __repr__(self):
    return f"<Item {self.Item_Name} {self.Item_Price}>"