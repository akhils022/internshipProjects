import dspy
from excel import write_to_db

class ExcelSignature(dspy.Signature):
    """
    You are an Excel agent tasked with reading data from Excel files and allowing users to download extracted data.
    Steps:
    1. Read the raw excel input from the user query.
    2. Extract these fields:
        - Organization, Website, Employee, Contact, Designation, Email, Mobile, Telephone, Address, City, State, Country, Industry, Other.
        - Extract city, state, country from Address (ex. Leela Tower, Kallai Road, Calicut -> City: Calicut, State: Kerala, Country: India)
    3. In the "Other Information" column, include any relevant info (but avoid details like PIN, Fax Number, etc.).
    4. Generate a JSON formatted string containing all data for the result file.
    5. Use the `write_to_db` tool to allow the user to download the contents.
    6. Return a simple message describing the status of the operation.
    """
    query: str = dspy.InputField(desc="The query from the user")
    response: str = dspy.OutputField(desc="A message describing whether the operation was successful or not.")

class ExcelAgent(dspy.Module):
    def __init__(self, tools):
        super().__init__()
        self.react = dspy.ReAct(ExcelSignature, tools=tools)

    def forward(self, query):
        # The ReAct module handles the reasoning and tool calling
        response = self.react(query=query)
        return dspy.Prediction(response=response.response)

# Instantiate the DSPy program
#dspy.configure(lm=dspy.LM("gemini/gemini-2.5-flash", api_key="AIzaSyCcI1YttvZn6_y75iai1_mOBOUs_AkwsCM",
#                         max_tokens=100000, temperature=0.2))
analytical_agent_dspy = ExcelAgent(tools=[write_to_db])

