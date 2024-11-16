from flask import Flask, render_template,request,redirect,url_for,jsonify
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry, WKTElement
from shapely.geometry import Point
from sqlalchemy import Float, func


import psycopg2
# print(psycopg2.__version__)

app = Flask(__name__)

#Connecting with database
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:Sanket9284@localhost:5432/flaskDB"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#defining class for the Schema of the table
class BktList(db.Model):
    __tablename__ = 'bkt_list'
    sno = db.Column(db.Integer, primary_key = True)
    pName = db.Column(db.String(200),nullable = False)
    pDesc = db.Column(db.String(1000),nullable = False)
    pGeom = db.Column(Geometry(geometry_type='POINT'))
    pLatLong = db.Column(db.String(1000))

    def __repr__(self) -> str:
        return f"{self.sno} - {self.pName}"

#Homepage Featched from index.html in Templates Folder
@app.route("/", methods=['GET','POST'])
def app_here():
    if request.method == "POST":
        # Get form data
        desc = request.form.get("desc")
        p_name = request.form.get("placeName")
        x = request.form.get("xCor")
        y = request.form.get("yCor")

        if desc and p_name :
                # Create geometry and lat-long string
                locationString = f"{x} {y}"
                if len(x) ==0:
                    latitude = None
                    longitude = None
                    point = None
                else:
                    latitude = float(x)
                    longitude = float(y)
                    point = WKTElement(f"POINT({longitude} {latitude})", srid=4326)

                # Add data to the database
                new_entry = BktList(pName=p_name, pDesc=desc, pGeom=point, pLatLong=locationString)
                db.session.add(new_entry)
                db.session.commit()

            # Redirect to avoid resubmission
        return redirect(url_for("app_here"))

    table = BktList.query.all()
    # for place in table:
    #     place.pGeom_wkt = place.pGeom.wkt
    return render_template('index.html',Data = table)


# For loading the table in leaflet from existing data 
@app.route('/get_markers', methods=['GET'])
def get_markers():
    # Get all points from the table
    products = BktList.query.all()

    # Format the data
    markers = []
    for product in products:
        lat, lon = product.pLatLong.split(' ')
        markers.append({
            'name': product.pName,
            'desc': product.pDesc,
            'FID':product.sno,
            'lat': float(lat),
            'lon': float(lon),
            
        })
    return jsonify(markers)


#adding single marker
@app.route('/update/<int:sno>', methods=['GET','POST'])
def get_marker(sno):

    if request.method=='POST':
        # Get form data
        desc = request.form.get("desc")
        p_name = request.form.get("placeName")
        x = request.form.get("lat")
        y = request.form.get("long")
        point = None
        locationString = None

        if desc and p_name :
            # Create geometry and lat-long string
            locationString = f"{x} {y}"
            if len(x) ==0:
                x = None
                y = None
                point = None
            else:
                x = float(x)
                y = float(y)
                point = WKTElement(f"POINT({x} {y})", srid=4326)

        # Add data to the database
        update_entry = BktList.query.filter_by(sno=sno).first()
        update_entry.sno = sno
        update_entry.pName = p_name
        update_entry.pDesc = desc
        update_entry.pGeom = point
        update_entry.pLatLong = locationString

        db.session.add(update_entry)
        db.session.commit()
        return redirect('/')

    # Get all points from the table
    mark = BktList.query.filter_by(sno=sno).first()
    # Format the data
    oldPoint = []
    lat, lon = mark.pLatLong.split(' ')
    lat = round(float(lat),5)  
    long = round(float(lon),5) 
    oldPoint = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],  # GeoJSON uses [longitude, latitude] order
                },
                "properties": {
                    "name": mark.pName,
                    "desc": mark.pDesc,
                    "lat": lat,
                    "lon": sno,
                }
            }
        ]
    }

    return render_template('update.html',table = mark, lat=lat,long=long,oldPoint=oldPoint) 


#delete
@app.route("/delete/<int:sno>")
def delete(sno):
    table = BktList.query.filter_by(sno=sno).first()
    db.session.delete(table)
    db.session.commit()

    return redirect("/")



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(debug=True, port=8000)