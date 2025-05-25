import streamlit as st
import oracledb

# Function to connect to the Oracle database
def connect_to_db():
    conn = oracledb.connect(
        user="system",
        password="nerain$1",
        dsn="127.0.0.1:1521/xe"  # Root container
    )
    return conn

# Function to fetch all employee data
def fetch_employees():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employee")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# Function to insert an employee into the database
def insert_employee(emp_id, emp_name, salary):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO employee (EMP_ID, EMP_NAME, SALARY) VALUES (:1, :2, :3)", (emp_id, emp_name, salary))
        conn.commit()
        st.success("Employee inserted successfully!")
    except oracledb.Error as e:
        st.error(f"Error inserting employee: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to delete an employee based on ID
def delete_employee(emp_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM employee WHERE EMP_ID = :1", (emp_id,))
        conn.commit()
        st.success(f"Employee with ID {emp_id} deleted successfully!")
    except oracledb.Error as e:
        st.error(f"Error deleting employee: {e}")
    finally:
        cursor.close()
        conn.close()

# Streamlit UI
st.title("Employee Management System")

# Fetch employees and display in a table
st.subheader("Employee List")
employees = fetch_employees()
if employees:
    st.write("### Employee Details")
    st.table(employees)

# Insert Employee Form
st.subheader("Insert New Employee")
emp_id = st.number_input("Employee ID", min_value=1, step=1)
emp_name = st.text_input("Employee Name")
salary = st.number_input("Salary", min_value=1, step=1000)

if st.button("Insert Employee"):
    if emp_name and salary > 0:
        insert_employee(emp_id, emp_name, salary)
    else:
        st.error("Please enter valid details")

# Delete Employee Form
st.subheader("Delete Employee")
emp_id_to_delete = st.number_input("Employee ID to delete", min_value=1, step=1)

if st.button("Delete Employee"):
    if emp_id_to_delete:
        delete_employee(emp_id_to_delete)
    else:
        st.error("Please enter a valid Employee ID")