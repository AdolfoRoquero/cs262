from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request
from forms import RegistrationForm, LoginForm, NewMessageForm
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required


app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

class User(UserMixin):
    def __init__(self, name):
        self.id = name

usernames = ['Adolfo', 'Leticia', 'Jacobo']
user_obj = [User(username) for username in usernames]


# Decorator such that the login_manager extension knows
# that this is the function to get a user by id
@login_manager.user_loader
def load_user(user_id):
    print("Load user")
    if user_id in usernames:
        obj_ind = usernames.index(user_id)
        return user_obj[obj_ind]
    return None

posts = [
    {
        'author': 'Corey Schafer',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 21, 2018'
    }
]


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/")
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('wall'))
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data in usernames:
            obj_ind = usernames.index(form.username.data)
            login_user(user_obj[obj_ind], remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('wall'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/wall")
@login_required
def wall():
    return render_template('wall.html', posts=posts)


@app.route("/message/new", methods=['GET', 'POST'])
@login_required
def new_message():
    form = NewMessageForm()
    if form.validate_on_submit():
        if True:
            flash('A message was sent', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('new_message.html', title='New Message', form=form)


if __name__ == '__main__':
    app.run(debug=True)
