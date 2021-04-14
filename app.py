from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename  # for file uploader
import json
from datetime import datetime
import os
import math

# for use config.json file
with open('config.json', 'r') as c:
    params = json.load(c)["params"]


app = Flask(__name__)

# set the secret key n u can write any secret key u want
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/flaskblog'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Contacts(db.Model):
    # sno,name, email, phone_num, message, date
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),  nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)


class Posts(db.Model):
    # sno,name, email, phone_num, message, date
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80),  nullable=False)
    sub_heading = db.Column(db.String(80),  nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    img_file = db.Column(db.String(12), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)


@app.route('/')
def home():
    posts = Posts.query.filter_by().all()
    # if ek page main mera 2 post han n total 10 post so 5 page bann sakta han so i will take greatest integer for that we will do floor
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    # Pagination logic (make new n previous functionality in home page)
    page = request.args.get('page')
    # means mera str(page) ek no. han
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)

    posts = posts[(page-1)*int(params['no_of_posts']): (page-1) *
                  int(params['no_of_posts']) + int(params['no_of_posts'])]
    # Pagination logic starts
    # first
    if(page == 1):
        prev = "#"
        next = "/?page=" + str(page+1)
    # last
    elif(page == last):
        prev = "/?page=" + str(page-1)
        next = "#"
    # middle
    else:
        prev = "/?page=" + str(page-1)
        next = "/?page=" + str(page+1)

    # [0:params['no_of_posts']] -> we write this becaz we have to show only five posts in our home page otherwise home page becomes lengthy n in no_of_posts we write 5 in config.json

    # posts = Posts.query.filter_by().all()[0:params['no_of_posts']]
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route('/about')
def about_page():
    return render_template('about.html', params=params)


# for admin
@app.route('/login', methods=['GET', 'POST'])
def dashboard():
    # if user is already login than
    # agar user already session main han and jo session user han bo han admin than usse dashboard.html main bhej do
    if ('user' in session and session['user'] == params['admin_user']):
        # posts saare aa jaenge admin panel main
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == 'POST':
        # if both username n password agar match ho jae config.json ke username n password ko than we will give access to login page
        # request.form will get from login.html form in name attribute
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username == params['admin_user'] and userpass == params['admin_password']):
            # set the session variable
            session['user'] = username
            # posts saare aa jaenge admin panel main
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)

    # otherwise aap login karo
    return render_template('login.html', params=params)


@app.route('/post/<string:post_slug>', methods=['GET'])
def post_page(post_slug):
    # Posts.query.filter_by(slug=post_slug).first() means post ke andhar jao query karo n usmain aap check karo slug is equals to post_slug
    # we write this becaz db se data read karne ke liye
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


# for make our edit button functionality
@app.route('/edit/<string:sno>', methods=['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            title = request.form.get('title')
            sub_heading = request.form.get('sub_heading')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            # for add new post
            if sno == '0':
                post = Posts(title=title, sub_heading=sub_heading, slug=slug,
                             content=content, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()

            # if my sno is not 0 than i will edit the existing post
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.slug = slug
                post.content = content
                post.sub_heading = sub_heading
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/' + sno)
        post = Posts.query.filter_by(sno=sno).first()

        return render_template('edit.html', params=params,  post=post, sno=sno)


@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    # koi person agar directly hamara url ko access kar raha han hum logg usse nahi karne denge
    if ('user' in session and session['user'] == params['admin_user']):
        if(request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(
                app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "uploaded successfull"


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/login')


@app.route('/delete/<string:sno>', methods=['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/login')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if(request.method == 'POST'):
        # Add entry to the db

        # fetch from db
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        # add entry to the db
        # lhs part come from class which we made above n rhs come from above
        # sno will take automatically becaz we do auto increment so atleast we will put 1 data from our own in phpmyadmin
        entry = Contacts(name=name, email=email,
                         phone=phone, message=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
    return render_template('contact.html', params=params)


if __name__ == "__main__":
    app.run(debug=True)
