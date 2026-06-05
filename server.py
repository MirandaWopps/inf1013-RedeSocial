from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json
import os

app = Flask(__name__)

# Arquivo para persistência dos dados
DATA_FILE = 'posts.json'

# Estrutura de dados para posts
def load_posts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_posts(posts):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

# Inicializar posts
posts = load_posts()
if not posts:
    # Posts de exemplo
    posts = [
        {
            'id': 1,
            'username': 'Maria Silva',
            'content': 'Acabei de lançar meu novo projeto! Estou muito animada para compartilhar isso com vocês. 🎉',
            'timestamp': '2026-06-05T09:00:00',
            'likes': 124,
            'comments': 18,
            'shares': 5
        },
        {
            'id': 2,
            'username': 'João Santos',
            'content': 'Bom dia! Começando a semana com energia positiva. ☀️',
            'timestamp': '2026-06-05T06:00:00',
            'likes': 43,
            'comments': 7,
            'shares': 2
        }
    ]
    save_posts(posts)

def format_time_ago(timestamp):
    """Formata o timestamp para 'X horas/minutos atrás'"""
    try:
        post_time = datetime.fromisoformat(timestamp)
        now = datetime.now()
        diff = now - post_time
        
        if diff.days > 0:
            if diff.days == 1:
                return "Ontem"
            return f"{diff.days} dias atrás"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} horas atrás" if hours > 1 else "1 hora atrás"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutos atrás" if minutes > 1 else "1 minuto atrás"
        else:
            return "Agora mesmo"
    except:
        return timestamp

# Rotas da API
@app.route('/api/posts', methods=['GET'])
def get_posts():
    """Retorna todos os posts"""
    return jsonify(posts)

@app.route('/api/posts', methods=['POST'])
def create_post():
    """Cria um novo post"""
    data = request.json
    new_post = {
        'id': len(posts) + 1,
        'username': data.get('username', 'Anônimo'),
        'content': data.get('content', ''),
        'timestamp': datetime.now().isoformat(),
        'likes': 0,
        'comments': 0,
        'shares': 0,
        'is_share': data.get('is_share', False),
        'original_author': data.get('original_author', None)
    }
    posts.insert(0, new_post)  # Adiciona no início
    save_posts(posts)
    return jsonify(new_post), 201

@app.route('/api/posts/<int:post_id>/share', methods=['POST'])
def share_post(post_id):
    """Compartilha um post existente"""
    # Encontrar o post original
    original_post = None
    for post in posts:
        if post['id'] == post_id:
            original_post = post
            break
    
    if not original_post:
        return jsonify({'error': 'Post não encontrado'}), 404
    
    # Incrementar contador de compartilhamentos do post original
    original_post['shares'] = original_post.get('shares', 0) + 1
    save_posts(posts)
    
    # Criar novo post como compartilhamento
    data = request.json
    shared_post = {
        'id': len(posts) + 1,
        'username': data.get('username', 'Leitor Conectado'),
        'content': original_post['content'],
        'timestamp': datetime.now().isoformat(),
        'likes': 0,
        'comments': 0,
        'shares': 0,
        'is_share': True,
        'original_author': original_post['username'],
        'original_post_id': original_post['id']
    }
    posts.insert(0, shared_post)
    save_posts(posts)
    return jsonify(shared_post), 201

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    """Adiciona um like ao post"""
    for post in posts:
        if post['id'] == post_id:
            post['likes'] += 1
            save_posts(posts)
            return jsonify({'likes': post['likes']})
    return jsonify({'error': 'Post não encontrado'}), 404

