from flask import Flask, render_template, request, session, redirect, flash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json, os, math
from flask_mail import Mail

#load the config the file for changable parametes
with open("config.json",'r') as c:
	params = json.load(c)["params"]

app = Flask(__name__)

app.secret_key ="super-secret-key"
app.config['UPLOAD_FOLDER'] = params['upload_location']

#email configuration to send updates
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'kiruifelix03@gmail.com'
app.config['MAIL_PASSWORD'] = 'xbod caxt ommg zexd'
app.config['MAIL_DEFAULT_SENDER'] = 'kiruifelix03@gmail.com'



mail = Mail(app)

local_server = params["local_server"]

if local_server == "True":
	app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
	app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']

db = SQLAlchemy(app)


class Contact(db.Model):
	"""
	Setup sql table "Contact" to store contact details
	"""
	sno = db.Column(db.Integer, primary_key=True,nullable=False)
	name = db.Column(db.String(80),nullable=False)
	email = db.Column(db.String(80), nullable=False)
	phone_num = db.Column(db.String(12), unique=False, nullable=True)
	mes = db.Column(db.String(120), nullable=False)
	date = db.Column(db.String(12), nullable=False)

class Posts(db.Model):
	"""
	Setup sql table "Posts" to store blogs to be displayed on website
	"""
	sno = db.Column(db.Integer, primary_key=True,nullable=False)
	title = db.Column(db.String(20),nullable=False)
	sub_heading = db.Column(db.String(50),nullable=True)
	content = db.Column(db.String(80), nullable=False)
	slug = db.Column(db.String(12), unique=True, nullable=False)
	img_file = db.Column(db.String(120), nullable=True)
	date = db.Column(db.String(12), nullable=False)

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
	return render_template("post.html",params=params, post=post)


@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
	if ('user' in session and session['user'] == params['admin_user']):
		posts= Posts.query.all()
		return render_template('dashboard.html', params=params, posts=posts)

	if request.method=="POST":
		username = request.form.get('username')
		password = request.form.get('pass')

		if (username == params['admin_user'] and password == params['admin_password']):
			session['user'] = username
			posts= Posts.query.all()
			return render_template('dashboard.html', params=params, posts = posts)

	
	return render_template("login.html",params=params)

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

@app.route("/edit/<string:sno>", methods=['GET','POST'])
def edit(sno):
	if ('user' in session and session['user']==params['admin_user']):
		if request.method=='POST':
				
			title = request.form.get('title')
			sub_heading = request.form.get('sub_heading')
			content =request.form.get('content')
			slug = request.form.get('slug')
			img_file = request.form.get('img_file')
			date = datetime.now()
			
			if sno=='0':
				post = Posts(title=title, sub_heading=sub_heading, content=content, slug=slug, img_file=img_file, date=date)
				db.session.add(post)
				db.session.commit()
				flash("New post added successfully!!","success")
			
			else:
				post = Posts.query.filter_by(sno=sno).first()
				post.title = title
				post.sub_heading = sub_heading
				post.content= content 
				post.slug=slug
				post.img_file =img_file
				post.date =date
				db.session.commit()
				flash("Post edited successfully!!","success")
				return redirect('/edit/'+sno)

		post = Posts.query.filter_by(sno=sno).first()
		
		return render_template('edit.html', params=params, post=post,sno=sno)


@app.route('/uploader',methods=['GET','POST'])
def upload():
	if('user' in session and session['user']==params['admin_user']):
		if request.method=='POST':
			f = request.files['file1']
			f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
			
			return "Uploaded Successfully"

@app.route('/logout')
def logout():
	session.pop('user')
	return redirect('/dashboard')

@app.route('/delete/<string:sno>')
def delete(sno):
	if('user' in session and session['user']== params['admin_user']):
		
		post = Posts.query.filter_by(sno=sno).first()
		db.session.delete(post)
		db.session.commit()
		flash("Post deleted successfully!!","success")
	return redirect("/dashboard")

if __name__ == "__main__":
	with app.app_context():
		db.create_all()
	app.run(debug=True)




