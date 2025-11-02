import requests  # HTTP 요청을 보내기 위한 라이브러리
from bs4 import BeautifulSoup  # HTML을 파싱하기 위한 라이브러리
import os  # 디렉토리 생성을 위한 라이브러리
import time  # 서버에 부담을 주지 않도록 잠시 대기하기 위한 라이브러리
from urllib.parse import urljoin, urlparse, parse_qs  # URL을 조합하고 분석하기 위한 라이브러리

# --- 설정 ---

# 크롤링할 기본 URL (게시판 목록 페이지 기준)
BASE_BOARD_URL = "http://www.kica0472.or.kr/php/board.php"

# 크롤링 대상 게시판 'board' 목록
# 사용자께서 알려주신 목록
BOARD_TABLES = [
    "intranet",
    "intranet2",
    "tech",
    "kicasosic",
    "kicanews",
    "dispute",
    "advertise"
]

# 데이터를 저장할 기본 디렉토리
SAVE_DIR_BASE = "kica_crawl_output"

# 요청 시 사용할 헤더 (봇이 아닌 브라우저처럼 보이게 하기 위함)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 요청 사이의 대기 시간 (초) - 서버 보호
POLITE_DELAY = 0.5

# --- 크롤러 함수 ---

def fetch_page(url):
    """지정된 URL의 웹페이지를 가져옵니다."""
    try:
        response = requests.get(url, headers=HEADERS)
        # HTTP 에러가 발생하면 예외를 발생시킵니다.
        response.raise_for_status()
        # UTF-8로 인코딩 강제 (사이트의 <meta> 태그 기준)
        response.encoding = 'utf-8'
        return response
    except requests.exceptions.RequestException as e:
        print(f"  [Error] 페이지를 가져오는 중 오류 발생 ({url}): {e}")
        return None


def save_post(response, save_path):
    """게시글 응답(response) 객체의 원본 내용을 파일로 저장합니다."""
    try:
        # .content를 사용하여 원본 바이트를 그대로 저장합니다.
        # 브라우저가 HTML 내의 charset을 보고 올바르게 렌더링할 것입니다.
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"  [Success] 게시글 저장 완료: {save_path}")
    except IOError as e:
        print(f"  [Error] 파일 저장 중 오류 발생 ({save_path}): {e}")


def crawl_board(board_name):
    """특정 게시판의 모든 게시글을 크롤링합니다."""
    print(f"\n--- '{board_name}' 게시판 크롤링 시작 ---")
    
    # 게시판별로 하위 디렉토리 생성
    save_dir = os.path.join(SAVE_DIR_BASE, board_name)
    os.makedirs(save_dir, exist_ok=True)
    
    page = 1
    while True:
        # 현재 페이지 목록 URL (새로운 구조에 맞게 수정)
        board_list_url = f"{BASE_BOARD_URL}?board={board_name}&page={page}"
        print(f"\n- {page} 페이지 목록을 확인합니다: {board_list_url}")
        
        response = fetch_page(board_list_url)
        if response is None:
            print(f"  ! {page} 페이지를 가져올 수 없어 {board_name} 게시판을 중단합니다.")
            break
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 게시글 링크 선택 (새로운 URL 구조에 맞게 수정)
        # 'command=body'와 'no=' 파라미터를 포함하는 링크를 찾습니다.
        # 게시판 이름(board=)도 일치하는지 확인하여 다른 게시판 링크가 섞이는 것을 방지합니다.
        post_links = soup.select(f"a[href*='board={board_name}'][href*='command=body'][href*='no=']")
        
        # 중복 링크 제거 (간혹 목록에 같은 링크가 여러 번 나올 수 있음)
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
            try:
                # 상대 경로를 절대 경로로 변환
                post_relative_url = link.get('href')
                post_url = urljoin(board_list_url, post_relative_url)
                
                # URL에서 no (게시글 고유 ID)를 추출하여 파일명으로 사용
                parsed_url = urlparse(post_url)
                query_params = parse_qs(parsed_url.query)
                post_id = query_params.get('no', [None])[0]
                
                if not post_id:
                    print(f"  [Warning] 'no' 파라미터를 찾을 수 없습니다: {post_url}")
                    continue
                    
                file_name = f"{post_id}.html"
                save_path = os.path.join(save_dir, file_name)
                
                # (옵션) 이미 파일이 존재하면 건너뛰기
                # if os.path.exists(save_path):
                #     print(f"  [Skip] 이미 파일이 존재합니다: {save_path}")
                #     continue

                print(f"  > 게시글 크롤링 시도: {post_url}")
                post_response = fetch_page(post_url)
                
                if post_response:
                    save_post(post_response, save_path)
                    
                # 서버에 부담을 주지 않도록 잠시 대기
                time.sleep(POLITE_DELAY)
                
            except Exception as e:
                print(f"  [Error] 개별 게시글 처리 중 오류 발생: {e}")
                
        # 다음 페이지로 이동
        page += 1

def main():
    """메인 실행 함수"""
    print(f"--- KICA 웹사이트 크롤링 시작 ---")
    print(f"저장 위치: {os.path.abspath(SAVE_DIR_BASE)}")
    
    # 모든 게시판에 대해 크롤링 실행
    for table_name in BOARD_TABLES:
        crawl_board(table_name)
        
    print("\n--- 모든 게시판 크롤링 완료 ---")

if __name__ == "__main__":
    main()

