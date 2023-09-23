-- Created By:    Cristian Scutaru
-- Creation Date: Sep 2023
-- Company:       XtractPro Software

CREATE OR REPLACE DATABASE streamlit_hierarchy_viewer;

CREATE STAGE stage
    directory = (enable=true)
    file_format = (type=CSV field_delimiter=None record_delimiter=None);

CREATE TABLE IF NOT EXISTS employees
    (EMPLOYEE_ID INT, EMPLOYEE_NAME VARCHAR, PHONE_NUMBER VARCHAR,
    HIRE_DATE DATE, JOB VARCHAR, SALARY INT,
    MANAGER_ID INT, DEPARTMENT VARCHAR);

PUT file://C:\Projects\streamlit-apps\streamlit-hierarchy-viewer\data\employees.csv @stage/data
    overwrite=true auto_compress=false;
COPY INTO employees FROM @stage/data
    FILE_FORMAT = (TYPE=CSV SKIP_HEADER=1 FIELD_OPTIONALLY_ENCLOSED_BY='"'
        NULL_IF='' EMPTY_FIELD_AS_NULL=true);

PUT file://C:\Projects\streamlit-apps\streamlit-hierarchy-viewer\main.py @stage
    overwrite=true auto_compress=false;

CREATE STREAMLIT streamlit_hierarchy_viewer
    ROOT_LOCATION = '@streamlit_hierarchy_viewer.public.stage'
    MAIN_FILE = '/main.py'
    QUERY_WAREHOUSE = "COMPUTE_WH";
SHOW STREAMLITS;
