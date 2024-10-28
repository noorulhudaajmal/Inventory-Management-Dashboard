# Inventory Insights Dashboard

## Getting Started
To run the dashboard on your local machine, follow the steps below:
### Prerequisites

- Python (version 3.6 or higher)

### Installation
1. Extract the zipped filed and open terminal at the project directory.
2. Create a virtual environment to manage dependencies:
```shell
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```
3. Install the required dependencies by running the following command:
```shell
pip install -r requirements.txt
```
4. Get your googlesheet config from GCP and insert in `./streamlit/secrets.toml`


### Usage

To start the Inventory Insights Dashboard, run the following command in your terminal:
```shell
streamlit run app.py
```

This will launch the dashboard application in your web browser. You can now interact with and explore the inventory data.

---