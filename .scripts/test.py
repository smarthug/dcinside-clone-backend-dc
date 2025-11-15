import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urljoin, urlparse, parse_qs
import re
from datetime import datetime
from pathlib import PurePath
import blake3
import psycopg2  # DB 연결을 위해 추가
from psycopg2.extras import DictCursor  # 결과를 딕셔너리 형태로 받기 위해 추가

# --- 설정 ---

# 크롤링할 기본 URL (게시판 목록 페이지 기준)
BASE_BOARD_URL = "http://www.kica0472.or.kr/php/board.php"

# 크롤링 대상 게시판 'board' 목록
BOARD_TABLES = [
    # "intranet", "intranet2", "kicasosic", "kicanews",
    # "dispute", "advertise", "datab",
    "kicanews"
]

BOARD_TO_GALLERY_SLUG_MAP = {
    "kicasosic": "news_kica",
    "kicanews": "news_related",
}

# 데이터를 저장할 기본 디렉토리 (HTML 백업용으로 유지)
SAVE_DIR_BASE = ".save_data"
# 미디어 파일(첨부파일)을 저장할 디렉토리
MEDIA_DIR_BASE = ".media"

# DB 연결 정보 (Django의 .env 파일 활용)
# 예: "postgres://postgres:postgres@localhost:5432/dcclone"
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgres://postgres:postgres@localhost:5432/dcclone")

# 요청 시 사용할 헤더
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 쿠키 정보
COOKIES = {
    "LONGaaA": os.getenv("KICA_LONGaaA", ""),
    "PHPSESSID": os.getenv("KICA_PHPSESSID", "")
}

# 요청 사이의 대기 시간 (초)
POLITE_DELAY = 0.5

# --- 도우미 함수 ---


def compute_hash(content) -> str:
    return blake3.blake3(content).hexdigest()


def get_filename_from_content(content, original_filename):
    file_ext = PurePath(original_filename).suffix
    file_root = compute_hash(content=content)
    path = PurePath(
        "{0}/{1}".format(file_root[:2], file_root[2:])).with_suffix(file_ext)
    return str(path).replace("\\", "/")


def get_detail_from_tr(soup, header_text):
    header_td = soup.find('td', class_='b_detail_left',
                          string=re.compile(header_text))
    if header_td and header_td.find_next_sibling('td'):
        return header_td.find_next_sibling('td').get_text(strip=True)
    return None


def download_file(conn, file_url, original_filename, board_name, post_created_at):
    """주어진 URL에서 파일을 다운로드하고, DB에 파일 정보를 저장합니다."""
    try:
        print(f"    > 첨부파일 다운로드 시도: {file_url}")
        response = requests.get(file_url, headers=HEADERS,
                                cookies=COOKIES, stream=True)
        response.raise_for_status()

        file_content = response.content
        django_path = get_filename_from_content(
            file_content, original_filename)
        full_save_path = os.path.join(MEDIA_DIR_BASE, django_path)
        save_dir = os.path.dirname(full_save_path)
        os.makedirs(save_dir, exist_ok=True)

        with open(full_save_path, 'wb') as f:
            f.write(file_content)
        print(
            f"    [Success] 파일 저장 완료: {full_save_path} (원본: {original_filename})")

        # --- DB에 파일 정보 저장 ---
        with conn.cursor() as cur:
            # 갤러리 ID 조회
            cur.execute(
                "SELECT id FROM core_gallery WHERE slug = %s", (BOARD_TO_GALLERY_SLUG_MAP[board_name],))
            gallery_record = cur.fetchone()
            if not gallery_record:
                print(
                    f"    [Error] DB에서 갤러리를 찾을 수 없습니다: {BOARD_TO_GALLERY_SLUG_MAP[board_name]}")
                return None, None, None
            gallery_id = gallery_record[0]

            # File 모델의 'file' 필드는 'private/' 접두사를 포함
            db_file_path = f"private/{django_path}"

            cur.execute(
                """
                INSERT INTO files_file (gallery_id, author_id, file, filename, created_at, is_deleted)
                VALUES (%s, 1, %s, %s, %s, false)
                ON CONFLICT DO NOTHING
                RETURNING id;
                """,
                (gallery_id, db_file_path, original_filename, post_created_at)
            )
            file_record = cur.fetchone()
            file_id = file_record[0] if file_record else None
        return django_path, original_filename, file_id

    except requests.exceptions.RequestException as e:
        print(f"    [Error] 파일 다운로드 중 오류 발생 ({file_url}): {e}")
    except Exception as e:
        print(f"    [Error] 파일 처리 중 오류 발생: {e}")
    return None, None, None

