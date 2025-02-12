import configparser
import pandas
import psycopg2


def is_company(document: str) -> int:
    """ Remove symbols and define if is a person or a company by document size """
    document = document.replace('.', '')
    document = document.replace('-', '')
    document = document.replace('/', '')
    if len(document) > 11:
        return 1
    return 0

def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        conn = psycopg2.connect(
            host=config['database']['host'],
            port=config['database']['port'],
            dbname=config['database']['dbname'],
            user=config['database']['user'],
            password=config['database']['password']
        )

        cursor = conn.cursor()
        print('Database successfully connected.')

        sheet = pandas.read_excel(config['sheet']['file_name'])
        for index, row in sheet.iterrows():
            values = (
                row['Nome'], row['CPF/CNPJ'],
                row['Telefones'], row['Endereço'],
                row['Complemento'], row['Estado'],
                row['CEP'], row['Cidade'],
                0, is_company(str(row['CPF/CNPJ']))
            )

            cursor.execute('''
                INSERT INTO controle_processos.pessoa (nome, documento, celular, logradoura, complemento, unidade_federativa, cep, cidade, numero, tipo_pessoa)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);''', values)

            conn.commit()
            print(f'Row {index}: {row.to_dict()}')

        # Queries for set null in database when the column is empty in Excel sheet
        queries = [
            "UPDATE controle_processos.pessoa SET nome = '' WHERE nome = 'NaN' RETURNING id;",
            "UPDATE controle_processos.pessoa SET documento = '' WHERE documento = 'NaN' RETURNING id;",
            "UPDATE controle_processos.pessoa SET celular = NULL WHERE celular = 'NaN' RETURNING id;",
            "UPDATE controle_processos.pessoa SET logradoura = NULL WHERE logradoura = 'NaN' RETURNING id;",
            "UPDATE controle_processos.pessoa SET complemento = NULL WHERE complemento = 'NaN' RETURNING id;",
            "UPDATE controle_processos.pessoa SET unidade_federativa = NULL WHERE unidade_federativa = 'NaN' RETURNING id;",
            "UPDATE controle_processos.pessoa SET cep = NULL WHERE cep = 'NaN' RETURNING id;",
            "UPDATE controle_processos.pessoa SET cidade = NULL WHERE cidade = 'NaN' RETURNING id;"
        ]

        for operation in queries:
            cursor.execute(operation)
            conn.commit()

            if cursor.fetchone():
                print(f'Total rows updated: {cursor.rowcount}.')
            else:
                print('There is no row which match with filters.')

        cursor.close()
        conn.close()
        print('Database connection successfully closed.')
    except FileNotFoundError as error:
        print('Excel file was not found: ', error)
    except Exception as error:
        print('Database connection failed: ', error)

if __name__ == '__main__':
    main()