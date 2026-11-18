# =========================
# TREINOS
# =========================

@app.route("/api/treinos", methods=["GET"])
def listar_treinos():
    conexao = conectar()
    try:
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
        return jsonify([dict(treino) for treino in treinos])
    finally:
        conexao.close()


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
    try:
        aluno = conexao.execute(
            "SELECT id FROM alunos WHERE id = ?",
            (aluno_id,)
        ).fetchone()

        if not aluno:
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

        return jsonify({
            "mensagem": "Treino cadastrado com sucesso!",
            "id": treino_id
        }), 201
    finally:
        conexao.close()


# =========================
# INICIALIZAÇÃO DO SERVIDOR
# =========================

if __name__ == "__main__":
    app.run(debug=True, port=5000)
