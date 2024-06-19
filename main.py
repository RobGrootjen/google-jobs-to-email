import http.client
import json
import smtplib
from email.mime.text import MIMEText
from google.cloud import storage

def scrape_jobs():
    conn = http.client.HTTPSConnection("jobs-api14.p.rapidapi.com")

    headers = {
        'x-rapidapi-key': "RAPID_API_KEY",
        'x-rapidapi-host': "jobs-api14.p.rapidapi.com"
    }

    conn.request("GET", "/list?query=%22Google%20Cloud%22&location=Spain&language=en_GB&remoteOnly=false&datePosted=today&employmentTypes=fulltime%3Bparttime%3Bintern%3Bcontractor&index=0", headers=headers)

    res = conn.getresponse()
    data = res.read()

    jobs = data.decode("utf-8")
    return jobs

def save_to_gcs(jobs):
    storage_client = storage.Client()
    bucket = storage_client.bucket('BUCKET_NAME')  # Replace with your bucket name
    blob = bucket.blob('latest_jobs.json')
    blob.upload_from_string(jobs, 'application/json')

def send_email(jobs):
    sender = 'EMAIL'  # Replace with your email
    recipient = 'EMAIL'  # Replace with recipient email
    subject = 'Daily Google Cloud Jobs'

    jobs_json = json.loads(jobs)
    jobs_list = jobs_json.get("jobs", [])

    if not jobs_list:
        print("No jobs found in the response.")
        return

    html_content = """
    <html>
    <body>
        <h1>Daily Job Updates</h1>
        <ul>
    """

    for job in jobs_list:
        html_content += f"""
            <li>
                <strong>Title:</strong> {job.get('title')}<br>
                <strong>Company:</strong> {job.get('company')}<br>
                <strong>Location:</strong> {job.get('location')}<br>
                <strong>Date Posted:</strong> {job.get('datePosted')}<br>
                <strong>Employment Type:</strong> {job.get('employmentType')}<br>
                <strong>Job Links:</strong>
                <ul>
        """
        job_providers = job.get('jobProviders', [])
        for provider in job_providers:
            html_content += f"<li><a href='{provider.get('url')}'>{provider.get('jobProvider')}</a></li>"
        
        html_content += """
                </ul>
                <br>
            </li>
            <hr>
        """

    html_content += """
        </ul>
    </body>
    </html>
    """

    msg = MIMEText(html_content, 'html')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    app_password = 'APP_PASSWORD'  # Replace with your app password

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender, app_password)
            server.sendmail(sender, recipient, msg.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main(request):
    jobs = scrape_jobs()
    print(f"Scraped jobs data: {jobs[:500]}")  # Print first 500 characters for debugging
    save_to_gcs(jobs)
    send_email(jobs)
    return 'Jobs scraped, saved to GCS, and email sent'