# --- 크롤러 함수 ---


def fetch_page(url, board_name=None):
    try:
        request_cookies = COOKIES
        if board_name == "kicanews":
            request_cookies = None
        response = requests.get(url, headers=HEADERS,
                                cookies=request_cookies, timeout=10)
        response.raise_for_status()
        response.encoding = "euc-kr"
        return response
    except requests.exceptions.RequestException as e:
        print(f"  [Error] 페이지를 가져오는 중 오류 발생 ({url}): {e}")
        return None


def parse_and_save_post(conn, post_response, board_name):
    """게시글 응답을 파싱하여 DB에 저장하고 첨부파일을 다운로드합니다."""
    post_url = post_response.url
    soup = BeautifulSoup(post_response.content.decode(
        'euc-kr', 'replace'), "html.parser")

    title = get_detail_from_tr(soup, '제목')
    nickname = get_detail_from_tr(soup, '작성자')
    created_at_str = get_detail_from_tr(soup, '작성일')
    is_notice = '[ 공지 ]' in title if title else False

    created_at_iso = None
    if created_at_str:
        try:
            cleaned_str = re.sub(r'\s*\([^)]*\)', '', created_at_str).strip()
            dt_obj = datetime.strptime(cleaned_str, '%Y-%m-%d %H:%M')
            created_at_iso = dt_obj.isoformat()
        except ValueError:
            print(f"  [Warning] 날짜 형식 변환 실패: {created_at_str}")

    content_body = soup.select_one("td[id^='bodytextID']")
    content = content_body.decode_contents() if content_body else ''

    attachments = []
    file_links = soup.find_all(
        'td', class_='b_detail_left', string=re.compile('파일첨부'))
    for file_link_header in file_links:
        file_link_data = file_link_header.find_next_sibling('td')
        if not file_link_data:
            continue
        onclick_attr = file_link_data.find('span', onclick=True)
        if not onclick_attr:
            continue

        match = re.search(r"OpenWin_smart\('([^']*)'", onclick_attr['onclick'])
        if match:
            relative_url = match.group(1)
            file_download_url = urljoin(post_url, relative_url)
            img_tag = file_link_data.find('img')
            original_name_from_tag = img_tag.next_sibling.strip(
            ) if img_tag and img_tag.next_sibling else onclick_attr.get_text(strip=True)
            if not original_name_from_tag:
                print(f"  [Warning] span 태그에서 파일명을 찾을 수 없습니다: {onclick_attr}")
                continue

            media_path, original_name, file_id = download_file(
                conn, file_download_url, original_name_from_tag, board_name, created_at_iso)
            if media_path and original_name and file_id:
                attachments.append(
                    {'path': media_path, 'name': original_name, 'id': file_id})

    # --- 대표 이미지 찾기 및 본문에 첨부파일 추가 ---
    representative_image_path = None
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif')

    if attachments:
        content += "\n\n--- 첨부파일 ---\n"
        for att in attachments:
            is_image = att['name'].lower().endswith(image_extensions)
            if is_image:
                content += f'<img src="/api/files/{att["id"]}/" alt="{att["name"]}" style="max-width:100%; height:auto;">\n'
            else:
                content += f'<a href="/api/files/{att["id"]}/">{att["name"]}</a>\n'

            if is_image and not representative_image_path:
                # Post.image 필드는 upload_to='posts/'
                representative_image_path = f'/api/files/{att["id"]}/'

    # --- DB에 게시글 저장 ---
    try:
        with conn.cursor() as cur:
            # 갤러리 ID 조회
            cur.execute(
                "SELECT id FROM core_gallery WHERE slug = %s", (BOARD_TO_GALLERY_SLUG_MAP[board_name],))
            gallery_record = cur.fetchone()
            if not gallery_record:
                print(
                    f"  [Error] DB에서 갤러리를 찾을 수 없습니다: {BOARD_TO_GALLERY_SLUG_MAP[board_name]}")
                conn.rollback()  # 현재 트랜잭션 롤백
                return
            gallery_id = gallery_record[0]

            # Post 모델에 맞게 데이터 준비
            # author_id는 익명 게시글이므로 NULL, recommend/views 등은 기본값 0으로 설정
            cur.execute(
                """
                INSERT INTO core_post (
                    gallery_id, title, content, nickname, created_at, updated_at, is_notice, image,
                    author_id, recommend, views, is_delete, is_pending, external_link
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 0, 0, false, false, NULL)
                ON CONFLICT DO NOTHING;
                """,
                (gallery_id, title, content, nickname, created_at_iso,
                 created_at_iso, is_notice, representative_image_path)
            )
        conn.commit()  # 게시글과 모든 첨부파일 정보를 하나의 트랜잭션으로 커밋
        print(f"  [Success] DB에 게시글 저장 완료: {title}")
    except Exception as e:
        print(f"  [Error] DB에 게시글 저장 중 오류 발생: {e}")
        conn.rollback()  # 오류 발생 시 롤백


