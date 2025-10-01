import os 
from pathlib import Path 
import logging 

logging.basicConfig(level=logging.INFO) 

project_name = 'regression-project'

list_of_files = [
    f"src/{project_name}/__init__.py",
    f"src/{project_name}/config.py",  # paths, global params, random_state 
    f"src/{project_name}/data/ingestion.py", # load csv(s)
    f"src/{project_name}/data/cleaning.py", 
    f"src/{project_name}/data/preprocessing.py", # ColumnTransformer, FunctionTransformer capper
    f"src/{project_name}/features/feature_engineering.py", # custom features, interactions
    f"src/{project_name}/models/train.py", # training orchestration (loop+GridSearchCV)
    f"src/{project_name}/models/evaluate.py", # metrics, corss-validation helpers
    f"src/{project_name}/models/persistence.py", # save/load model + preporcessors(joblib)
    f"src/{project_name}/viz/plotting.py", # functions for residuals, actual vs pred, comparison bars 
    f"src/{project_name}/viz/eda_reports.py", # wrapper for ydata-profiling or custom EDA 
    f"src/{project_name}/api/server.py", # FastAPI/FLask endpoints (predict, train, status)
    f"src/{project_name}/utils/logger.py",
    f"src/{project_name}/utils/helpers.py",
    f"interface/streamlit_app.py", # or react_app 
    f"interface/static", # demo gifs/screenshots used in README 
    "models/",
    "reports/",
    "environment.yml",
    "requirements.txt",
    "app.py",
    'setup.py',
    "Dockerfile",
    ".github/workflows/ci.yml",  # basic CI: lint, texts, build 
    'README.md',
    '.gitignore'
]

for filepath in list_of_files:
    filepath = Path(filepath)
    filedir, filename = os.path.split(filepath)

    if filedir != "":
        os.makedirs(filedir,exist_ok=True)
        logging.info(f"Creating directory: {filedir} for the file {filename}")

    if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0):
        with open(filepath, 'w') as f:
            logging.info(f"Creating empty file: {filepath}")

    else: 
        logging.info(f"{filename} already exists")