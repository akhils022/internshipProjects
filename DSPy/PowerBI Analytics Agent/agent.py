import dspy
from typing import Callable, Sequence

# Define DSPy Signature and Program
class AnalyticalSignature(dspy.Signature):
    """
    You are a PowerBI Analytics agent assisting with interpreting trends and insights
    in a user database. You should use the `powerbi_metadata` tool to understand the
    data source, and the `dax_query` tool to execute a query. Return both a textual
    analysis with insights and/or recommendations, and Highcharts formatted JSON visuals.
    """
    query: str = dspy.InputField(desc="The user's analytics question")
    text_result: str = dspy.OutputField(desc="Summary of findings and suggestions")
    charts: str = dspy.OutputField(desc="HighCharts-compatible chart JSON if needed")

class AnalyticalAgent(dspy.Module):
    def __init__(self, tools):
        super().__init__()
        self.react = dspy.ReAct(AnalyticalSignature, tools=tools)

    def forward(self, query):
        response = self.react(query=query)
        return dspy.Prediction(
            text_result=response.text_result,
            charts=response.charts
        )

class DSPyAgentApp:
    def __init__(
            self,
            name: str,
            tools: Sequence[Callable],
            project: str,
            location: str,
    ):
        self.name = name
        self.tools = tools
        self.project = project
        self.location = location

    def set_up(self):
        import vertexai
        vertexai.init(project=self.project, location=self.location)
        dspy.settings.configure(lm=dspy.LM("vertexai/gemini-2.5-flash"))
        self.agent = AnalyticalAgent(tools=self.tools)

    def query(self, query: str):
        # We call the forward method of our DSPy agent here.
        if not self.agent:
            print("Error: Agent not set up. Please call `set_up()` first.")
            return {"text": "Agent not initialized.", "charts": "[]"}

        result = self.agent.forward(query=query)
        return {
            "text": result.text_result,
            "charts": result.charts
        }