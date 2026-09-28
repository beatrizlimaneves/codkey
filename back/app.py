from flask import Flask, request, jsonify
from flask_cors import CORS
from database import conectar, criar_banco
import os

app = Flask(__name__)
CORS(app)

# Cria o banco e as tabelas quando o servidor inicia
criar_banco()


@app.route("/")
def inicio():
    return jsonify({
        "mensagem": "API Academia das Maravilhas funcionando!"
    })


@app.route("/api/teste", methods=["GET"])
def teste():
    return jsonify({
        "status": "ok",
        "mensagem": "Conexão com a API funcionando."
    })


# =========================
# USUÁRIOS / LOGIN
# =========================

@app.route("/api/cadastro", methods=["POST"])
def cadastro():
    dados = request.get_json() or {}

    nome = dados.get("nome")
    email = dados.get("email")
    senha = dados.get("senha")

    if not nome or not email or not senha:
        return jsonify({
            "erro": "Nome, email e senha são obrigatórios."
        }), 400

    conexao = conectar()

    try:
        conexao.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
            (nome, email, senha)
        )
        conexao.commit()

        return jsonify({
            "mensagem": "Cadastro realizado com sucesso!"
        }), 201

    except Exception as erro:
        if "UNIQUE" in str(erro).upper():
            return jsonify({
                "erro": "Este email já está cadastrado."
            }), 409

        return jsonify({
            "erro": str(erro)
        }), 500

    finally:
        conexao.close()


@app.route("/api/login", methods=["POST"])
def login():
    dados = request.get_json() or {}

    email = dados.get("email")
    senha = dados.get("senha")

    if not email or not senha:
        return jsonify({
            "erro": "Email e senha são obrigatórios."
        }), 400

    conexao = conectar()

    usuario = conexao.execute(
        "SELECT id, nome, email FROM usuarios WHERE email = ? AND senha = ?",
        (email, senha)
    ).fetchone()

    conexao.close()

    if not usuario:
        return jsonify({
            "erro": "Email ou senha incorretos."
        }), 401

    return jsonify({
        "mensagem": "Login realizado com sucesso!",
        "usuario": dict(usuario)
    })


# =========================
# ALUNOS
# =========================

@app.route("/api/alunos", methods=["GET"])
def listar_alunos():
    conexao = conectar()

    alunos = conexao.execute(
        "SELECT * FROM alunos ORDER BY id DESC"
    ).fetchall()

    conexao.close()

    return jsonify([dict(aluno) for aluno in alunos])


@app.route("/api/alunos", methods=["POST"])
def cadastrar_aluno():
    dados = request.get_json() or {}

    nome = dados.get("nome")
    email = dados.get("email")
    telefone = dados.get("telefone")
    idade = dados.get("idade")

    if not nome:
        return jsonify({
            "erro": "O nome do aluno é obrigatório."
        }), 400

    conexao = conectar()

    cursor = conexao.execute(
        """
        INSERT INTO alunos (nome, email, telefone, idade)
        VALUES (?, ?, ?, ?)
        """,
        (nome, email, telefone, idade)
    )

    conexao.commit()
    aluno_id = cursor.lastrowid
    conexao.close()

    return jsonify({
        "mensagem": "Aluno cadastrado com sucesso!",
        "id": aluno_id
    }), 201


@app.route("/api/alunos/<int:id>", methods=["DELETE"])
def excluir_aluno(id):
    conexao = conectar()

    cursor = conexao.execute(
        "DELETE FROM alunos WHERE id = ?",
        (id,)
    )

    conexao.commit()
    conexao.close()

    if cursor.rowcount == 0:
        return jsonify({
            "erro": "Aluno não encontrado."
        }), 404

    return jsonify({
        "mensagem": "Aluno excluído com sucesso!"
    })


# =========================
# PLANOS
# =========================

@app.route("/api/planos", methods=["GET"])
def listar_planos():
    conexao = conectar()

    planos = conexao.execute(
        "SELECT * FROM planos ORDER BY id DESC"
    ).fetchall()

    conexao.close()

    return jsonify([dict(plano) for plano in planos])


