from flask import Flask, render_template, send_file, request, redirect, url_for
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
import os
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message

app = Flask(__name__)

# Set the directory for uploaded files
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.realpath(__file__)),"C:\\Users\\91834\\OneDrive\\Desktop\\Customer SegementationFinal\\Code")

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '20at1a3149@gmail.com'  # replace with your email
app.config['MAIL_PASSWORD'] = 'knac grqm wuco smmk'  # replace with your password

mail = Mail(app)

# Function to check if the uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}

@app.route('/')
def home():
    filename = request.args.get('filename')
    
    # If a file has been uploaded, get the column names
    if filename:
        data = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        columns = data.columns.tolist()
    else:
        columns = []
    
    return render_template('index.html', filename=filename, columns=columns)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('home', filename=filename))

@app.route('/segment/<filename>', methods=['GET', 'POST'])
def segment(filename):
    if request.method == 'POST':
        # Get the selected features from the form
        selected_features = request.form.getlist('features')

        # Get the number of clusters from the form
        n_clusters = int(request.form.get('n_clusters'))

        # Load the data from the uploaded file
        data = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Prepare the features for clustering
        df1 = data[selected_features]

        # One-hot encode the categorical features
        encoder = OneHotEncoder()
        encoded_features = encoder.fit_transform(df1).toarray()
        X = pd.DataFrame(encoded_features)

        # Perform KMeans clustering
        km = KMeans(n_clusters=n_clusters)
        y = km.fit_predict(X)

        # Add the cluster labels to the original dataframe
        data["label"] = y

        # Get the directory of your script
        dir_path = os.path.dirname(os.path.realpath(__file__))

        # Save each cluster's data to a separate CSV file in the static directory
        for cluster_label in range(n_clusters):
            cluster_df = data[data['label'] == cluster_label]
            cluster_df.to_csv(os.path.join(dir_path, 'static', f'cluster_{cluster_label+1}.csv'), index=False)

        return render_template('index.html', segmented=True, n_clusters=n_clusters)
    else:
        return render_template('index.html', filename=filename)

@app.route('/download/<int:cluster_label>')
def download(cluster_label):
    # Get the directory of your script
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    return send_file(os.path.join(dir_path, 'static', f'cluster_{cluster_label+1}.csv'), as_attachment=True)

@app.route('/view/<int:cluster_label>')
def view(cluster_label):
    # Get the directory of your script
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    # Read the CSV file
    data = pd.read_csv(os.path.join(dir_path, 'static', f'cluster_{cluster_label+1}.csv'))
    
    # Convert the data to HTML
    data_html = data.to_html()

    # Return the HTML
    return data_html

@app.route('/send_email/<int:cluster_label>', methods=['GET', 'POST'])
def send_email(cluster_label):
    if request.method == 'POST':
        subject = request.form.get('subject')
        body = request.form.get('body')

        # Read the CSV file
        data = pd.read_csv(os.path.join('Code', 'static', f'cluster_{cluster_label+1}.csv'))
        
        # Get the email addresses of the customers in the cluster
        email_addresses = data['Email_id'].tolist()

        # Create the email message
        msg = Message(subject,
                      sender='artbypravalli9@gmail.com',  # replace with your email
                      recipients=email_addresses)
        msg.body = body

        # Send the email
        try:
            mail.send(msg)
            return 'Email sent!'
        except Exception as e:
            return f'Failed to send email: {str(e)}'
    else:
        return render_template('send_email.html')

if __name__ == '__main__':
    app.run(debug=True)