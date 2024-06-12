from flask import Flask, render_template, request, session, redirect, flash,url_for
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json, os, math
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,BooleanField,PasswordField
from wtforms.validators import DataRequired,Email,EqualTo,Length
from flask_login import login_user,logout_user,LoginManager,login_required
from flask_login import UserMixin,current_user


#load the config the file for changable parametes
with open("config.json",'r') as c:
	params = json.load(c)["params"]

app = Flask(__name__)

app.secret_key ="super-secret-key"
app.config['UPLOAD_FOLDER'] = params['upload_location']

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

login_manager.init_app(app)

#email configuration to send updates
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = params['sender']
app.config['MAIL_PASSWORD'] = params['password']
app.config['MAIL_DEFAULT_SENDER'] = params['sender']



mail = Mail(app)




app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']



db = SQLAlchemy(app)


class Contact(db.Model):
	"""
	Setup sql table "Contact" to store contact details
	"""
	id = db.Column(db.Integer, primary_key=True,nullable=False)
	name = db.Column(db.String(80),nullable=False)
	email = db.Column(db.String(80), nullable=False)
	phone_num = db.Column(db.String(12), unique=False, nullable=True)
	mes = db.Column(db.String(120), nullable=False)
	date = db.Column(db.String(12), nullable=False)

class Posts(db.Model):
	"""
	Setup sql table "Posts" to store blogs to be displayed on website
	"""
	id = db.Column(db.Integer, primary_key=True,nullable=False)
	title = db.Column(db.String(20),nullable=False)
	sub_heading = db.Column(db.String(50),nullable=True)
	content = db.Column(db.String(80), nullable=False)
	slug = db.Column(db.String(12), unique=True, nullable=False)
	img_file = db.Column(db.String(120), nullable=True)
	date = db.Column(db.String(12), nullable=False)

class User(db.Model,UserMixin):
	"""
	Set up sql table "Users to store users credentials for login and signing up"
	"""
	id = db.Column(db.Integer,primary_key=True,nullable=False)
	username = db.Column(db.String(50),nullable=False)
	password_hash = db.Column(db.String(120),nullable=False)
	email = db.Column(db.String(80), nullable=False)
	admin = db.Column(db.Boolean,default=False,nullable=False)

	def set_password(self, password):
		"""
		Hash the user's password using werkzeug.security.
		"""
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		"""
		Verify if the provided password matches the stored password.
		"""
		return check_password_hash(self.password_hash, password)

	def get_id(self):
		return str(self.id)


#Registration form
class RegistrationForm(FlaskForm):
	username = StringField('Username',validators=[Length(max=15,min=2),DataRequired()])
	email = StringField("Email",validators=[Email(),DataRequired(),Length(max=100)])
	password = PasswordField("Password",validators=[DataRequired(),Length(min=6)])
	confirm_password =PasswordField("Confirm Password",validators=[EqualTo('password')])
	admin = BooleanField('Admin')
	submit = SubmitField("Sign Up")
#Login form
class LoginForm(FlaskForm):
	username = StringField('Username')
	password = PasswordField("Password")
	submit = SubmitField("Login")

@app.route("/") #Homepage
def home():
	posts = Posts.query.filter_by().all()
	last = math.ceil(len(posts)/int(params['no_of_posts']))

	#pagination logic
	page = request.args.get('page')
	if not str(page).isnumeric():
		page = 1
	
	page = int(page)
	posts = posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]

	if page==1: #First Page
		prev = "#"
		nexxt = "/?page=" + str(page+1)
	elif page==last: #Last Page
		prev="/?page=" + str(page-1)
		nexxt = "#"
	else:  #Middle Page
		prev="/?page=" + str(page-1)
		nexxt = "/?page=" + str(page+1)

	return render_template("index.html",params=params,posts=posts,prev=prev, nexxt=nexxt, page=page, last=last)

@app.route("/post/<string:post_slug>", methods=["GET"])
def post_query(post_slug):
	post = Posts.query.filter_by(slug=post_slug).first()
	return render_template("post.html",params=params, post=post,current_user=current_user)


@app.route("/about")
def about():
	
	return render_template("about.html",params=params)

@app.route("/contact", methods=["GET","POST"])
def contact():
	if(request.method == "POST"):
		name = request.form.get("name")
		email = request.form.get("email")
		phone = request.form.get("phone")
		message = request.form.get("message")
		
		entry = Contact(name=name,email=email,phone_num=phone,mes=message,date=datetime.now())
		db.session.add(entry)
		db.session.commit()
		mail.send_message(f"New Message from {name} via {params['blog_heading']}",
						sender=email,
						recipients=[params['gmail_user']],
						body= message + "\n" + phone + "\n"+ email
					)
		flash("Thank you for writing to us, we'll get back to you at the earliest!", "success")
	return render_template("contact.html",params=params)

@app.route("/edit/<string:id>", methods=['GET','POST'])
def edit(id):
	#if ('user' in session and session['user']==params['admin_user']):
		if request.method=='POST':
				
			title = request.form.get('title')
			sub_heading = request.form.get('sub_heading')
			content =request.form.get('content')
			slug = request.form.get('slug')
			img_file = request.form.get('img_file')
			date = datetime.now()
			
			if id=='0':
				post = Posts(title=title, sub_heading=sub_heading, content=content, slug=slug, img_file=img_file, date=date)
				db.session.add(post)
				db.session.commit()
				flash("New post added successfully!!","success")
			
			else:
				post = Posts.query.filter_by(id=id).first()
				post.title = title
				post.sub_heading = sub_heading
				post.content= content 
				post.slug=slug
				post.img_file =img_file
				post.date =date
				db.session.commit()
				flash("Post edited successfully!!","success")
				return redirect('/edit/'+id)

		post = Posts.query.filter_by(id=id).first()
		
		return render_template('edit.html', params=params, post=post,id=id,current_user=current_user)



@app.route('/uploader',methods=['GET','POST'])
def upload():
	
		if request.method=='POST':
			f = request.files['file1']
			f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
			
			return "Uploaded Successfully"

@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('home'))

@app.route('/delete/<string:id>')
@login_required
def delete(id):

	post = Posts.query.filter_by(id=id).first()
	db.session.delete(post)
	db.session.commit()
	flash("Post deleted successfully!!","success")
	return redirect("/dashboard")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, password_hash=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash (f"{form.username.data} has been signed up successfuly", "success")
        login_user(user)
        return redirect(url_for('home'))
    else:
       flash("Check the Form fields and try again!","danger")
    return render_template('register.html',params=params, form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		username = form.username.data
		password = form.password.data
		user = User.query.filter_by(username=username).first()
		if user and user.password_hash==password:
			login_user(user)
			return redirect(url_for('home'))
			flash('Logged in successfully','success')
		else:
			flash('Check username or password and try again!')
			return render_template('login.html',params=params,form=form)
	return render_template('login.html',params=params,form=form)

@app.route("/dashboard")
@login_required
def dashboard():
	posts=Posts.query.all()
	return render_template("dashboard.html",params=params,posts=posts,current_user=current_user)


if __name__ == "__main__":
	with app.app_context():
		db.create_all()
	app.run(debug=True)