@app.route("/api/planos", methods=["POST"])
def cadastrar_plano():
    dados = request.get_json() or {}

    nome = dados.get("nome")
    preco = dados.get("preco")
    descricao = dados.get("descricao")

    if not nome or preco is None:
        return jsonify({
            "erro": "Nome e preço são obrigatórios."
        }), 400

    try:
        preco = float(preco)
    except (TypeError, ValueError):
        return jsonify({
            "erro": "O preço precisa ser um número."
        }), 400

    conexao = conectar()

    cursor = conexao.execute(
        """
        INSERT INTO planos (nome, preco, descricao)
        VALUES (?, ?, ?)
        """,
        (nome, preco, descricao)
    )

    conexao.commit()
    plano_id = cursor.lastrowid
    conexao.close()

    return jsonify({
        "mensagem": "Plano cadastrado com sucesso!",
        "id": plano_id
    }), 201


# =========================
# PAGAMENTOS
# =========================

@app.route("/api/pagamentos", methods=["GET"])
def listar_pagamentos():
    conexao = conectar()

    pagamentos = conexao.execute(
        """
        SELECT
            pagamentos.id,
            pagamentos.aluno_id,
            alunos.nome AS aluno,
            pagamentos.valor,
            pagamentos.data,
            pagamentos.status
        FROM pagamentos
        INNER JOIN alunos ON alunos.id = pagamentos.aluno_id
        ORDER BY pagamentos.id DESC
        """
    ).fetchall()

    conexao.close()

    return jsonify([dict(pagamento) for pagamento in pagamentos])


@app.route("/api/pagamentos", methods=["POST"])
def cadastrar_pagamento():
    dados = request.get_json() or {}

    aluno_id = dados.get("aluno_id")
    valor = dados.get("valor")
    data = dados.get("data")
    status = dados.get("status", "Pendente")

    if aluno_id is None or valor is None or not data:
        return jsonify({
            "erro": "Aluno, valor e data são obrigatórios."
        }), 400

    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return jsonify({
            "erro": "O valor precisa ser um número."
        }), 400

    conexao = conectar()

    aluno = conexao.execute(
        "SELECT id FROM alunos WHERE id = ?",
        (aluno_id,)
    ).fetchone()

    if not aluno:
        conexao.close()
        return jsonify({
            "erro": "Aluno não encontrado."
        }), 404

    cursor = conexao.execute(
        """
        INSERT INTO pagamentos (aluno_id, valor, data, status)
        VALUES (?, ?, ?, ?)
        """,
        (aluno_id, valor, data, status)
    )

    conexao.commit()
    pagamento_id = cursor.lastrowid
    conexao.close()

    return jsonify({
        "mensagem": "Pagamento cadastrado com sucesso!",
        "id": pagamento_id
    }), 201


# =========================
# TREINOS
# =========================

@app.route("/api/treinos", methods=["GET"])
def listar_treinos():
    conexao = conectar()

    treinos = conexao.execute(
        """
        SELECT
            treinos.id,
            treinos.aluno_id,
            alunos.nome AS aluno,
            treinos.nome,
            treinos.descricao
        FROM treinos
        INNER JOIN alunos ON alunos.id = treinos.aluno_id
        ORDER BY treinos.id DESC
        """
    ).fetchall()

    conexao.close()

    return jsonify([dict(treino) for treino in treinos])


@app.route("/api/treinos", methods=["POST"])
def cadastrar_treino():
    dados = request.get_json() or {}

    aluno_id = dados.get("aluno_id")
    nome = dados.get("nome")
    descricao = dados.get("descricao")

    if aluno_id is None or not nome:
        return jsonify({
            "erro": "Aluno e nome do treino são obrigatórios."
        }), 400

    conexao = conectar()

    aluno = conexao.execute(
        "SELECT id FROM alunos WHERE id = ?",
        (aluno_id,)
    ).fetchone()

    if not aluno:
        conexao.close()
        return jsonify({
            "erro": "Aluno não encontrado."
        }), 404

    cursor = conexao.execute(
        """
        INSERT INTO treinos (aluno_id, nome, descricao)
        VALUES (?, ?, ?)
        """,
        (aluno_id, nome, descricao)
    )

    conexao.commit()
    treino_id = cursor.lastrowid
    conexao.close()

    return jsonify({
        "mensagem": "Treino cadastrado com sucesso!",
        "id": treino_id
    }), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
