import requests
from bs4 import BeautifulSoup

# 認証情報
LOGIN_URL = "https://admin-z2ijkdqr.pokerroom634.com/admin/login"
TARGET_URL = "https://admin-z2ijkdqr.pokerroom634.com/admin/game/list?tab=ring"
USERNAME = "pokerroom634staff1@gmail.com"
PASSWORD = "uW5XZF.i"

def main():
    # セッション開始
    session = requests.Session()
    
    # ログイン処理
    # ログインページをGETしてCSRFトークンを取得
    login_page = session.get(LOGIN_URL)
    login_page.raise_for_status()
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find('input', {'name': '_csrf'}).get('value')

    # ログイン用データの準備（OAuth2.0パラメータ追加）
    login_data = {
        "email": USERNAME,
        "password": PASSWORD,
        "_csrf": csrf_token,
        "client_id": "3v1i5i8d6jpdor3lmhsqs1lcfq",
        "redirect_uri": "https://admin-z2ijkdqr.pokerroom634.com/oauth2/idpresponse",
        "response_type": "code",
        "scope": "openid",
        "state": login_page.url.split("state=")[1].split("&")[0]
    }
    
    try:
        # ログイン実行（リダイレクトを許可）
        response = session.post(LOGIN_URL, data=login_data, allow_redirects=True)
        response.raise_for_status()
        
        # デバッグ情報出力
        print(f"\n=== ログイン応答情報 ===")
        print(f"最終ステータスコード: {response.status_code}")
        print(f"リダイレクト履歴: {len(response.history)}回")
        print("最終URL:", response.url)
        print("セッションクッキー:", session.cookies.get_dict())
        print("レスポンス本文（一部）:", response.text[:500])
        print("======================\n")
        
        # ログイン状態の確認
        if response.status_code != 200:
            raise Exception(f"ログイン失敗: HTTPステータス {response.status_code}")
            
        # ターゲットページ取得（ユーザー提供のヘッダーを使用）
        headers = {
            'authority': 'admin-z2ijkdqr.pokerroom634.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
            'referer': 'https://admin-z2ijkdqr.pokerroom634.com/admin/home',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
        
        # ユーザー提供の正しいURLを使用
        target_response = session.get(
            "https://admin-z2ijkdqr.pokerroom634.com/admin/season/list",
            headers=headers
        )
        target_response.raise_for_status()
        
        # HTML解析
        soup = BeautifulSoup(target_response.text, 'html.parser')
        
        # デバッグ用HTML保存（絶対パス指定）
        debug_path = 'c:/code/physics_simulation/debug_page.html'
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(f"HTTP Status: {target_response.status_code}\n")
            f.write(soup.prettify())
        print(f"デバッグファイルを保存しました: {debug_path}")
        
        # データ抽出（テーブル構造に合わせて修正）
        # テーブル検索方法を階層的に改善
        table_container = (
            soup.select_one('div[role="grid"]') or  # ロール属性で検索
            soup.find('div', {'data-testid': 'game-table'}) or  # テスト用属性
            soup.select_one('div.MuiBox-root > table')  # 階層構造で検索
        )
        if not table_container:
            # デバッグ用にHTML構造をダンプ
            container_debug_path = 'c:/code/physics_simulation/container_debug.html'
            with open(container_debug_path, 'w', encoding='utf-8') as f:
                f.write("=== 検索対象コンテナ ===\n")
                f.write(str(soup.find_all('div', class_='MuiBox-root')))
                f.write("\n\n=== 全体構造 ===")
                f.write(soup.prettify())
            raise Exception(f"テーブルコンテナが見つかりませんでした。デバッグファイルを確認してください: {container_debug_path}")
            
        # テーブル要素を取得
        table = table_container.find('table', {'class': 'MuiTable-root'})
        if not table:
            raise Exception("テーブル要素が見つかりませんでした")

        # ヘッダー抽出（th要素から直接テキスト取得）
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        # 行データ抽出（Material-UIテーブル構造に対応）
        tbody = table.find('tbody', {'class': 'MuiTableBody-root'})
        if not tbody:
            raise Exception("テーブルボディが見つかりませんでした")
            
        rows = []
        for row in tbody.find_all('tr', {'class': 'MuiTableRow-root'}):
            # 各セルから直接div要素を検索
            cells = [
                cell.find('div', {'class': 'MuiBox-root'}).get_text(strip=True) 
                if cell.find('div', {'class': 'MuiBox-root'}) 
                else '' 
                for cell in row.find_all('td', {'class': 'MuiTableCell-root'})
            ]
            # 空行を除外
            if any(cells):
                rows.append(cells)
                
        # 結果表示
        print("スクレイピング結果:")
        print("ヘッダー:", headers)
        for i, row in enumerate(rows, 1):
            print(f"行{i}: {row}")
            
    except Exception as e:
        print(f"\n=== エラー詳細 ===")
        print(f"エラータイプ: {type(e).__name__}")
        print(f"エラーメッセージ: {str(e)}")
        print(f"発生ファイル: {__file__}")
        print(f"発生行数: {e.__traceback__.tb_lineno}")
        print("======================\n")

if __name__ == "__main__":
    main()
