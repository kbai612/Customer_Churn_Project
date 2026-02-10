-- ============================================================================
-- Snowflake Setup Script for Retail Customer Churn Project
-- ============================================================================
-- This script creates the necessary databases, schemas, warehouses, stages,
-- file formats, and tables for the churn prediction project.
-- ============================================================================

-- ============================================================================
-- SECTION 1: DATABASE AND SCHEMA SETUP
-- ============================================================================

-- Create raw database for landing zone
CREATE DATABASE IF NOT EXISTS CHURN_RAW;

-- Create analytics database for transformed data
CREATE DATABASE IF NOT EXISTS CHURN_ANALYTICS;

-- Create raw schema
CREATE SCHEMA IF NOT EXISTS CHURN_RAW.RAW;

-- Create analytics schema
CREATE SCHEMA IF NOT EXISTS CHURN_ANALYTICS.ANALYTICS;

-- ============================================================================
-- SECTION 2: WAREHOUSE SETUP
-- ============================================================================

-- Create compute warehouse for analytics workloads
CREATE WAREHOUSE IF NOT EXISTS ANALYTICS_WH
  WITH WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Warehouse for dbt transformations and analytics queries';

-- Set the warehouse as default for this session
USE WAREHOUSE ANALYTICS_WH;

-- ============================================================================
-- SECTION 3: FILE FORMAT AND STAGE SETUP
-- ============================================================================

-- Create CSV file format with headers
CREATE OR REPLACE FILE FORMAT CHURN_RAW.RAW.CSV_FORMAT
  TYPE = 'CSV'
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  SKIP_HEADER = 1
  FIELD_DELIMITER = ','
  TRIM_SPACE = TRUE
  ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
  ESCAPE = 'NONE'
  ESCAPE_UNENCLOSED_FIELD = '\134'
  DATE_FORMAT = 'AUTO'
  TIMESTAMP_FORMAT = 'AUTO'
  NULL_IF = ('NULL', 'null', '')
  COMMENT = 'CSV format with header row for churn data';

-- Create internal stage for file uploads
CREATE OR REPLACE STAGE CHURN_RAW.RAW.CHURN_STAGE
  FILE_FORMAT = CHURN_RAW.RAW.CSV_FORMAT
  COMMENT = 'Internal stage for uploading customer churn CSV files';

-- ============================================================================
-- SECTION 4: RAW TABLES SETUP
-- ============================================================================

USE DATABASE CHURN_RAW;
USE SCHEMA RAW;

-- Raw customers table
CREATE OR REPLACE TABLE CHURN_RAW.RAW.CUSTOMERS (
  customer_id VARCHAR(50),
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  email VARCHAR(255),
  age INTEGER,
  gender VARCHAR(20),
  signup_date DATE,
  city VARCHAR(100),
  state VARCHAR(10),
  segment VARCHAR(50),
  acquisition_channel VARCHAR(50),
  device_type VARCHAR(50),
  timezone VARCHAR(50),
  preferred_language VARCHAR(50),
  customer_lifetime_days INTEGER,
  initial_referral_credits INTEGER
);

-- Raw transactions table
CREATE OR REPLACE TABLE CHURN_RAW.RAW.TRANSACTIONS (
  transaction_id VARCHAR(50),
  customer_id VARCHAR(50),
  transaction_date DATE,
  product_category VARCHAR(50),
  quantity INTEGER,
  unit_price DECIMAL(10, 2),
  total_amount DECIMAL(10, 2),
  payment_method VARCHAR(50)
);

-- Raw subscriptions table
CREATE OR REPLACE TABLE CHURN_RAW.RAW.SUBSCRIPTIONS (
  customer_id VARCHAR(50),
  plan_type VARCHAR(50),
  monthly_charges DECIMAL(10, 2),
  contract_type VARCHAR(50),
  last_payment_date DATE,
  is_active INTEGER
);

-- Raw behavioral events table
CREATE OR REPLACE TABLE CHURN_RAW.RAW.BEHAVIORAL_EVENTS (
  event_id VARCHAR(50),
  customer_id VARCHAR(50),
  event_date DATE,
  event_type VARCHAR(50),
  device_type VARCHAR(50),
  session_duration_minutes DECIMAL(10, 2),
  pages_viewed INTEGER
);

-- ============================================================================
-- SECTION 5: DATA LOADING INSTRUCTIONS
-- ============================================================================

-- STEP 1: Upload CSV files from local machine to Snowflake stage
-- Run these commands from your local SnowSQL CLI or Snowflake web interface:
-- 
-- PUT file://c:/Users/admin/Documents/Github Repos/Customer_Churn_Project/data_generation/customers.csv @CHURN_RAW.RAW.CHURN_STAGE AUTO_COMPRESS=TRUE;
-- PUT file://c:/Users/admin/Documents/Github Repos/Customer_Churn_Project/data_generation/transactions.csv @CHURN_RAW.RAW.CHURN_STAGE AUTO_COMPRESS=TRUE;
-- PUT file://c:/Users/admin/Documents/Github Repos/Customer_Churn_Project/data_generation/subscriptions.csv @CHURN_RAW.RAW.CHURN_STAGE AUTO_COMPRESS=TRUE;
-- PUT file://c:/Users/admin/Documents/Github Repos/Customer_Churn_Project/data_generation/behavioral_events.csv @CHURN_RAW.RAW.CHURN_STAGE AUTO_COMPRESS=TRUE;

