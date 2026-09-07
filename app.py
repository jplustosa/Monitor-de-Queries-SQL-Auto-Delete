# Monitor de arquivos SQL para Oracle com exportação CSV.
import csv
import glob
import os
import threading
import time
from pathlib import Path

import oracledb
import pandas as pd
import tkinter as tk
from dotenv import load_dotenv
from tkinter import filedialog, messagebox

load_dotenv()

ORACLE_USER = os.getenv("ORACLE_USER")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD")
ORACLE_DSN = os.getenv("ORACLE_DSN")

PASTA_MONITORADA = Path(os.getenv("SQL_WATCH_DIR", "./scripts"))
MONITOR_INTERVAL = int(os.getenv("SQL_MONITOR_INTERVAL", "5"))
monitorando = False
thread_monitoramento = None


def validar_configuracao():
    """Garante que as credenciais Oracle foram fornecidas pelo ambiente."""
    missing = [
        name for name, value in {
            "ORACLE_USER": ORACLE_USER,
            "ORACLE_PASSWORD": ORACLE_PASSWORD,
            "ORACLE_DSN": ORACLE_DSN,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Configuração ausente: {', '.join(missing)}")


def criar_pasta_scripts():
    PASTA_MONITORADA.mkdir(parents=True, exist_ok=True)


def extrair_query_do_arquivo(caminho_arquivo):
    encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
    for encoding in encodings:
        try:
            return Path(caminho_arquivo).read_text(encoding=encoding).strip()
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            print(f"Erro ao ler arquivo: {exc}")
            return None
    return Path(caminho_arquivo).read_text(encoding="utf-8", errors="ignore").strip()


def executar_query_direct(cursor, query):
    try:
        cursor.execute(query)
        return True
    except oracledb.DatabaseError as exc:
        error_obj = exc.args[0]
        print(f"Erro Oracle: {error_obj.code} - {error_obj.message}")
        return False


def apagar_arquivo_script(caminho_arquivo):
    try:
        Path(caminho_arquivo).unlink()
        print(f"Arquivo apagado: {caminho_arquivo}")
        return True
    except OSError as exc:
        print(f"Erro ao apagar arquivo {caminho_arquivo}: {exc}")
        return False


def executar_query(query, nome_arquivo, caminho_script):
    if not query or not query.strip():
        messagebox.showerror("Erro", "Query vazia ou inválida.")
        return False

    try:
        validar_configuracao()
        with oracledb.connect(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN,
        ) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'DD/MM/YYYY'")
                if not executar_query_direct(cursor, query):
                    return False
                columns = [col[0] for col in cursor.description]
                data = cursor.fetchall()

        if not data:
            messagebox.showinfo("Info", "A query não retornou resultados.")
            return apagar_arquivo_script(caminho_script)

        df = pd.DataFrame(data, columns=columns)
        caminho_arquivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=nome_arquivo,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not caminho_arquivo:
            return False

        df.to_csv(
            caminho_arquivo,
            sep=";",
            index=False,
            encoding="utf-8-sig",
            quoting=csv.QUOTE_MINIMAL,
        )
        apagado = apagar_arquivo_script(caminho_script)
        messagebox.showinfo(
            "Sucesso",
            f"Arquivo salvo com sucesso!\nLinhas: {len(df)}\n"
            + ("Script original apagado." if apagado else "Erro ao apagar script."),
        )
        return True
    except oracledb.DatabaseError as exc:
        error_obj = exc.args[0]
        messagebox.showerror("Erro de Banco de Dados", f"Erro Oracle {error_obj.code}:\n{error_obj.message}")
        return False
    except Exception as exc:
        messagebox.showerror("Erro", f"Ocorreu um erro inesperado:\n{exc}")
        return False


def processar_arquivos_txt():
    criar_pasta_scripts()
    arquivos_txt = glob.glob(str(PASTA_MONITORADA / "*.txt"))
    if not arquivos_txt:
        messagebox.showinfo("Info", f"Nenhum arquivo .txt encontrado em '{PASTA_MONITORADA}'.")
        return
    for arquivo in arquivos_txt:
        nome_arquivo = Path(arquivo).name
        query_content = extrair_query_do_arquivo(arquivo)
        if query_content:
            nome_csv = Path(nome_arquivo).with_suffix(".csv").name
            log_mensagem(f"Processando: {nome_arquivo}")
            log_mensagem("Concluído e script apagado." if executar_query(query_content, nome_csv, arquivo) else "Falha ao executar.")
        else:
            log_mensagem(f"Erro ao ler: {nome_arquivo}")


def testar_conexao():
    try:
        validar_configuracao()
        with oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.fetchone()
        messagebox.showinfo("Conexão Testada", "Conexão com o banco de dados bem-sucedida!")
        return True
    except Exception as exc:
        messagebox.showerror("Erro de Conexão", f"Falha na conexão:\n{exc}")
        return False


def monitorar_pasta():
    global monitorando
    criar_pasta_scripts()
    arquivos_processados = set()
    while monitorando:
        try:
            arquivos_atual = set(glob.glob(str(PASTA_MONITORADA / "*.txt")))
            for arquivo in arquivos_atual - arquivos_processados:
                nome_arquivo = Path(arquivo).name
                query_content = extrair_query_do_arquivo(arquivo)
                if query_content:
                    root.after(0, lambda n=nome_arquivo: status_var.set(f"Processando: {n}"))
                    nome_csv = Path(nome_arquivo).with_suffix(".csv").name
                    success = executar_query(query_content, nome_csv, arquivo)
                    if success:
                        arquivos_processados.add(arquivo)
                        root.after(0, lambda n=nome_arquivo: status_var.set(f"Processado: {n}"))
                    root.after(0, lambda n=nome_arquivo, ok=success: log_mensagem(f"{'Concluído' if ok else 'Falha'}: {n}"))
            time.sleep(MONITOR_INTERVAL)
        except Exception as exc:
            root.after(0, lambda e=exc: log_mensagem(f"Erro no monitoramento: {e}"))
            time.sleep(MONITOR_INTERVAL)


def iniciar_monitoramento():
    global monitorando, thread_monitoramento
    if monitorando:
        return
    monitorando = True
    thread_monitoramento = threading.Thread(target=monitorar_pasta, daemon=True)
    thread_monitoramento.start()
    status_var.set("Monitoramento ativo")
    log_mensagem("Monitoramento iniciado.")


def parar_monitoramento():
    global monitorando
    monitorando = False
    status_var.set("Monitoramento parado")
    log_mensagem("Monitoramento parado.")


def limpar_pasta():
    criar_pasta_scripts()
    removidos = 0
    for arquivo in PASTA_MONITORADA.glob("*.txt"):
        try:
            arquivo.unlink()
            removidos += 1
        except OSError as exc:
            log_mensagem(f"Erro ao remover {arquivo.name}: {exc}")
    log_mensagem(f"Arquivos removidos: {removidos}")


def abrir_pasta():
    criar_pasta_scripts()
    os.startfile(PASTA_MONITORADA.resolve()) if os.name == "nt" else os.system(f'xdg-open "{PASTA_MONITORADA.resolve()}"')


def log_mensagem(mensagem):
    log_text.insert(tk.END, mensagem + "\n")
    log_text.see(tk.END)


root = tk.Tk()
root.title("Monitor de Queries SQL")
root.geometry("850x550")
status_var = tk.StringVar(value="Monitoramento parado")

frame = tk.Frame(root)
frame.pack(pady=10)
for texto, comando in [
    ("Testar Conexão", testar_conexao),
    ("Iniciar Monitoramento", iniciar_monitoramento),
    ("Parar Monitoramento", parar_monitoramento),
    ("Processar Arquivos", processar_arquivos_txt),
    ("Abrir Pasta", abrir_pasta),
    ("Limpar Pasta", limpar_pasta),
]:
    tk.Button(frame, text=texto, command=comando).pack(side=tk.LEFT, padx=4)

tk.Label(root, textvariable=status_var).pack(pady=5)
log_text = tk.Text(root, height=25, width=100)
log_text.pack(padx=10, pady=10)
criar_pasta_scripts()
root.mainloop()
