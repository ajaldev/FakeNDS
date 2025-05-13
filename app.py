import datetime
import os
import pickle
import sqlite3
import pytesseract
from PIL import Image
from deep_translator import GoogleTranslator
from sklearn.feature_extraction.text import TfidfVectorizer
from flask import Flask, render_template, redirect, request, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'fakenews'


import pytesseract

# Manually set the path to the tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Check if it's working
print(pytesseract.get_tesseract_version())  

# SQLite database setup
DATABASE = 'fakenews.db'

#Public Section Start

@app.route('/')
def home():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
   
    c.execute("SELECT * FROM news")
    newsss=c.fetchall()
    print(newsss)
    data={"newsss":newsss}
    return render_template('index.html',**data)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/authe', methods=['GET', 'POST'])
def authe():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT id, username, type FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
       
        if user:
            session['user_id'] = user[0]  # Store user_id in session
            session['username'] = user[1]  # Store username in session
            session['type'] = user[2] # Store User Type in session
            if session['type']:
                return redirect(url_for('home'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
    return render_template('login.html')


@app.route('/register_db', methods=['GET', 'POST'])
def register_db():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        mobile = request.form['mobile']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = c.fetchone()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
        else:
            c.execute("INSERT INTO users (name, email, mobile, username, password, type) VALUES (?, ?, ?, ?, ?, ?)",
                      (name, email, mobile, username,  password,"user"))
            conn.commit()
            conn.close()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

#Public Section End

#User Section Start

@app.route('/user_feedback')
def user_feedback():
    return render_template('feedback.html')

@app.route('/user_feedback_db', methods=['GET', 'POST'])
def user_feedback_db():
    if request.method == 'POST':
        feedback=request.form['feedback']
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO feedback (username, feedback, date) VALUES (?, ?, ?)",
                    (session['username'],feedback,datetime.datetime.now()))
        conn.commit()
        conn.close()
        return redirect(url_for('user_feedback'))
    return redirect(url_for('user_feedback'))

@app.route('/news_checking')
def news_checking():
    return render_template('news_checking.html')

@app.route('/news_single/<int:id>')
def news_single(id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM news WHERE id=?",(id,))
    news=c.fetchone()
    data={"news":news}
    return render_template('news_single.html',**data)


@app.route('/user_profile')
def user_profile():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?",(session['user_id'],))
    user=c.fetchone()
    data={"user":user}
    return render_template('profile.html',**data)


@app.route('/change_password')
def change_password():
    if request.method == 'POST':
        old=request.form['old']
        new=request.form['new']
        cn=request.form['new']
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("UPDATE users SET password=? WHERE id=?",
                    (new,session['username']))
        conn.commit()
        conn.close()
    return redirect(url_for(user_profile))

#User Section End



#Admin Section Start
@app.route('/add_news', methods=['GET', 'POST'])
def add_news():
    return render_template('add_news.html')


@app.route('/add_news_db', methods=['GET', 'POST'])
def add_news_db():
    if request.method == 'POST':
        head=request.form['head']
        cat=request.form['cat']
        auther=request.form['auther']
        desc=request.form['desc']
        img=request.files['img']
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        if img:
            image_path = os.path.join('static/upload', img.filename)
            img.save(image_path)
           
        c.execute("INSERT INTO news (headline, category, description, date_time,auther,img) VALUES (?, ?, ?, ?, ?, ?)",
                    (head, cat, desc, datetime.datetime.now(), auther,image_path))
        conn.commit()
        conn.close()
        return redirect(url_for('add_news'))
    return redirect(url_for('add_news'))

@app.route('/delete_news/<int:id>', methods=['GET', 'POST'])
def delete_news(id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM news WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect(url_for('all_news'))
    

@app.route('/all_news', methods=['GET', 'POST'])
def all_news():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM news")
    newsss=c.fetchall()
    conn.commit()
    conn.close()
    data={"newsss":newsss}
    return render_template('news_list.html',**data)
    
@app.route('/admin_feedback', methods=['GET', 'POST'])
def admin_feedback():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM feedback")
    feedback=c.fetchall()
    conn.commit()
    conn.close()
    data={"feedback":feedback}
    return render_template('admin_feedback.html',**data)


#Admin Section End

#Prediction Section Start

# Load trained model and vectorizer
with open('model.pkl', 'rb') as model_file:
    model = pickle.load(model_file)

with open('vectorizer.pkl', 'rb') as vectorizer_file:
    vectorizer = pickle.load(vectorizer_file)

# OCR function to extract text from image
def extract_text_from_image(image_path):
    text = pytesseract.image_to_string(Image.open(image_path))
    return text.strip()

# Translate non-English text to English
def translate_to_english(text, source_lang):
    return GoogleTranslator(source=source_lang, target="en").translate(text)

# Preprocess text for prediction
def preprocess_text(text):
    return vectorizer.transform([text])

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    prediction_result = None
    confidence = None
    image_path=None
    #print("Model:", model)
    if request.method == 'POST':
        text_input = request.form['news_text']
        language = request.form['language']
        uploaded_file = request.files['news_image']
        print(uploaded_file)
        if uploaded_file:
            image_path = os.path.join('static/query_uploads', uploaded_file.filename)
            uploaded_file.save(image_path)
            text_input = extract_text_from_image(image_path)
            print(text_input)

        if text_input:
            if language and language != 'en':
                text_input = translate_to_english(text_input, language)

            #text_input = str(text_input)
            #transformed_text = preprocess_text(text_input)
            #print(transformed_text)
            # Convert sparse matrix to dense array
            #transformed_text = transformed_text.toarray()
            #print("Transformed Type:", type(transformed_text))
            #print("Transformed Shape:", transformed_text.shape)
            
            prediction = model.predict([text_input])  # No need to convert
            if hasattr(model, "predict_proba"):
                confidence = round(model.predict_proba([text_input])[:, 1][0], 4)
            prediction_result = 'Fake News' if prediction == 0 else 'Real News'
            print("result:",prediction_result)
    return render_template('news_checking.html', result=prediction_result, confidence=confidence,image_path=image_path,language=language,text_input=text_input)
#Prediction Section End

# Logout Start
@app.route('/logout')
def logout():
    session['user_id']=""
    session['username']=""
    session['type']=""
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)