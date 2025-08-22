import json
import pandas as pd

# Split a chatbot response into text and graphs
def split_response(response):
    start_index = response.find('```json\n')
    if start_index != -1:
        start_index += len('```json\n')
        # Extract text and json data
        text = response[:response.find('```json\n')].strip()
        json_data = response[start_index:].split('```')[0].strip()
        try:
            # Load the JSON data
            data = json.loads(json_data)
            graphs = []
            for graph in data["charts"]:
                # Create graph based on the data
                graphs.append((create_graph(data["charts"][graph]), extract_table_from_graph(data["charts"][graph])))
            return text, graphs
        except json.JSONDecodeError:
            return text, None
    else:
        # If no graphs, return text only
        return response, None

# Uses HighCharts API to create a HTML graph
def create_graph(graph):
    return f"""
    <div style="width:100%; height:auto;">
        <div id="container" style="width:100%; min-height: 500px;"></div>
    </div>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script type="text/javascript">
        var chartData = {json.dumps(graph)};
        var chart = Highcharts.chart('container', chartData);
    </script>
    """

def format_number(num):
    if pd.isna(num):
        return "-"
    abs_num = abs(num)
    if abs_num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif abs_num >= 1_000:
        return f"{num / 1_000:.0f}K"
    else:
        return f"{num:.0f}"

def extract_table_from_graph(graph):
    categories = graph.get("xAxis", {}).get("categories", [])
    data_dict = {}
    for series in graph.get("series", []):
        data_dict[series["name"]] = series.get("data", [])
    df = pd.DataFrame(data_dict, index=categories).map(format_number)
    df.index.name = graph.get("xAxis", {}).get("title", {}).get("text", "Category")

    return df

