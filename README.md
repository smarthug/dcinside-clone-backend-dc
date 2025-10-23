

# DCInside Clone — Backend (Django + DRF + PostgreSQL) 

VSCode(Windows, PowerShell)에서 **uv + 로컬 실행** 바로 되게 “명령어 + 무슨 일 하는지”를 정리했습니다.
DB는 **Docker의 PostgreSQL**로 띄우고, Django 앱은 **로컬(uv)** 로 실행하는 플로우 기준입니다.

---

## 0) 프로젝트 폴더 준비

```powershell
# 다운받은 zip 풀기 -> 폴더로 이동
cd "C:\path\to\dcinside-clone-backend-dc"
```

* 압축을 푼 **프로젝트 루트**로 이동합니다.

---

## 1) uv & 가상환경

```powershell
# uv 설치 (없다면)
python -m pip install --upgrade uv

# 가상환경 생성 (.venv 폴더)
uv venv

# 가상환경 활성화 (PowerShell)
. .\.venv\Scripts\Activate.ps1
```

* `uv venv`는 `.venv`를 만들고
* `Activate.ps1`는 가상환경을 현재 터미널 세션에 적용합니다.
* **실행 정책 오류**가 뜬다면:

  ```powershell
  Set-ExecutionPolicy -Scope Process RemoteSigned
  ```

---

## 2) 의존성 설치

```powershell
# pyproject.toml 기반 의존성 설치
uv sync
# (동일 효과) uv pip install -e .
```

* Django, DRF, psycopg, SimpleJWT, CORS, Pillow, dj-database-url 등을 설치합니다.

---

## 3) Postgres(DB) 띄우기 — Docker

### A안: compose로 DB만 켜서 사용 (추천)

```powershell
# Docker Desktop 실행되어 있어야 함
docker compose up -d db
```

* `postgres:16-alpine` 컨테이너가 5432 포트를 엽니다.
* 컨테이너 이름은 compose 내부적으로 `dcinside-clone-backend-dc-db-1` 형태로 생성됩니다.

### B안: 단독 docker run (compose 안 쓰고)

```powershell
docker run -d --name dcclone-db `
  -e POSTGRES_DB=dcclone `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -p 5432:5432 postgres:16-alpine
```

* 이름을 `dcclone-db`로 지정해 독립 실행합니다.

---

## 4) 환경변수 파일(.env) 만들기

```powershell
copy .env.example .env
notepad .env
```

* 열리는 메모장에서 **DATABASE_URL**을 아래처럼 확인/수정:

  * Docker DB로 로컬 실행 시 보통:

    ```
    DATABASE_URL=postgres://postgres:postgres@localhost:5432/dcclone
    ```
  * 프런트 개발 환경을 쓸 거면 CORS도 필요에 따라 수정:

    ```
    CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
    ```
* `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`도 필요 시 조정.

---

## 5) Django 초기화(마이그레이션)

이 프로젝트는 **커스텀 User + Gallery/Post/Comment + Vote 모델**이 있으므로, **makemigrations → migrate** 순으로 진행합니다.

```powershell
# 장고 버전 확인(선택)
uv run python -m django --version

# 마이그레이션 파일 생성
uv run python manage.py makemigrations users core

# DB 반영
uv run python manage.py migrate

# 관리자 계정 생성
uv run python manage.py createsuperuser
```

* `makemigrations`는 모델 변경점을 마이그레이션 파일로 생성
* `migrate`는 해당 파일을 DB에 반영
* `createsuperuser`는 /admin 로그인용 관리자 생성

---

## 6) 서버 실행

```powershell
uv run python manage.py runserver
```

* 브라우저에서:

  * API root: [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)
  * Admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## (옵션) 전체 Docker로 실행하고 싶다면

```powershell
docker compose up --build -d
# 최초 1회
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

* 이 모드는 **웹(장고)도 컨테이너**로 돌고, 포트 8000을 엽니다.

---

## 스키마 개요 (디시형)

```
Gallery (1) ──< (N) Post (1) ──< (N) Comment
```

* **Gallery**: 게시판 (slug, title)
* **Post**: 글 (title, content, image 1장, recommend, views, 익명 닉네임 허용)
* **Comment**: 댓글/대댓글 (self-referential parent)

보조 테이블:

* **PostVote**: (post, user, value ∈ {1, -1})
* **CommentVote**: (comment, user, value ∈ {1, -1})

---

## 주요 엔드포인트

* **Auth (JWT)**

  * `POST /api/auth/jwt/create/`
    요청 예:

    ```json
    { "username": "관리자ID", "password": "암호" }
    ```
  * `POST /api/auth/jwt/refresh/`

    ```json
    { "refresh": "<refresh_token>" }
    ```

* **Galleries**

  * `GET /api/galleries/`
  * `POST /api/galleries/` (관리/운영 계정으로 생성 권장)

* **Posts**

  * `GET /api/posts/?gallery={slug}`
  * `POST /api/posts/` (익명: nickname 사용 / 인증 시 author 자동)
  * `POST /api/posts/{id}/view/`  → 조회수 +1
  * `POST /api/posts/{id}/vote/`
    요청 예:

    ```json
    { "value": 1 }   // 또는 -1
    ```

* **Comments**

  * `GET /api/comments/?post={id}`
  * `POST /api/comments/`
  * `POST /api/comments/{id}/vote/`

    ```json
    { "value": 1 }   // 또는 -1
    ```

* **Hot**

  * `GET /api/hot/` (최근 48시간 내 추천 기준 정렬)

### 간단 cURL 예시

```powershell
# 로그인 (access/refresh 토큰 발급)
curl -X POST http://127.0.0.1:8000/api/auth/jwt/create/ `
  -H "Content-Type: application/json" `
  -d "{""username"":""admin"",""password"":""pass""}"

# 갤러리 생성 (토큰 필요)
curl -X POST http://127.0.0.1:8000/api/galleries/ `
  -H "Authorization: Bearer <ACCESS_TOKEN>" `
  -H "Content-Type: application/json" `
  -d "{""slug"":""baseball"",""title"":""야구 갤러리""}"

