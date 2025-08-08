from flask import Flask, render_template, request, send_file, redirect, url_for
import os
import re
import json
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin
from report_generator import create_pdf_report
from concurrent.futures import ThreadPoolExecutor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# Config
COMPANY_NAME = "XSSScanX" # <-- Update with your company name
PAYLOADS_FILE = "payloads/custom_payload.txt"
PDF_REPORT_FOLDER = "reports"
THREADS = 10

def read_payloads(file_path):
    """Reads payloads from a text file, one per line."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    return []

def inject_get_params(url, payload):
    """Injects a payload into GET parameters of a URL."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if not params:
        params = {"q": payload}
    else:
        for p in params:
            params[p] = payload
    new_query = urlencode(params, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

def extract_forms(url):
    """Extracts all forms from a given URL."""
    try:
        r = requests.get(url, verify=False, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        return soup.find_all("form")
    except:
        return []

def submit_form(form, base_url, payload):
    """Submits a form with a payload and returns the response."""
    action = form.get("action")
    method = form.get("method", "get").lower()
    form_url = urljoin(base_url, action)
    inputs = form.find_all(["input", "textarea", "select"])
    data = {}
    for inp in inputs:
        name = inp.get("name")
        if name:
            data[name] = payload
    if method == "post":
        return requests.post(form_url, data=data, verify=False, timeout=10)
    else:
        return requests.get(form_url, params=data, verify=False, timeout=10)

def detect_reflection(html, payload):
    """Detects if a payload is reflected in the HTML response."""
    if payload in html:
        return True
    if re.search(r'".*{}.*"'.format(re.escape(payload)), html):
        return True
    if re.search(r'<script[^>]*>.*{}.*</script>'.format(re.escape(payload)), html, re.IGNORECASE | re.DOTALL):
        return True
    return False

def test_get(url, payload):
    """Tests for XSS in GET parameters."""
    results = []
    test_url = inject_get_params(url, payload)
    try:
        r = requests.get(test_url, timeout=10, verify=False)
        vulnerable = detect_reflection(r.text, payload)
        results.append({
            "type": "GET",
            "payload": payload,
            "url_tested": test_url,
            "vulnerable": vulnerable,
            "status_code": r.status_code,
            "response_text": r.text[:300]
        })
    except requests.RequestException as e:
        results.append({
            "type": "GET",
            "payload": payload,
            "url_tested": test_url,
            "vulnerable": False,
            "status_code": "Error",
            "error": str(e)
        })
    return results

def test_forms(url, payload):
    """Tests for XSS in form inputs."""
    results = []
    forms = extract_forms(url)
    for i, form in enumerate(forms):
        try:
            r = submit_form(form, url, payload)
            vulnerable = detect_reflection(r.text, payload)
            results.append({
                "type": f"FORM #{i+1}",
                "payload": payload,
                "url_tested": r.url,
                "vulnerable": vulnerable,
                "status_code": r.status_code,
                "response_text": r.text[:300]
            })
        except requests.RequestException as e:
            results.append({
                "type": f"FORM #{i+1}",
                "payload": payload,
                "url_tested": url,
                "vulnerable": False,
                "status_code": "Error",
                "error": str(e)
            })
    return results

def test_headers(url, payload):
    """Tests for XSS in HTTP headers."""
    results = []
    headers_list = {
        "User-Agent": payload,
        "Referer": payload,
        "X-Forwarded-For": payload
    }
    try:
        r = requests.get(url, headers=headers_list, verify=False, timeout=10)
        vulnerable = detect_reflection(r.text, payload)
        results.append({
            "type": "HEADERS",
            "payload": payload,
            "url_tested": url,
            "vulnerable": vulnerable,
            "status_code": r.status_code,
            "response_text": r.text[:300]
        })
    except requests.RequestException as e:
        results.append({
            "type": "HEADERS",
            "payload": payload,
            "url_tested": url,
            "vulnerable": False,
            "status_code": "Error",
            "error": str(e)
        })
    return results

def test_cookies(url, payload):
    """Tests for XSS in cookies."""
    results = []
    try:
        cookies = {"sessionid": payload}
        r = requests.get(url, cookies=cookies, verify=False, timeout=10)
        vulnerable = detect_reflection(r.text, payload)
        results.append({
            "type": "COOKIES",
            "payload": payload,
            "url_tested": url,
            "vulnerable": vulnerable,
            "status_code": r.status_code,
            "response_text": r.text[:300]
        })
    except requests.RequestException as e:
        results.append({
            "type": "COOKIES",
            "payload": payload,
            "url_tested": url,
            "vulnerable": False,
            "status_code": "Error",
            "error": str(e)
        })
    return results

def test_payloads_on_url(url, payloads):
    """Runs all tests concurrently using a ThreadPoolExecutor."""
    results = []
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = []
        for payload in payloads:
            futures.append(executor.submit(test_get, url, payload))
            futures.append(executor.submit(test_forms, url, payload))
            futures.append(executor.submit(test_headers, url, payload))
            futures.append(executor.submit(test_cookies, url, payload))
        for future in futures:
            results.extend(future.result())
    return results

@app.route('/')
def index():
    """Renders the main index page."""
    return render_template('index.html', company_name=COMPANY_NAME)

@app.route('/test_url', methods=['POST'])
def test_url():
    """Handles the form submission and runs the scan."""
    target_url = request.form.get('target_url')
    if not target_url:
        return redirect(url_for('index'))

    payloads = read_payloads(PAYLOADS_FILE)
    if not payloads:
        return "No payloads found in the file. Please add some payloads.", 404

    test_results = test_payloads_on_url(target_url, payloads)

    return render_template('report.html',
                           results=test_results,
                           company_name=COMPANY_NAME,
                           target_url=target_url)

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    """Generates and downloads a PDF report."""
    results_json = request.form.get('results_json')
    target_url = request.form.get('target_url')
    if not results_json or not target_url:
        return "No results to generate a report.", 400

    test_results = json.loads(results_json)

    if not os.path.exists(PDF_REPORT_FOLDER):
        os.makedirs(PDF_REPORT_FOLDER)

    pdf_path = create_pdf_report(test_results, COMPANY_NAME, folder=PDF_REPORT_FOLDER, target_url=target_url) 

    return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