def crawl_kicanews_board(conn, board_name):
    """'kicanews' 게시판을 크롤링하여 DB에 저장합니다. (외부 링크 방식)"""
    print(f"\n--- '{board_name}' 게시판 크롤링 시작 (외부 링크 방식) ---")

    # --- 테스트용 설정: 처리할 게시글 수 제한 ---
    post_process_limit = 3
    processed_count = 0

    page = 1
    while True:
        board_list_url = f"{BASE_BOARD_URL}?board={board_name}&page={page}"
        print(f"\n- {page} 페이지 목록을 확인합니다: {board_list_url}")

        response = fetch_page(board_list_url, board_name=board_name)
        if response is None:
            print(f"  ! {page} 페이지를 가져올 수 없어 {board_name} 게시판을 중단합니다.")
            break

        soup = BeautifulSoup(response.content.decode(
            'euc-kr', 'replace'), "html.parser")
        post_divs = soup.select("div.report_list")

        if not post_divs:
            print(f"- {page} 페이지에 게시글이 없습니다. '{board_name}' 게시판 크롤링 완료.")
            break

        print(f"- {page} 페이지에서 {len(post_divs)}개의 게시글 링크를 찾았습니다.")

        for post_div in post_divs:
            # 테스트용 게시글 수 제한 확인
            if processed_count >= post_process_limit:
                print(f"\n[Info] 테스트용 게시글 처리 제한({post_process_limit}개)에 도달하여 크롤링을 중단합니다.")
                break

            onclick_attr = post_div.get('onclick', '')
            match = re.search(r"window\.open\('([^']*)'\)", onclick_attr)
            if not match:
                continue

            external_link = match.group(1)
            title = post_div.select_one(".news_board_title").get_text(
                strip=True) if post_div.select_one(".news_board_title") else "제목 없음"
            source = post_div.select_one(".news_board_data2").get_text(strip=True).replace(
                "출처 :", "").strip() if post_div.select_one(".news_board_data2") else "출처 없음"

            # --- 대표 이미지 처리 ---
            representative_image_path = None
            img_tag = post_div.select_one(".news_album img.list_thumbnail")
            if img_tag and img_tag.get('src') and 'imgblank.gif' not in img_tag['src']:
                img_relative_url = img_tag['src']
                img_download_url = urljoin(board_list_url, img_relative_url)
                original_filename = os.path.basename(
                    urlparse(img_download_url).path)

                # kicanews는 작성일 정보가 없으므로, 크롤링 시점을 사용
                now_iso = datetime.now().isoformat()

                _, _, file_id = download_file(
                    conn, img_download_url, original_filename, board_name, now_iso
                )
                if file_id:
                    representative_image_path = f"/api/files/{file_id}/"
                    print(
                        f"    [Success] 대표 이미지 설정 완료: {representative_image_path}")
                else:
                    print(f"    [Warning] 대표 이미지 다운로드 또는 DB 저장 실패.")

            # kicanews는 게시글 상세 페이지가 없으므로, 목록에서 바로 DB에 저장
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM core_gallery WHERE slug = %s",
                                (BOARD_TO_GALLERY_SLUG_MAP[board_name],))
                    gallery_id = cur.fetchone()[0]

                    # 작성일 정보가 없으므로 크롤링 시점을 사용
                    now_iso = datetime.now().isoformat()

                    cur.execute(
                        """
                        INSERT INTO core_post (
                            gallery_id, title, content, nickname, created_at, updated_at, is_notice, image,
                            author_id, recommend, views, is_delete, is_pending, external_link
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, false, %s, 1, 0, 0, false, false, %s)
                        ON CONFLICT DO NOTHING;
                        """,
                        (gallery_id, title, f"외부 링크: {external_link}", source,
                         now_iso, now_iso, representative_image_path, external_link)
                    )
                conn.commit()
                print(f"  [Success] DB에 외부 링크 게시글 저장 완료: {title}")

                processed_count += 1  # 처리된 게시글 수 증가

            except Exception as e:
                print(f"  [Error] DB에 외부 링크 게시글 저장 중 오류 발생: {e}")
                conn.rollback()

            time.sleep(POLITE_DELAY)

        # 루프 종료 조건 확인
        if processed_count >= post_process_limit:
            break

        page += 1