# 글 작성 (익명 닉네임)
curl -X POST http://127.0.0.1:8000/api/posts/ `
  -H "Content-Type: application/json" `
  -d "{""gallery"":""baseball"",""title"":""첫 글"",""content"":""안녕"",""nickname"":""ㅇㅇ""}"

# 댓글 작성
curl -X POST http://127.0.0.1:8000/api/comments/ `
  -H "Content-Type: application/json" `
  -d "{""post"":1,""content"":""댓글"",""nickname"":""ㅇㅇ""}"
```

---

## ERD(관계도) 생성 가이드 (선택)

### 방법 1) django-extensions + Graphviz (권장)

```powershell
uv pip install django-extensions graphviz
# (윈도우 이미지 렌더가 필요하면)
uv pip install pygraphviz  # 또는 pydotplus
```

`dcclone/settings/base.py`:

```python
INSTALLED_APPS += ['django_extensions']
```

생성:

```powershell
# 바로 PNG
uv run python manage.py graph_models -a -o erd.png

# 또는 dot 파일로 내보낸 뒤 수동 렌더
uv run python manage.py graph_models -a --dot -o erd.dot
dot -Tsvg erd.dot -Gfontname="Arial" -Nfontname="Arial" -Efontname="Arial" -o erd.svg
```

> **폰트 경고(Pango WARNING)**가 뜬다면 Windows에 **Roboto** 설치 또는 위처럼 `-G/-N/-E fontname`으로 Arial/DejaVu Sans를 강제 지정하세요.

---

## 파일 트리(요약)

```
dcinside-clone-backend-dc/
├─ dcclone/
│  ├─ settings/
│  ├─ urls.py
│  ├─ asgi.py, wsgi.py
├─ core/
│  ├─ models.py        # Gallery, Post, Comment, Vote
│  ├─ serializers.py
│  ├─ views.py
│  ├─ admin.py
├─ users/
│  ├─ models.py        # Custom User
│  ├─ admin.py
├─ pyproject.toml      # uv 관리
├─ docker-compose.yml  # db(web)
├─ Dockerfile
├─ .env.example
└─ manage.py
```

---

## 자주 막히는 포인트 & 해결법

1. **DB 연결 실패** (`OperationalError: connection refused`)

* 원인: Postgres 컨테이너가 아직 준비 전 / 포트 충돌.
* 확인:

  ```powershell
  docker ps
  docker logs <컨테이너이름>
  Test-NetConnection localhost -Port 5432
  ```
* 조치: 컨테이너 재시작, 포트 사용 중 프로세스 종료, 또는 `DATABASE_URL` 재확인.

2. **`psycopg` 관련 오류**

* 대부분 `uv sync` 미실행 또는 venv 미적용.
* 조치: 가상환경 다시 활성화 후 `uv sync`.

3. **PowerShell 실행 정책 오류로 venv 활성화 실패**

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
. .\.venv\Scripts\Activate.ps1
```

4. **마이그레이션 누락으로 테이블 없음**

```powershell
uv run python manage.py makemigrations users core
uv run python manage.py migrate
```

5. **포트 8000 사용 중**

```powershell
uv run python manage.py runserver 0.0.0.0:8001
```

6. **JWT 401**

* 토큰 필요. `/api/auth/jwt/create/`로 `access` 발급 →
  `Authorization: Bearer <access>` 헤더에 넣어 호출.

7. **Docker 데몬 연결 오류** (윈도우)

* Docker Desktop 실행/업데이트, **Linux containers** 모드, `docker context use desktop-linux`, WSL 통합 확인.

---

## 운영/확장 팁

* **익명 방지/제한**: IP 해시 저장, 글 비밀번호, 1일 글/댓글 제한, 캡차 등
* **추천 악용 방지**: 동일 IP/세션/토큰/디바이스 지표로 rate-limit, 투표 이력 로깅
* **조회수**: IP+UA+시간대 기준 중복 방지, 캐시(Redis)로 누적
* **검색 최적화**: Post.title/content 인덱스, 필요 시 Elastic/Lunr
* **정적/미디어**: S3 등 외부 스토리지 + CDN
* **배포**: gunicorn/uvicorn + nginx, `DEBUG=False`, `ALLOWED_HOSTS`/보안 헤더 설정

---

필요하면 이 README를 프로젝트에 바로 반영해줄 수도 있어. 추가로 “말머리/힛갤/블라인드/신고/차단” 같은 디시 특화 기능도 순차적으로 붙여줄게. 어떤 것부터 넣을지 말해줘!
