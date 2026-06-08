# FastAPI Todo/Tag 管理アプリ

このプロジェクトは、FastAPI と PostgreSQL をベースにした Todo 管理アプリです。ユーザー認証、タグ管理、Todo 作成・更新・削除、検索、ページング、および CSRF 保護が含まれています。

## 特長

- ユーザー登録・ログイン機能
- Todo の CRUD 操作
- タグの CRUD 操作
- タグと Todo の紐付け
- CSRF トークンによる保護
- Gunicorn + Uvicorn での本番起動
- Docker Compose による PostgreSQL とアプリの起動
- Alembic によるマイグレーション管理
- Jinja2 テンプレートによる HTML レンダリング
- 静的ファイルサポート

## 必要条件

- Python 3.13 以上
- Docker
- Docker Compose

## セットアップ

1. リポジトリをクローン

```bash
git clone <repository-url>
cd fastapi-test
```

2. 環境変数ファイルを作成

```bash
copy .env.example .env
```

Windows PowerShell では:

```powershell
Copy-Item .env.example .env
```

3. `.env` の値を必要に応じて調整

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_PORT`
- `DB_URL`
- `PORT_APP`
- `ENVIRONMENT`
- `ALLOWED_ORIGINS`
- `ALLOWED_HOSTS`

## Docker Compose で起動

```bash
docker compose up --build
```

起動後、アプリは `http://localhost:8000` で利用できます。

`docker-compose.yml` には以下のサービスが定義されています:

- `db` : PostgreSQL
- `app` : FastAPI アプリ
- `test_app` / `test_db` : テスト用サービス

## ローカル実行（venv または pip）

### 仮想環境の作成

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 依存関係のインストール

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### マイグレーション実行

```bash
alembic upgrade head
```

### アプリ起動

```bash
docker compose up -d
```

## テスト

テストは `pytest` で実行します。

```bash
pytest
```

Docker Compose 経由でテスト環境を用意する場合は、`test_app` と `test_db` サービスを使用します。

## ディレクトリ構成

- `app/`
  - `routers/` : ルーティング処理
  - `models.py` : ORM モデル定義
  - `schemas.py` : Pydantic スキーマ
  - `crud.py` : DB 操作
  - `database.py` : DB 接続・依存関係
  - `auth.py` : トークン認証
- `templates/` : Jinja2 テンプレート
- `static/` : CSS などの静的ファイル
- `docker/` : Dockerfile
- `migration/` : Alembic 設定とバージョン管理
- `tests/` : テストコード

## 主要エンドポイント

- `GET /account/register` : 登録ページ
- `POST /account/register` : 登録処理
- `GET /account/login` : ログインページ
- `POST /account/login` : ログイン処理
- `GET /api/todo` : Todo 一覧
- `GET /api/todo/{todo_id}` : Todo 詳細
- `POST /api/todo` : Todo 作成
- `PUT /api/todo/{todo_id}` : Todo 更新
- `DELETE /api/todo/{todo_id}` : Todo 削除
- `GET /api/tag` : タグ一覧
- `GET /api/tag/{tag_id}` : タグ詳細
- `POST /api/tag` : タグ作成
- `PUT /api/tag/{tag_id}` : タグ更新
- `DELETE /api/tag/{tag_id}` : タグ削除

## 補足

- `main.py` で `TrustedHostMiddleware` とセキュリティヘッダーを設定しています。
- `docker/Dockerfile` では `requirements.txt` を使って依存関係を固定インストールします。
- `packages.json` は Tailwind CSS 用の `devDependencies` が定義されています。

---

必要であれば、README にさらに「開発者向け実装説明」や「データベース初期化手順」などの節を追加できます。
