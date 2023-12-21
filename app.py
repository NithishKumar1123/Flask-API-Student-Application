from flask import Flask
from flask import render_template
from flask_restful import Resource, Api, fields, marshal_with, reqparse
from flask import request, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException
from flask import make_response
import json

app = None
api = None
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api_database.sqlite3'
db = SQLAlchemy()
db.init_app(app)
api = Api(app)
app.app_context().push()

course_output = {
    "course_id" : fields.Integer,
    "course_name" : fields.String,
    "course_code" : fields.String,
    "course_description" : fields.String
}

student_output = {
    "student_id" : fields.Integer,
    "first_name" : fields.String,
    "last_name" : fields.String,
    "roll_number" : fields.String
}

enrollment_output = {
    "enrollment_id" : fields.Integer,
    "student_id" : fields.Integer,
    "course_id" : fields.Integer
}

update_course = reqparse.RequestParser()
update_course.add_argument('course_name')
update_course.add_argument('course_code')
update_course.add_argument('course_description')

update_student = reqparse.RequestParser()
update_student.add_argument('first_name')
update_student.add_argument('last_name')
update_student.add_argument('roll_number')

update_enrollment = reqparse.RequestParser()
update_enrollment.add_argument('course_id')

class Student(db.Model):
    __tablename__ = 'student'
    student_id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    roll_number = db.Column(db.String, unique = True, nullable = False)
    first_name = db.Column(db.String, nullable = False)
    last_name = db.Column(db.String)
    courses = db.relationship("Course", secondary = "enrollment")

class Course(db.Model):
    __tablename__ = 'course'
    course_id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    course_code = db.Column(db.String, unique = True, nullable = False)
    course_name = db.Column(db.String, nullable = False)
    course_description = db.Column(db.String)

class Enrollment(db.Model):
    __tablename__ = 'enrollment'
    enrollment_id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.student_id"), nullable = False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.course_id"), nullable = False)

class InternalServerException(HTTPException):
    def __init__(self, status_code):
        self.response = make_response('', status_code)

class NotFound(HTTPException):
    def __init__(self, status_code):
        self.response = make_response('', status_code)

class Exception(HTTPException):
    def __init__(self, status_code, error_code, error_message):
        message = {"error_code" : error_code, "error_message" : error_message}
        self.response = make_response(json.dumps(message), status_code)

class Exist(HTTPException):
    def __init__(self, status_code):
        self.response = make_response('', status_code)

class CourseAPI(Resource):
    @marshal_with(course_output)
    def get(self, course_id):
        data = None
        data = Course.query.filter_by(course_id = course_id).first()
        if data:
            return data
        else:
            raise NotFound(status_code = 404)

    @marshal_with(course_output)
    def put(self, course_id):
        data = None
        args = update_course.parse_args()
        course_name = args.get("course_name", None)
        course_code = args.get("course_code", None)
        course_description = args.get("course_description", None)
        if course_name is None:
            raise Exception(status_code = 400, error_code = "COURSE001", error_message = "Course Name is required")
        if course_code is None:
            raise Exception(status_code = 400, error_code = "COURSE002", error_message = "Course Code is required")
        data = Course.query.filter_by(course_id = course_id).first()
        if data is None:
            raise NotFound(status_code = 404)
        else:
            data.course_name = course_name
            data.course_code = course_code
            if course_description:
                data.course_description = course_description
            db.session.commit()
            return data
  
    def delete(self, course_id):
        data = None
        data = Course.query.filter_by(course_id = course_id).first()
        if data is None:
            raise NotFound(status_code = 404) 
        else:
            enroll = Enrollment.query.filter_by(course_id = course_id).all()
            for row in enroll:
                db.session.delete(row)
            db.session.delete(data)
            db.session.commit()
   
    @marshal_with(course_output)
    def post(self):
        args = update_course.parse_args()
        course_name = args.get("course_name", None)
        course_code = args.get("course_code", None)
        course_description = args.get("course_description", None)
        data = None
        if course_name is None:
            raise Exception(status_code = 400, error_code = "COURSE001", error_message = "Course Name is required")
        if course_code is None:
            raise Exception(status_code = 400, error_code = "COURSE002", error_message = "Course Code is required")
        data = Course.query.filter_by(course_code = course_code).first()
        if data:
            raise Exist(status_code = 409)
        else:
            new_course = Course(course_name = course_name, course_code = course_code, course_description = course_description)
            db.session.add(new_course)
            db.session.commit()
            data = Course.query.filter_by(course_code = course_code).first()
            return data, 201

