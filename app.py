import streamlit as st
import csv
import io
from collections import defaultdict
from openai import OpenAI
import os  # Add this line to import the os module

def read_csv(file):
    csv_data = []
    csv_file = io.StringIO(file.getvalue().decode("utf-8"))
    reader = csv.reader(csv_file, delimiter=';')
    for row in reader:
        csv_data.append(row)
    return csv_data

def print_csv_preview(data, num_rows=5):
    st.subheader("Vista previa del archivo CSV:")
    for i, row in enumerate(data[:num_rows]):
        st.text(f"Fila {i}: {row}")
    st.text("...")

def calculate_sales_per_salesman(data):
    sales_per_salesman = defaultdict(float)
    for row in data[1:]:  # Skip header row
        if len(row) >= 6:
            salesman = row[0]  # Salesman name is in the first column
            if salesman.lower() == "total":  # Ignore "Total" row
                continue
            try:
                sale = float(row[5].replace('$', '').replace('.', '').replace(',', '.'))
                sales_per_salesman[salesman] += sale
            except ValueError:
                continue  # Skip rows where sale amount is not a valid number
    return dict(sales_per_salesman)

def generate_report(sales_per_salesman, total_budget, salesman_budget):
    total_sales = sum(sales_per_salesman.values())
    num_salesmen = len(sales_per_salesman)
    
    st.subheader("Informe de Ventas")
    st.write(f"Ventas Totales: ${total_sales:.2f}")
    st.write(f"Presupuesto Total: ${total_budget:.2f}")
    st.write(f"Diferencia: ${total_sales - total_budget:.2f}")
    st.write(f"Porcentaje del Presupuesto Alcanzado: {(total_sales / total_budget) * 100:.2f}%")

    st.write(f"Presupuesto Individual por Vendedor: ${salesman_budget:.2f}")
    st.write(f"Total de Vendedores: {num_salesmen}")

    st.subheader("Ventas por Vendedor:")
    for salesman, sales in sales_per_salesman.items():
        st.write(f"\n{salesman}:")
        st.write(f"  Ventas: ${sales:.2f}")
        st.write(f"  Presupuesto: ${salesman_budget:.2f}")
        st.write(f"  Diferencia: ${sales - salesman_budget:.2f}")
        st.write(f"  Porcentaje del Presupuesto Alcanzado: {(sales / salesman_budget) * 100:.2f}%")

def get_openai_response(prompt, data, api_key):
    client = OpenAI(api_key=api_key)
    
    context = f"CSV data: {data[:10]}\n\nQuestion: {prompt}\n\nAnswer:"
    
    try:
        response = client.chat.completions.create(
            model="GPT-4o mini",  # Make sure this model name is correct and available to you
            messages=[
                {"role": "system", "content": "You are an expert senior sales analyst that answers questions about CSV data."},
                {"role": "user", "content": context}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error al obtener respuesta de OpenAI: {str(e)}"

def ask_questions(csv_data):
    st.subheader("Preguntas sobre el archivo CSV")
    st.write("Para hacer preguntas sobre los datos, necesitará una clave de API de OpenAI.")
    
    api_key = st.text_input("Ingrese su clave secreta de la API de OpenAI:", type="password")
    question = st.text_input("Haga una pregunta sobre los datos del archivo CSV:")

    if st.button("Obtener Respuesta") and api_key and question:
        answer = get_openai_response(question, csv_data, api_key)
        st.write(f"Respuesta: {answer}")

def main():
    st.title("Análisis de Ventas")

    uploaded_file = st.file_uploader("Cargar archivo CSV", type="csv")
    
    if uploaded_file is not None:
        csv_data = read_csv(uploaded_file)
        if not csv_data:
            st.error("Error: El archivo CSV está vacío.")
            return

        print_csv_preview(csv_data)

        sales_per_salesman = calculate_sales_per_salesman(csv_data)

        if not sales_per_salesman:
            st.error("Error: No se encontraron datos de ventas válidos en el archivo CSV.")
            return

        total_budget = st.number_input("Ingrese el objetivo de ventas total (presupuesto) para todos los vendedores combinados: $", min_value=0.0, step=1000.0)
        salesman_budget = st.number_input("Ingrese el presupuesto individual para cada vendedor: $", min_value=0.0, step=100.0)

        if st.button("Generar Informe"):
            generate_report(sales_per_salesman, total_budget, salesman_budget)

        ask_questions(csv_data)

if __name__ == "__main__":
    main()