from flask import Flask, flash, redirect, render_template, \
     request, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import secrets

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///flask.db"
db = SQLAlchemy(app)
app.app_context().push()
app.secret_key =  secrets.token_hex(16)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=True, nullable=False)
    posts = db.relationship('Post', back_populates='host')
    comments = db.relationship('Comment', back_populates='person')
    def __repr__(self):
        return f"User('{self.id}', '{self.email}', '{self.username}', {self.password})"
    
class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    host = db.relationship('User', back_populates='posts')
    topic = db.Column(db.String(20), nullable=True)# unique=True,
    description = db.Column(db.Text, unique=True, nullable=True)
    comments = db.relationship('Comment', back_populates='post')
    created = db.Column(db.DateTime, default=datetime.now)
    def __repr__(self):
        return f"Post('{self.id}', '{self.topic}', '{self.description}')"

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)

    person_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    person = db.relationship('User', back_populates='comments')

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    post = db.relationship('Post', back_populates='comments')

    body = db.Column(db.Text, unique=True, nullable=True)
    created = db.Column(db.DateTime, default=datetime.now)
    def __repr__(self):
        return f"Post('{self.id}', '{self.body}', '{self.created}')"


#--------------------
    
@app.route('/')
@app.route('/home')
def home():
    posts_ = Post.query.order_by(Post.created.desc()).all()
    posts = []
    for post in posts_:
        if post.topic not in posts:
            posts.append(post.topic)
    

    users = User.query.all()
    return render_template('home.html', posts=posts, posts_=posts_, users=users)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username=request.form['username']
        password=request.form['password']
        user_ = User.query.filter_by(username=username).first()

        if str(user_) == 'None':
            flash('User does not exist!','error')
        else:
            if user_.password == password:
                session['username'] = username
                session['is_login'] = True
                flash('You were successfully logged in', 'success')
                return redirect(url_for('home'))
            else:
                flash('Incorrect password', 'error')

    return render_template('login_register.html')




@app.route('/register-page', methods=['POST'])
def register():
    username=request.form['username']
    email=request.form['email']

    check_username = User.query.filter_by(username=username).first()
    check_email = User.query.filter_by(email=email).first()

    if str(check_username) == 'None' and str(check_email) == 'None':
        db.session.add(User(email=request.form['email'], username=request.form['username'], password=request.form['password']))
        db.session.commit()

        session['username'] = username
        session['is_login'] = True

        flash('Successfully Registered', 'success')

        return redirect(url_for('home'))
    else:
        flash("Username or Email already exists!", 'error')
    return redirect(url_for('login'))



@app.route('/log-out')
def log_out():
    session.pop('username', None)
    session.pop('is_login', None)
    return redirect('/')
    



@app.route('/create-post', methods=['GET', 'POST'])
def create_post():
    if 'username' not in session:
        return redirect('/login')
    #
    if request.method == "POST":
        user = User.query.filter_by(username=session['username']).first()
        user_id = user.id
        db.session.add(Post(user_id=user_id, topic=request.form['topic'], description=request.form['description']))
        db.session.commit()
        return redirect('/home')

    posts_ = Post.query.order_by(Post.created.desc()).all()
    posts = []
    for post in posts_:
        if post.topic not in posts:
            posts.append(post.topic)

    return render_template('create_post.html', posts=posts)




@app.route('/post/<post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    if request.method == 'POST':
        if 'username' not in session:
            return redirect('/login')###########
        else:
            user = User.query.filter_by(username=session['username']).first()
            user_id = user.id
            db.session.add(Comment(person_id=user_id, post_id=post_id, body=request.form['comment']))
            db.session.commit()

    
    main_post = Post.query.get(post_id)

    comments = main_post.comments

    posts_ = Post.query.order_by(Post.created.desc()).all()
    posts = []
    for post in posts_:
        if post.topic not in posts:
            posts.append(post.topic)

    return render_template('show-post.html', main_post=main_post, comments=comments, posts=posts)




@app.route('/<subject>')
def filter(subject):
    filtered_posts = Post.query.filter_by(topic=subject)

    posts_ = Post.query.order_by(Post.created.desc()).all()
    posts = []
    for post in posts_:
        if post.topic not in posts:
            posts.append(post.topic)


    return render_template('filter-post.html', filtered_posts=filtered_posts, posts=posts)




@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect('/login')
    
    user = session['username']
    info = User.query.filter_by(username=user).first()
    posts = Post.query.filter_by(user_id=info.id).order_by(Post.created.desc()).all()
    return render_template('profile.html', info=info, posts=posts)



@app.route('/profile/comments')
def profile_comment():
    username = session['username']
    user = User.query.filter_by(username=username).first()

    comments = Comment.query.filter_by(person_id=user.id)
    return render_template('profile_comment.html', comments=comments, user=user)


@app.route('/user/<username>')
def user_post(username):
    flag = True
    flag1 = True

    user = User.query.filter_by(username=username).first()
    user_id = user.id

    user_posts = Post.query.filter_by(user_id=user_id).order_by(Post.created.desc()).all()
    if str(user_posts) == '[]':
        flag = False

    user_comment=Comment.query.filter_by(person_id=user_id).order_by(Comment.created.desc()).first()
    if str(user_comment) == 'None':
        flag1=False
    
    posts_ = Post.query.order_by(Post.created.desc()).all()
    posts = []
    for post in posts_:
        if post.topic not in posts:
            posts.append(post.topic)

    return render_template('user_post.html', user_posts=user_posts, user_comment=user_comment, posts=posts, username=username, flag=flag, flag1=flag1)


if __name__ == "__main__":
        app.run(debug=True)


#this is a comment updated
#another comment
#third comment of program
#final comment
#lets do that
