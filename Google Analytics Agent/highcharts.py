# Program that tests functionality of highcharts with JSON input
import streamlit as st
import json

# Test JSON for Highcharts
highcharts_json = {
        "title": {
          "text": "Sales Trends in the United States by Category"
        },
        "xAxis": {
          "title": {
              "text": "Year"
          }
        },
        "yAxis": {
          "title": {
              "text": "Total Sales"
          }
        },
        "series": [
          {
              "name": "Furniture",
              "data": [
                157188,
                170518,
                198910,
                215390
              ]
          },
          {
              "name": "Office Supplies",
              "data": [
                151782,
                137248,
                183531,
                246566
              ]
          },
          {
              "name": "Technology",
              "data": [
                175285,
                162794,
                226082,
                272060
              ]
          }
        ],
        "xAxis": {
          "categories": [
              "2011",
              "2012",
              "2013",
              "2014"
          ]
        }
    }

# Convert the Highcharts JSON structure to a JSON string
highcharts_json_str = json.dumps(highcharts_json)

# Streamlit App to embed the Highcharts chart
st.title("Highcharts Integration with Streamlit")

# HTML and JavaScript for Highcharts
highcharts_html = f"""
    <div id="container" style="width:100%; height:400px;"></div>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script type="text/javascript">
        var chartData = {highcharts_json_str};  // Embed the chart data here
        Highcharts.chart('container', chartData);
    </script>
"""

hh = """
      <div id="container" style="width:100%; height:400px;"></div>
      <script src="https://code.highcharts.com/highcharts.js"></script>
      <script type="text/javascript">
          var chartData = "\n      <div id=\"container\" style=\"width:100%; height:400px;\"></div>\n      <script src=\"https://code.highcharts.com/highcharts.js\"></script>\n      <script type=\"text/javascript\">\n          var chartData = {\"title\": {\"text\": \"US Sales Trends by Category (2011-2014)\"}, \"xAxis\": {\"title\": {\"text\": \"Year\"}, \"categories\": [\"2011\", \"2012\", \"2013\", \"2014\"]}, \"yAxis\": {\"title\": {\"text\": \"Total Sales\"}}, \"series\": [{\"name\": \"Furniture\", \"data\": [157188, 170518, 198910, 215390]}, {\"name\": \"Office Supplies\", \"data\": [151782, 137248, 183531, 246566]}, {\"name\": \"Technology\", \"data\": [175285, 162794, 226082, 272060]}]};\n          Highcharts.chart('container', chartData);\n      </script>\n  ";
          Highcharts.chart('container', chartData);
      </script>
"""

# Embed the HTML with the Highcharts chart
st.components.v1.html(highcharts_html, height=500)
st.components.v1.html(hh, height=500)