@app.route('/api/posts/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    """Adiciona um comentário ao post"""
    data = request.json
    for post in posts:
        if post['id'] == post_id:
            post['comments'] = post.get('comments', 0) + 1
            save_posts(posts)
            return jsonify({'comments': post['comments']})
    return jsonify({'error': 'Post não encontrado'}), 404

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Deleta um post"""
    global posts
    posts = [post for post in posts if post['id'] != post_id]
    save_posts(posts)
    return jsonify({'message': 'Post deletado com sucesso'}), 200

# Rota principal - interface web
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# Template HTML/CSS/JS
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rede Social</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
        }

        .header {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        h1 {
            color: #333;
            margin-bottom: 20px;
            font-size: 2em;
        }

        .create-post {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .create-post input,
        .create-post textarea {
            width: 100%;
            padding: 12px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
        }

        .create-post textarea {
            min-height: 100px;
            resize: vertical;
        }

        .create-post button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: transform 0.2s;
        }

        .create-post button:hover {
            transform: translateY(-2px);
        }

        .feed {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .feed h2 {
            margin-bottom: 20px;
            color: #333;
        }

        .post {
            border-bottom: 1px solid #eee;
            padding: 20px 0;
            transition: background 0.2s;
        }

        .post:last-child {
            border-bottom: none;
        }

        .post:hover {
            background: #f9f9f9;
            padding-left: 10px;
            padding-right: 10px;
        }

        .share-indicator {
            background: #f0f2f5;
            padding: 8px 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 13px;
            color: #65676b;
        }

        .share-indicator i {
            margin-right: 5px;
        }

        .post-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .username {
            font-weight: bold;
            color: #667eea;
            font-size: 16px;
        }

        .timestamp {
            color: #999;
            font-size: 12px;
        }

        .post-content {
            color: #333;
            line-height: 1.5;
            margin-bottom: 15px;
            word-wrap: break-word;
        }

        .post-actions {
            display: flex;
            gap: 20px;
            align-items: center;
            margin-top: 10px;
        }

        .action-btn {
            background: none;
            border: none;
            cursor: pointer;
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 14px;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #65676b;
        }

        .action-btn:hover {
            background: #f0f2f5;
        }

        .like-btn:hover {
            color: #4caf50;
        }

        .comment-btn:hover {
            color: #2196f3;
        }

        .share-btn:hover {
            color: #9c27b0;
        }

        .stats {
            font-size: 13px;
            color: #65676b;
        }

        .empty-feed {
            text-align: center;
            color: #999;
            padding: 40px;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .post {
            animation: fadeIn 0.3s ease-out;
        }

        .share-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }

        .share-modal-content {
            background: white;
            padding: 30px;
            border-radius: 12px;
            max-width: 400px;
            width: 90%;
        }

        .share-modal-content h3 {
            margin-bottom: 20px;
        }

        .share-modal-content input {
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #ddd;
            border-radius: 6px;
        }

        .modal-buttons {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }

        .modal-buttons button {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }

        .modal-buttons button:first-child {
            background: #ddd;
        }

        .modal-buttons button:last-child {
            background: #667eea;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Rede Social</h1>
        </div>

        <div class="create-post">
            <input type="text" id="username" placeholder="Seu nome" maxlength="50">
            <textarea id="content" placeholder="O que você está pensando?"></textarea>
            <button onclick="createPost()">Publicar</button>
        </div>

        <div class="feed">
            <h2>Feed</h2>
            <div id="posts-container"></div>
        </div>
    </div>

    <!-- Modal de Compartilhamento -->
    <div id="shareModal" class="share-modal">
        <div class="share-modal-content">
            <h3>Compartilhar Post</h3>
            <input type="text" id="shareUsername" placeholder="Seu nome (opcional)">
            <div class="modal-buttons">
                <button onclick="closeShareModal()">Cancelar</button>
                <button onclick="confirmShare()">Compartilhar</button>
            </div>
        </div>
    </div>

    <script>
        let currentSharePostId = null;

        async function loadPosts() {
            try {
                const response = await fetch('/api/posts');
                const posts = await response.json();
                displayPosts(posts);
            } catch (error) {
                console.error('Erro ao carregar posts:', error);
            }
        }

        function formatTimestamp(timestamp) {
            const postDate = new Date(timestamp);
            const now = new Date();
            const diffTime = Math.abs(now - postDate);
            const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
            const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
            const diffMinutes = Math.floor(diffTime / (1000 * 60));

            if (diffDays > 0) {
                return diffDays === 1 ? 'Ontem' : `${diffDays} dias atrás`;
            } else if (diffHours > 0) {
                return `${diffHours} ${diffHours === 1 ? 'hora' : 'horas'} atrás`;
            } else if (diffMinutes > 0) {
                return `${diffMinutes} ${diffMinutes === 1 ? 'minuto' : 'minutos'} atrás`;
            } else {
                return 'Agora mesmo';
            }
        }

        function displayPosts(posts) {
            const container = document.getElementById('posts-container');
            
            if (posts.length === 0) {
                container.innerHTML = '<div class="empty-feed">Nenhum post ainda. Seja o primeiro a publicar!</div>';
                return;
            }

            container.innerHTML = posts.map(post => {
                let shareHtml = '';
                if (post.is_share) {
                    shareHtml = `
                        <div class="share-indicator">
                            🔄 ${escapeHtml(post.username)} compartilhou de ${escapeHtml(post.original_author)}
                        </div>
                    `;
                }

                return `
                    <div class="post" id="post-${post.id}">
                        ${shareHtml}
                        <div class="post-header">
                            <span class="username">${post.is_share ? '' : escapeHtml(post.username)}</span>
                            <span class="timestamp">${formatTimestamp(post.timestamp)}</span>
                        </div>
                        <div class="post-content">${escapeHtml(post.content)}</div>
                        <div class="stats">
                            ❤️ ${post.likes}   💬 ${post.comments}   🔄 ${post.shares || 0}
                        </div>
                        <div class="post-actions">
                            <button class="action-btn like-btn" onclick="handleLike(${post.id})">
                                👍 Curtir
                            </button>
                            <button class="action-btn comment-btn" onclick="handleComment(${post.id})">
                                💬 Comentar
                            </button>
                            <button class="action-btn share-btn" onclick="openShareModal(${post.id})">
                                🔄 Compartilhar
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        async function createPost() {
            const username = document.getElementById('username').value.trim();
            const content = document.getElementById('content').value.trim();

            if (!content) {
                alert('Por favor, escreva algo para publicar!');
                return;
            }

            try {
                const response = await fetch('/api/posts', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: username || 'Anônimo',
                        content: content,
                        is_share: false
                    })
                });

                if (response.ok) {
                    document.getElementById('username').value = '';
                    document.getElementById('content').value = '';
                    loadPosts();
                }
            } catch (error) {
                console.error('Erro ao criar post:', error);
                alert('Erro ao publicar. Tente novamente.');
            }
        }

        function openShareModal(postId) {
            currentSharePostId = postId;
            document.getElementById('shareModal').style.display = 'flex';
            document.getElementById('shareUsername').value = '';
        }

        function closeShareModal() {
            document.getElementById('shareModal').style.display = 'none';
            currentSharePostId = null;
        }

        async function confirmShare() {
            if (!currentSharePostId) return;
            
            const username = document.getElementById('shareUsername').value.trim();
            
            try {
                const response = await fetch(`/api/posts/${currentSharePostId}/share`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: username || 'Leitor Conectado'
                    })
                });

                if (response.ok) {
                    alert('Post compartilhado com sucesso!');
                    closeShareModal();
                    loadPosts();
                } else {
                    alert('Erro ao compartilhar. Tente novamente.');
                }
            } catch (error) {
                console.error('Erro ao compartilhar:', error);
                alert('Erro ao compartilhar. Tente novamente.');
            }
        }

        async function handleLike(postId) {
            try {
                const response = await fetch(`/api/posts/${postId}/like`, {
                    method: 'POST'
                });
                if (response.ok) {
                    loadPosts();
                }
            } catch (error) {
                console.error('Erro ao dar like:', error);
            }
        }

        async function handleComment(postId) {
            const comment = prompt('Digite seu comentário:');
            if (comment && comment.trim()) {
                try {
                    const response = await fetch(`/api/posts/${postId}/comment`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ comment: comment })
                    });
                    if (response.ok) {
                        alert('Comentário adicionado!');
                        loadPosts();
                    }
                } catch (error) {
                    console.error('Erro ao comentar:', error);
                }
            }
        }

        // Fechar modal ao clicar fora
        window.onclick = function(event) {
            const modal = document.getElementById('shareModal');
            if (event.target === modal) {
                closeShareModal();
            }
        }

        // Carregar posts ao iniciar
        loadPosts();

        // Atualizar feed a cada 30 segundos
        setInterval(loadPosts, 30000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)