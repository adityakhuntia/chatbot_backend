from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.agents import initialize_agent, AgentType
from langchain_cohere import ChatCohere
from langchain.tools import Tool
from langchain_experimental.sql import SQLDatabaseChain
from langchain_community.utilities import SQLDatabase
from urllib.parse import quote
import os

app = FastAPI()

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://nizvcdssajfpjtncbojx.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5penZjZHNzYWpmcGp0bmNib2p4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI2MTU0ODksImV4cCI6MjA1ODE5MTQ4OX0.5b2Yzfzzzz-C8S6iqhG3SinKszlgjdd4NUxogWIxCLc")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "8ueWFEgswEV04DUHCsnpIiFqYDeD35e4BPs8sepl")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD", "SupaBase@Ishanya@Team_2")

# Initialize database connection
DB_HOST = SUPABASE_URL.replace("https://", "db.")  # Adjusting the host format
db = SQLDatabase.from_uri(
    f"postgresql://postgres:{quote(SUPABASE_PASSWORD, safe='')}@{DB_HOST}:5432/postgres"
)

db_chain = SQLDatabaseChain.from_llm(
    llm=ChatCohere(cohere_api_key=COHERE_API_KEY),
    db=db,
    return_direct=True,
    verbose=True
)

def query_database(query: str):
    """Function to interact with Supabase using SQL queries."""
    print(f"Executing Query: {query}")
    result = db.run(query)
    print(f"Query Result: {result}")
    return result

tool = Tool(
    name="DatabaseQuery",
    func=query_database,
    description="Use this tool to query the Supabase database with SQL commands"
)

# Initialize LangChain agent
llm = ChatCohere(cohere_api_key=COHERE_API_KEY, temperature=0)
agent = initialize_agent(
    tools=[tool],
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True
)

class QueryRequest(BaseModel):
    user_query: str

@app.post("/chatbot")
async def chatbot(request: QueryRequest):
    try:
        user_query = request.user_query + (
            "The following is the schema of the Students table: "
            "STUDENT_id: Unique identifier for the student. "
            "first_name: First name of the student. "
            "last_name: Last name of the student. "
            "photo: Profile picture or avatar of the student. "
            "gender: Gender of the student. "
            "dob: Date of birth of the student. "
            "primary_diagnosis: Primary medical or educational diagnosis. "
            "comorbidity: Any additional medical conditions. "
            "udid: Unique Disability ID (if applicable). "
            "enrollment_year: Year the student was enrolled. "
            "status: Current enrollment status (active, graduated, etc.). "
            "student_email: Email address of the student. "
            "program_id: Primary program the student is enrolled in. --> Foreign Key to Programme Table" 
            "program_2_id: Secondary program (if any). --> Foreign Key to Programme Table"
            "number_of_sessions: Total sessions attended or scheduled. "
            "timings: Preferred or scheduled session timings. "
            "days_of_week: Days of the week the student attends sessions. "
            "educator_id: Primary educator assigned to the student. "
            "secondary_educator_id: Secondary educator (if any). "
            "session_type: Type of session (e.g., individual, group, online). "
            "blood_group: Student's blood group. "
            "allergies: Known allergies, if any. "
            "contact_number: Primary contact number. "
            "alt_contact_number: Alternate contact number. "
            "address: Residential address of the student. "
            "transport: Transportation details or requirements. "
            "strengths: Notable strengths of the student. "
            "weakness: Areas where the student may need additional support. "
            "comments: Additional notes or remarks. "
            "created_at: Timestamp when the record was created. "
            "center_id: Identifier for the center the student is associated with."
            "The following is the schema of the programs table: "
            "id: Unique identifier for the programme, "
            "name: Name of the programme, "
            "num_of_student: Number of students enrolled in the programme, "
            "num_of_educator: Number of educators assigned to the programme, "
            "center_id: Identifier for the center associated with the programme, "
            "created_at: Timestamp when the programme record was created."
        )
        response = agent.invoke(user_query)
        output = response.get('output', "No response")
    except Exception as e:
        output = f"Error processing request: {str(e)}"
    return {"response": output}

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Default to 8000 if PORT is not set
    uvicorn.run(app, host="0.0.0.0", port=port)
