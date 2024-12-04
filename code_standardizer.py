import sys
import os
import subprocess
import streamlit as st
import google.generativeai as genai

# Configure the API key
my_secret = os.environ['GOOGLE_API_KEY']
genai.configure(api_key=my_secret)


# Function to ensure Pylint is installed
def ensure_pylint_installed():
    try:
        subprocess.run(['pylint', '--version'], check=True)
    except FileNotFoundError:
        st.write("Pylint is not installed. Installing it now...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pylint"])


# Function to ensure Black is installed
def ensure_black_installed():
    try:
        subprocess.run(['black', '--version'], check=True)
    except FileNotFoundError:
        st.write("Black is not installed. Installing it now...")
        subprocess.run([sys.executable, "-m", "pip", "install", "black"])


# Function to ensure lintr is installed for R
def ensure_lintr_installed():
    rscript_path = "Rscript"  # Replace with the actual path to Rscript
    try:
        subprocess.run([rscript_path, '-e', 'library(lintr)'], check=True)
    except subprocess.CalledProcessError:
        st.write("lintr is not installed in R. Installing it now...")
        subprocess.run([rscript_path, '-e', 'install.packages("lintr")'])


# Function to analyze code using Pylint
def analyze_code_pylint(file_path):
    ensure_pylint_installed()
    result = subprocess.run(['pylint', file_path],
                            capture_output=True,
                            text=True)
    return result.stdout


# Function to extract Pylint score from the report
def extract_pylint_score(lint_report):
    for line in lint_report.splitlines():
        if "Your code has been rated at" in line:
            return line.strip()
    return "Pylint score not found."


# Function to format code using Black
def format_code_black(file_path):
    ensure_black_installed()
    subprocess.run(['black', file_path])
    with open(file_path, 'r') as file:
        formatted_code = file.read()
    return formatted_code


# Function to analyze code using lintr for R
def analyze_code_lintr(file_path):
    ensure_lintr_installed()
    rscript_path = "Rscript"  # Replace with the actual path to Rscript
    result = subprocess.run(
        [rscript_path, '-e', f'lintr::lint("{file_path}")'],
        capture_output=True,
        text=True)
    return result.stdout


