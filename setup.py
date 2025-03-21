import subprocess
import sys
import os

def install_requirements():
    """必要なパッケージをインストールする関数"""
    print("必要なパッケージをインストールしています...")
    
    # 必要なパッケージのリスト
    packages = [
        "pygame",
        "numpy<2.0.0",  # OpenCVとの互換性のためNumPy 1.xを使用
        "scipy",
        "opencv-python"
    ]
    
    # pipを使ってインストール
    for package in packages:
        print(f"{package}をインストールしています...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("全てのパッケージのインストールが完了しました！")

def setup_environment():
    """環境を準備する関数"""
    print("物理演算シミュレーションの環境をセットアップしています...")
    
    # 必要なフォルダ構造を作成
    folders = [
        "physics_simulation",
        "physics_simulation/assets",
        "physics_simulation/assets/sounds",
        "physics_simulation/assets/bgm",
        "physics_simulation/videos"
    ]
    
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"{folder}フォルダを作成しました。")
    
    print("環境のセットアップが完了しました！")

def generate_sounds():
    """サウンドファイルを生成する関数"""
    print("サウンドファイルを生成しています...")
    
    try:
        # generate_sounds.pyを実行
        subprocess.check_call([sys.executable, "physics_simulation/generate_sounds.py"])
        print("サウンドファイルの生成が完了しました！")
    except Exception as e:
        print(f"サウンドファイルの生成中にエラーが発生しました: {e}")
        print("主要な機能は引き続き利用できますが、音声は再生されません。")

def main():
    """メインの処理関数"""
    print("=== 物理演算シミュレーションのセットアップ ===")
    
    # 必要なパッケージのインストール
    install_requirements()
    
    # 環境のセットアップ
    setup_environment()
    
    # サウンドの生成
    generate_sounds()
    
    print("\n=== セットアップが完了しました ===")
    print("シミュレーションを起動するには、次のコマンドを実行してください:")
    print("python physics_simulation/main.py")
    
    # 自動的にシミュレーションを起動するか確認
    launch = input("\nシミュレーションを今すぐ起動しますか？ (y/n): ")
    if launch.lower() == 'y':
        print("シミュレーションを起動します...")
        subprocess.call([sys.executable, "physics_simulation/main.py"])

if __name__ == "__main__":
    main()