class StudentAPI(Resource):
    @marshal_with(student_output)
    def get(self, student_id):
        data = None
        data = Student.query.filter_by(student_id = student_id).first()
        if data:
            return data
        else:
            raise NotFound(status_code = 404)

    @marshal_with(student_output)
    def put(self, student_id):
        data = None
        data = Student.query.filter_by(student_id = student_id).first()
        if data is None:
            raise NotFound(status_code = 404)
        else:
            args = update_student.parse_args()
            first_name = args.get("first_name", None)
            last_name = args.get("last_name", None)
            roll_number = args.get("roll_number", None)
            if roll_number is None:
                raise Exception(status_code = 400, error_code = "STUDENT001", error_message = "Roll Number required")
            if first_name is None:
                raise Exception(status_code = 400, error_code = "STUDENT002", error_message = "First Name is required")
            data.first_name = first_name
            data.roll_number = roll_number
            if last_name:
                data.last_name = last_name
            db.session.commit()
            return data

    def delete(self, student_id):
        data = None
        data = Student.query.filter_by(student_id = student_id).first()
        if data is None:
            raise NotFound(status_code = 404) 
        else:
            enroll = Enrollment.query.filter_by(student_id = student_id).all()
            for row in enroll:
                db.session.delete(row)
            db.session.delete(data)
            db.session.commit()

    @marshal_with(student_output)
    def post(self):
        args = update_student.parse_args()
        first_name = args.get("first_name", None)
        last_name = args.get("last_name", None)
        roll_number = args.get("roll_number", None)
        data = None
        if roll_number is None:
            raise Exception(status_code = 400, error_code = "STUDENT001", error_message = "Roll Number required")
        if first_name is None:
            raise Exception(status_code = 400, error_code = "STUDENT002", error_message = "First Name is required")
        data = Student.query.filter_by(roll_number = roll_number).first()
        if data:
            raise Exist(status_code = 409)
        else:
            new_student = Student(first_name = first_name, last_name = last_name, roll_number = roll_number)
            db.session.add(new_student)
            db.session.commit()
            data = Student.query.filter_by(roll_number = roll_number).first()
            return data, 201

class EnrollmentAPI(Resource):
    @marshal_with(enrollment_output)
    def get(self, student_id):
        data = None
        data = Student.query.filter_by(student_id = student_id).first()
        if data is None:
            raise Exception(status_code = 400, error_code = "ENROLLMENT002", error_message = "Student does not exist")
        else:
            data = None
            data = Enrollment.query.filter_by(student_id = student_id).all()
            if data:
                return data
            else:
                raise NotFound(status_code = 404)

    @marshal_with(enrollment_output)
    def post(self, student_id):
        args = update_enrollment.parse_args()
        course_id = args.get("course_id", None)
        data = None
        student = Student.query.filter_by(student_id = student_id).first()
        course = Course.query.filter_by(course_id = course_id).first()
        if course is None:
            raise Exception(status_code = 400, error_code = "ENROLLMENT001", error_message = "Course does not exist")
        if student is None:
            raise Exception(status_code = 400, error_code = "ENROLLMENT002", error_message = "Student does not exist")
        else:
            new_enrollment = Enrollment(student_id = student_id, course_id = course_id)
            db.session.add(new_enrollment)
            db.session.commit()
            data = Enrollment.query.filter_by(student_id = student_id).all()
            return data, 201
  
    def delete(self, student_id, course_id):
        data = None
        data = Enrollment.query.filter_by(student_id = student_id, course_id = course_id).first()
        if data is None:
            raise NotFound(status_code = 404) 
        else:
            db.session.delete(data)
            db.session.commit()

api.add_resource(CourseAPI, "/api/course", "/api/course/<int:course_id>")
api.add_resource(StudentAPI, "/api/student", "/api/student/<int:student_id>")
api.add_resource(EnrollmentAPI, "/api/student/<int:student_id>/course", "/api/student/<int:student_id>/course/<int:course_id>")

