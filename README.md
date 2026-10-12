# EduPro Online Platform Analytics Dashboard

An interactive Streamlit dashboard that analyses course ratings, teacher performance and enrolments on the EduPro online learning platform.

**Live app:** `ADD YOUR .streamlit.app LINK HERE`

---

## Overview

EduPro is an online learning platform with courses, teachers and learners. This project turns the platform's data into an easy-to-use dashboard so that managers and course teams can see which course categories and teachers perform best, what drives ratings and enrolments, and where improvement is needed.

## Dataset

- **File:** `EduPro Online Platform.xlsx`
- Contains course, teacher and enrolment information for the platform, including fields such as course category, course rating, teacher expertise and enrolments.

## Features

- **Interactive filters** to narrow the data to the categories and teachers you want to explore
- **Course rating analysis** showing the best- and worst-rated course categories
- **Teacher analysis** covering expertise and consistency of ratings
- **Correlation insights** that describe how strongly factors such as expertise and teacher consistency relate to ratings
- **Enrolment analysis** comparing performance across teacher groups
- **Data tables** that you can scroll and explore in the app
- **CSV download** of the teacher-level summary table

## Tech Stack

- Python
- Streamlit
- pandas
- openpyxl (to read the Excel file)

## Project Structure

```
.
├── .streamlit/
│   └── config.toml                 # Streamlit theme and settings
├── app.py                          # Main dashboard application
├── EduPro Online Platform.xlsx     # Dataset
├── requirements.txt                # Python dependencies
└── README.md                       # Project overview
```

## How to Run Locally

1. Clone the repository:
   ```
   git clone https://github.com/lockish/edupro.git
   cd edupro
   ```
2. (Optional) Create and activate a virtual environment.
3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Start the app:
   ```
   streamlit run app.py
   ```
5. Open the address shown in the terminal, usually `http://localhost:8501`.

## How to Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **Create app**, choose this repository and the `main` branch, and set the main file path to `app.py`.
4. Click **Deploy**. Streamlit installs the packages in `requirements.txt` and gives you a public link.

## Author

**Lokesh**
GitHub: [@lockish](https://github.com/lockish)
