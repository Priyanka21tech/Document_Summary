# Document_Summary
This is a simple Document summarizer flask application that takes the follwing input-
  1. URL
  2. PDF
  3. TEXT 
and determines the summary of the content. In case the PDF is protected it asks the suer for the password before proceeding to the summarization. The summarization contains the extracted text and the summarized text.

# Project Structure
>Doc_summary
  >static
    >s.css
  >templates
    >index.html
    >password.html
  >app2.py

# Project running
python app2.py

# Note: The .env file contains the credentials of OPENAI_API