@app.route('/')
def index():
    students = Student.query.all()
    return render_template('index_page.html', students = students)

@app.route('/student/create', methods = ["GET", "POST"])
def create():
    if request.method == "GET":
        return render_template("student_create.html")
    else:
        roll = request.form["roll"]
        f_name = request.form["f_name"]
        l_name = request.form["l_name"]
        course_list = request.form.getlist("courses")
        data = Student.query.filter_by(roll_number = roll).all()
        if(data == []):
            new_student = Student(roll_number = roll, first_name = f_name, last_name = l_name)
            db.session.add(new_student)
            db.session.commit()
            if('course_1' in course_list):
                new_enrollment = Enrollment(student_id = new_student.student_id, course_id = 1)
                db.session.add(new_enrollment)
            if('course_2' in course_list):
                new_enrollment = Enrollment(student_id = new_student.student_id, course_id = 2)
                db.session.add(new_enrollment)
            if('course_3' in course_list):
                new_enrollment = Enrollment(student_id = new_student.student_id, course_id = 3)
                db.session.add(new_enrollment)
            if('course_4' in course_list):
                new_enrollment = Enrollment(student_id = new_student.student_id, course_id = 4)
                db.session.add(new_enrollment)
            db.session.commit()
            return redirect("/")
        else:
            return render_template("student_exist.html")

@app.route("/student/<int:student_id>/update", methods = ["GET", "POST"])
def update(student_id):
    if request.method == "GET":
        data = Student.query.filter_by(student_id = student_id)
        return render_template("student_update.html", student = data[0])
    else:
        f_name = request.form["f_name"]
        l_name = request.form["l_name"]
        course_list = request.form.getlist("courses")
        student = Student.query.filter_by(student_id = student_id).all()
        student[0].first_name = f_name
        student[0].last_name = l_name
        if('course_1' in course_list):
            enroll = Enrollment.query.filter_by(student_id = student_id, course_id = 1).all()
            if(enroll == []):
                update_enrollment = Enrollment(student_id = student_id, course_id = 1)
                db.session.add(update_enrollment)
        else:
            enroll = Enrollment.query.filter_by(student_id = student_id, course_id = 1).all()
            if(enroll != []):
                db.session.delete(enroll[0])
        if('course_2' in course_list):
            enroll = Enrollment.query.filter_by(student_id = student_id, course_id = 2).all()
            if(enroll == []):
                update_enrollment = Enrollment(student_id = student_id, course_id = 2)
                db.session.add(update_enrollment)
        else:
            enroll = Enrollment.query.filter_by(student_id = student_id, course_id = 2).all()
            if(enroll != []):
                db.session.delete(enroll[0])
        if('course_3' in course_list):
            enroll = Enrollment.query.filter_by(student_id = student_id, course_id = 3).all()
            if(enroll == []):
                update_enrollment = Enrollment(student_id = student_id, course_id = 3)
                db.session.add(update_enrollment)
        else:
            enroll = Enrollment.query.filter_by(student_id = student_id, course_id = 3).all()
            if(enroll != []):
                db.session.delete(enroll[0])
        if('course_4' in course_list):
            enroll = Enrollment.query.filter_by(student_id = student_id, course_id = 4).all()
            if(enroll == []):
                update_enrollment = Enrollment(student_id = student_id, course_id = 4)
                db.session.add(update_enrollment)
        else:
            enroll = Enrollment.query.filter_by(student_id = student_id, course_id = 4).all()
            if(enroll != []):
                db.session.delete(enroll[0])
        db.session.commit()
        return redirect("/")

@app.route("/student/<int:student_id>/delete")
def delete(student_id):
    enroll = Enrollment.query.filter_by(student_id = student_id).all()
    for row in enroll:
        db.session.delete(row)
    student = Student.query.filter_by(student_id = student_id).all()
    db.session.delete(student[0])
    db.session.commit()
    return redirect("/")

@app.route("/student/<int:student_id>")
def display(student_id):
    students = Student.query.filter_by(student_id = student_id).all()
    enroll = Enrollment.query.filter_by(student_id = student_id).all()
    courses = []
    for row in enroll:
        courses.append(Course.query.filter_by(course_id = row.course_id).one())
    return render_template("student_display.html", students = students, courses = courses)


if __name__ == '__main__':
    app.run(debug = True)