# Function to call the Gemini LLM
def call_gemini_llm(prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')  # Use this model
        response = model.generate_content(prompt)
        response.resolve()
        return response.text
    except Exception as e:
        st.error(f"Error calling Gemini LLM: {e}")
        return ""


# Function to standardize code based on Pylint report
def standardize_code_pylint(code, lint_report):
    prompt = f"""
    Given the following Python code and the Pylint report, improve the code to address all issues and achieve a Pylint score greater than 8.
    Include only the necessary docstrings and avoid redundant explanations.

    Original Code:
    {code}

    Pylint Report:
    {lint_report}

    Improved Code:
    """
    standardized_code = call_gemini_llm(prompt)
    return standardized_code.replace('```python', ' ').replace('```', ' ')


# Function to standardize code using Black
def standardize_code_black(code):
    prompt = f"""
    Given the following Python code, format it according to the Black code style.

    Original Code:
    {code}

    Improved Code:
    """
    standardized_code = call_gemini_llm(prompt)
    return standardized_code.replace('```python', ' ').replace('```', ' ')


# Function to standardize code using lintr for R
def standardize_code_lintr(code, lint_report):
    prompt = f"""
    Given the following R code and the lintr report, improve the code to address all issues according to R's best practices.
    Include only the necessary comments and avoid redundant explanations.

    Original Code:
    {code}

  

    Improved Code:
    """
    standardized_code = call_gemini_llm(prompt)
    return standardized_code.replace('```r', ' ').replace('```', ' ')


# Function to summarize code
def summarize_code(code, language="Python"):
    prompt = f"""
    Summarize the following {language} code. Provide a concise explanation of what the code does.

    Code:
    {code}

    Summary:
    """
    summary = call_gemini_llm(prompt)
    return summary


# Function to translate Python to R
def translate_python_to_r(python_code):
    prompt = f"""
    Translate the following Python code into R code.

    Python Code:
    {python_code}

    R Code:
    """
    r_code = call_gemini_llm(prompt)
    return r_code


# Function to translate R to Python
def translate_r_to_python(r_code):
    prompt = f"""
    Translate the following R code into Python code.

    R Code:
    {r_code}

    Python Code:
    """
    python_code = call_gemini_llm(prompt)
    return python_code


# Streamlit app
def main():
    st.title("Code Standardizer and Translator")

    action_choice = st.radio("Choose an action:", ('Standardize', 'Translate'))
    language_choice = st.radio("Choose a language:", ('Python', 'R'))

    if action_choice == 'Translate':
        if language_choice == 'Python':
            translation_code = st.text_area("Paste Python code here:",
                                            height=200)
            if st.button("Translate to R"):
                translated_code = translate_python_to_r(translation_code)
                st.subheader("Translated R Code")
                st.text_area("R Code", translated_code, height=200)

        elif language_choice == 'R':
            translation_code = st.text_area("Paste R code here:", height=200)
            if st.button("Translate to Python"):
                translated_code = translate_r_to_python(translation_code)
                st.subheader("Translated Python Code")
                st.text_area("Python Code", translated_code, height=200)

    elif action_choice == 'Standardize':
        standardizer_choice = st.radio("Choose a standardizer:",
                                       ('Pylint', 'Black', 'lintr'))

        uploaded_file = st.file_uploader("Upload a file", type=["py", "r"])
        if uploaded_file is not None:
            file_path = uploaded_file.name
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            # Read the original code
            with open(file_path, 'r') as file:
                original_code = file.read()

            # Summarize the original code
            summary = summarize_code(original_code, language=language_choice)
            st.subheader("Code Summary")
            st.text_area("Summary Output", summary, height=150)

            standardized_code = ""
            standardized_file_path = f'standardized_{file_path}'

            if language_choice == 'Python':
                if standardizer_choice == 'Pylint':
                    lint_report = analyze_code_pylint(file_path)
                    st.subheader("Pylint Report")
                    st.text(lint_report)

                    standardized_code = standardize_code_pylint(
                        original_code, lint_report)

                    # Save the standardized code
                    with open(standardized_file_path, 'w') as file:
                        file.write(standardized_code)

                    # Display the standardized code
                    st.subheader("Standardized Code (Pylint)")
                    st.text_area("Standardized Code",
                                 standardized_code,
                                 height=200)

                    # Analyze the new code with Pylint and display the new score
                    new_lint_report = analyze_code_pylint(
                        standardized_file_path)
                    st.subheader("New Pylint Report")
                    st.text(new_lint_report)

                    # Extract and display the new Pylint score
                    new_pylint_score = extract_pylint_score(new_lint_report)
                    st.subheader("New Pylint Score")
                    st.text(new_pylint_score)

                elif standardizer_choice == 'Black':
                    standardized_code = format_code_black(file_path)

                    # Save the standardized code
                    with open(standardized_file_path, 'w') as file:
                        file.write(standardized_code)

                    # Display the standardized code
                    st.subheader("Standardized Code (Black)")
                    st.text_area("Standardized Code",
                                 standardized_code,
                                 height=200)

            elif language_choice == 'R':
                if standardizer_choice == 'lintr':
                    lint_report = analyze_code_lintr(file_path)
                    st.subheader("lintr Report")
                    st.text(lint_report)

                    standardized_code = standardize_code_lintr(
                        original_code, lint_report)

                    # Save the standardized code
                    with open(standardized_file_path, 'w') as file:
                        file.write(standardized_code)

                    # Display the standardized code
                    st.subheader("Standardized Code (lintr)")
                    st.text_area("Standardized Code",
                                 standardized_code,
                                 height=200)

            # Provide download button for the standardized code
            with open(standardized_file_path, 'r') as file:
                st.download_button(label="Download Standardized Code",
                                   data=file,
                                   file_name=standardized_file_path,
                                   mime="text/plain")


if __name__ == "__main__":
    main()
