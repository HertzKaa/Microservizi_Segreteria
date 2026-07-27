***

## 🚀 Getting Started

To run this project, you will need to set up both the **Backend** and the **Frontend** environments.

### 1. Prerequisites
*   [Python 3.x](https://www.python.org/) installed.
*   [Node.js/npm](https://nodejs.org/) installed (for the frontend).

---

### 2. Backend Setup
Open a terminal in the root folder and run the following commands:

```bash
# Create virtual environment using Python Launcher (Windows)
py -m venv venv

# If you get an 'ensurepip' error on Windows, use this alternative:
# py -m venv --without-pip venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1  # On macOS/Linux use: source venv/bin/activate

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Run the backend
cd backend
python app.py
```

---

### 3. Frontend Setup
Open a **new terminal** window, navigate to the frontend folder, and run:

```bash
cd frontend
py -m http.server 8000  

# Go to the page
http://localhost:8000/admission_verification_form.html
http://localhost:8000/student_ontology_form.html
```