def crawl_board(conn, board_name):
    """특정 게시판의 모든 게시글을 크롤링하여 DB에 저장합니다."""
    print(f"\n--- '{board_name}' 게시판 크롤링 시작 ---")

    # 갤러리가 DB에 존재하는지 확인
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM core_gallery WHERE slug = %s",
                    (BOARD_TO_GALLERY_SLUG_MAP[board_name],))
        if cur.fetchone() is None:
            print(f"[Critical] '{board_name}' 갤러리가 DB에 존재하지 않습니다. 건너뜁니다.")
            print(f"         먼저 Django Admin이나 API를 통해 갤러리를 생성해주세요.")
            return

    # kicanews는 처리 방식이 다르므로 분기
    if board_name == "kicanews":
        crawl_kicanews_board(conn, board_name)
        return

    # --- 테스트용 설정: 처리할 게시글 수 제한 ---
    post_process_limit = 3
    processed_count = 0

    page = 1
    while True:
        board_list_url = f"{BASE_BOARD_URL}?board={board_name}&page={page}"
        print(f"\n- {page} 페이지 목록을 확인합니다: {board_list_url}")

        response = fetch_page(board_list_url, board_name=board_name)
        if response is None:
            print(f"  ! {page} 페이지를 가져올 수 없어 {board_name} 게시판을 중단합니다.")
            break

        soup = BeautifulSoup(response.content.decode(
            'euc-kr', 'replace'), "html.parser")
        post_links = soup.select(
            f"a[href*='board={board_name}'][href*='command=body'][href*='no=']")

        unique_links = []
        seen_hrefs = set()
        for link in post_links:
            href = link.get('href')
            if href not in seen_hrefs:
                seen_hrefs.add(href)
                unique_links.append(link)
        post_links = unique_links

        if not post_links:
            print(f"- {page} 페이지에 게시글이 없습니다. '{board_name}' 게시판 크롤링 완료.")
            break

        print(f"- {page} 페이지에서 {len(post_links)}개의 게시글 링크를 찾았습니다.")

        for link in post_links:
            # 테스트용 게시글 수 제한 확인
            if processed_count >= post_process_limit:
                print(f"\n[Info] 테스트용 게시글 처리 제한({post_process_limit}개)에 도달하여 크롤링을 중단합니다.")
                break

            try:
                post_relative_url = link.get('href')
                post_url = urljoin(board_list_url, post_relative_url)

                print(f"  > 게시글 처리 시도: {post_url}")
                post_response = fetch_page(post_url, board_name=board_name)

                if post_response:
                    parse_and_save_post(conn, post_response, board_name)
                    processed_count += 1 # 처리된 게시글 수 증가

                time.sleep(POLITE_DELAY)

            except Exception as e:
                print(f"  [Error] 개별 게시글 처리 중 오류 발생: {e}")

        # 루프 종료 조건 확인
        if processed_count >= post_process_limit:
            break

        page += 1


def main():
    """메인 실행 함수"""
    print("--- KICA 웹사이트 크롤링 시작 ---")
    print(f"미디어 저장 위치: {os.path.abspath(MEDIA_DIR_BASE)}")

    conn = None
    try:
        # 데이터베이스 연결
        print(f"데이터베이스에 연결합니다...")
        conn = psycopg2.connect(DATABASE_URL)
        print("데이터베이스 연결 성공!")

        # 모든 게시판에 대해 크롤링 실행
        for table_name in BOARD_TABLES:
            crawl_board(conn, table_name)

    except psycopg2.OperationalError as e:
        print(f"[Critical] 데이터베이스 연결 실패: {e}")
        print("DB가 실행 중인지, DATABASE_URL 환경 변수가 올바른지 확인하세요.")
    except Exception as e:
        print(f"[Critical] 예기치 않은 오류 발생: {e}")
    finally:
        if conn:
            conn.close()
            print("\n데이터베이스 연결을 닫았습니다.")

    print("\n--- 모든 게시판 크롤링 완료 ---")


if __name__ == "__main__":
    main()