-- STEP 2: Verify files are in the stage
-- LIST @CHURN_RAW.RAW.CHURN_STAGE;

-- STEP 3: Load data from stage into raw tables
COPY INTO CHURN_RAW.RAW.CUSTOMERS
FROM @CHURN_RAW.RAW.CHURN_STAGE/customers.csv.gz
FILE_FORMAT = (FORMAT_NAME = 'CHURN_RAW.RAW.CSV_FORMAT')
ON_ERROR = 'CONTINUE'
PURGE = TRUE;

COPY INTO CHURN_RAW.RAW.TRANSACTIONS
FROM @CHURN_RAW.RAW.CHURN_STAGE/transactions.csv.gz
FILE_FORMAT = (FORMAT_NAME = 'CHURN_RAW.RAW.CSV_FORMAT')
ON_ERROR = 'CONTINUE'
PURGE = TRUE;

COPY INTO CHURN_RAW.RAW.SUBSCRIPTIONS
FROM @CHURN_RAW.RAW.CHURN_STAGE/subscriptions.csv.gz
FILE_FORMAT = (FORMAT_NAME = 'CHURN_RAW.RAW.CSV_FORMAT')
ON_ERROR = 'CONTINUE'
PURGE = TRUE;

COPY INTO CHURN_RAW.RAW.BEHAVIORAL_EVENTS
FROM @CHURN_RAW.RAW.CHURN_STAGE/behavioral_events.csv.gz
FILE_FORMAT = (FORMAT_NAME = 'CHURN_RAW.RAW.CSV_FORMAT')
ON_ERROR = 'CONTINUE'
PURGE = TRUE;

-- ============================================================================
-- SECTION 6: DATA VALIDATION
-- ============================================================================

-- Verify row counts
SELECT 'CUSTOMERS' AS table_name, COUNT(*) AS row_count FROM CHURN_RAW.RAW.CUSTOMERS
UNION ALL
SELECT 'TRANSACTIONS' AS table_name, COUNT(*) AS row_count FROM CHURN_RAW.RAW.TRANSACTIONS
UNION ALL
SELECT 'SUBSCRIPTIONS' AS table_name, COUNT(*) AS row_count FROM CHURN_RAW.RAW.SUBSCRIPTIONS
UNION ALL
SELECT 'BEHAVIORAL_EVENTS' AS table_name, COUNT(*) AS row_count FROM CHURN_RAW.RAW.BEHAVIORAL_EVENTS;

-- Check for null customer_ids
SELECT 
  'CUSTOMERS' AS table_name, 
  COUNT(*) AS null_customer_ids 
FROM CHURN_RAW.RAW.CUSTOMERS 
WHERE customer_id IS NULL
UNION ALL
SELECT 
  'TRANSACTIONS' AS table_name, 
  COUNT(*) AS null_customer_ids 
FROM CHURN_RAW.RAW.TRANSACTIONS 
WHERE customer_id IS NULL
UNION ALL
SELECT 
  'SUBSCRIPTIONS' AS table_name, 
  COUNT(*) AS null_customer_ids 
FROM CHURN_RAW.RAW.SUBSCRIPTIONS 
WHERE customer_id IS NULL
UNION ALL
SELECT 
  'BEHAVIORAL_EVENTS' AS table_name, 
  COUNT(*) AS null_customer_ids 
FROM CHURN_RAW.RAW.BEHAVIORAL_EVENTS 
WHERE customer_id IS NULL;

-- Preview sample data
SELECT * FROM CHURN_RAW.RAW.CUSTOMERS LIMIT 5;
SELECT * FROM CHURN_RAW.RAW.TRANSACTIONS LIMIT 5;
SELECT * FROM CHURN_RAW.RAW.SUBSCRIPTIONS LIMIT 5;
SELECT * FROM CHURN_RAW.RAW.BEHAVIORAL_EVENTS LIMIT 5;

-- ============================================================================
-- SECTION 7: GRANT PERMISSIONS (OPTIONAL)
-- ============================================================================

-- Grant usage on warehouse to specific role (adjust role name as needed)
-- GRANT USAGE ON WAREHOUSE ANALYTICS_WH TO ROLE YOUR_ROLE_NAME;

-- Grant database privileges
-- GRANT USAGE ON DATABASE CHURN_RAW TO ROLE YOUR_ROLE_NAME;
-- GRANT USAGE ON DATABASE CHURN_ANALYTICS TO ROLE YOUR_ROLE_NAME;

-- Grant schema privileges
-- GRANT USAGE ON SCHEMA CHURN_RAW.RAW TO ROLE YOUR_ROLE_NAME;
-- GRANT USAGE ON SCHEMA CHURN_ANALYTICS.ANALYTICS TO ROLE YOUR_ROLE_NAME;
-- GRANT CREATE TABLE ON SCHEMA CHURN_ANALYTICS.ANALYTICS TO ROLE YOUR_ROLE_NAME;
-- GRANT CREATE VIEW ON SCHEMA CHURN_ANALYTICS.ANALYTICS TO ROLE YOUR_ROLE_NAME;

-- ============================================================================
-- END OF SETUP SCRIPT
-- ============================================================================
