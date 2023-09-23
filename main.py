"""
Created By:    Cristian Scutaru
Creation Date: Sep 2023
Company:       XtractPro Software
"""

import configparser, os
import pandas as pd
import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session


# get and show all row properties in the "exploded" node
def getShapeProps(row, cols, label, displayCol):
    vals = ''
    for col in cols:
        if col != displayCol:
            val = '&nbsp;' if col not in row or row[col] is None else str(row[col])
            vals += (f'\t\t<tr><td align="left"><font color="#000000">{col}&nbsp;</font></td>\n'
                + f'\t\t<td align="left"><font color="#000000">{val}</font></td></tr>\n')

    return (f' [ label=<<table style="rounded" border="0" cellborder="0" cellspacing="0" cellpadding="1">\n'
        + f'\t\t<tr><td align="center" colspan="2"><font color="#000000"><b>{label}</b></font></td></tr>\n'
        + f'{vals}\t\t</table>> ]')

# add node (with label and eventual value)
def getShape(row, cols, fromCol, toCol, displayCol, all, v, t):
    fromToCol = fromCol if fromCol != '' else toCol
    label = str(row[fromToCol]) if displayCol == '' else str(row[displayCol])
    if all: display = getShapeProps(row, cols, label, displayCol)
    else: display = f' [label="{label}"{v}]'
    return f'\n\t{t}n{str(row[fromToCol])}{display};'

# returns a DOT graphviz chart
def makeGraph(df, cols, fromCol, toCol, displayCol, groupCol, valueCol, rev, all):
    s = ""; t = ""
    if fromCol == '': return s

    # calculate in, max, to scale values between 1..3 inches
    mi, ma = 1, 3; min, max = 0.0, 0.0
    if valueCol != '':
        for row in rows:
            val = float(row[valueCol])
            if val < min: min = val
            if val > max: max = val

    # add groups (as subgraph clusters)
    if groupCol != '':
        df.sort(key=lambda x: x[groupCol])
        t = "\t"

    # add nodes
    g = None; gps = 1;
    for row in rows:
        # read group and create subgroup cluster for next nodes
        if groupCol != '':
            grp = str(row[groupCol])
            if g is None or grp != g:
                if g is not None: s += '\n\t}'
                s += (f'\n\tsubgraph cluster{gps} {{\n'
                    + f'\t\tlabel="{grp}"')
                gps += 1; g = grp

        # resize bubble based on value
        v = ''
        if valueCol != '':
            valN = (ma - mi) * (float(row[valueCol]) - min) / (max - min) + 1 
            v = f' width={valN:0.2f} tooltip="{row[valueCol]}"'

        # add node (with label and eventual value)
        s += getShape(row, cols, fromCol, toCol, displayCol, all, v, t)
    if groupCol != '' and g is not None: s += '\n\t}'

    # add links
    if fromCol != '' and toCol != '':
        for row in rows:
            if not pd.isna(row[toCol]):
                if rev: s += f'\n\tn{str(row[toCol])} -> n{str(row[fromCol])};'
                else: s += f'\n\tn{str(row[fromCol])} -> n{str(row[toCol])};'

    # add digraph around
    shape = 'Mrecord' if valueCol == '' else 'circle'
    s = (f'digraph {{\n'
        + f'\tgraph [rankdir="LR"; compound="True" color="Gray"];\n'
        + f'\tnode [shape="{shape}" style="filled" color="SkyBlue"]'
        + f'{s}\n}}')
    return s

# allows Snowflake connection from the account or locally
def getSession():
    try:
        return get_active_session()
    except:
        parser = configparser.ConfigParser()
        parser.read(os.path.join(os.path.expanduser('~'), ".snowsql/config"))
        section = "connections.my_conn"
        pars = {
            "account": parser.get(section, "accountname"),
            "user": parser.get(section, "username"),
            "password": parser.get(section, "password")
        }
        return Session.builder.configs(pars).create()

# run the SQL query, when changed
@st.cache_resource(show_spinner="Executing the SQL query...")
def runQuery(query):
    res = getSession().sql(query)
    rows = res.collect()
    cols = res.columns.copy()
    cols.insert(0, "")
    cols = tuple(cols)
    return rows, cols

tabQuery, tabGraph, tabCode = st.tabs(["SQL Query", "Graph", "DOT Code"])

sql = "select * from streamlit_hierarchy_viewer.public.employees;"
query = tabQuery.text_area(label="Enter an SQL query to execute:", label_visibility="collapsed", value=sql)
if query not in st.session_state or st.session_state["query"] != query:
    if tabQuery.button("Run"):
        st.session_state["query"] = query

rows, cols = runQuery(query)
df = tabQuery.dataframe(rows, use_container_width=True)

fromCol = st.sidebar.selectbox('FROM Column', cols, help='The unique identifier of each row')
toCol = st.sidebar.selectbox('TO Column', cols, help='The foreign key column, that makes the hierarchy')
rev = st.sidebar.checkbox('Reverse Directions', help='Switch all relationship directions')
displayCol = st.sidebar.selectbox('Display Column', cols, help='Friendly row identifier value')
groupCol = st.sidebar.selectbox('Group Column', cols, help='If you want to group rows by a value')
valueCol = st.sidebar.selectbox('Value Column', cols, help='Show bubbles resized by this value')
all = st.sidebar.checkbox('Expand All', help='Tp show all row values as shape properties')

s = makeGraph(rows, cols, fromCol, toCol, displayCol, groupCol, valueCol, rev, all)
tabGraph.graphviz_chart(s, use_container_width=True)
tabCode.code(s, language="dot", line_numbers=True)
