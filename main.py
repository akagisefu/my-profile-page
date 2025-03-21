import pygame
import sys
import random
import math
import os
import time
from pygame import mixer

# 動画出力機能（オプション）
VIDEO_EXPORT_ENABLED = False
AUDIO_EXPORT_ENABLED = False

try:
    import cv2
    import numpy as np
    from datetime import datetime
    VIDEO_EXPORT_ENABLED = True
    print("動画エクスポート機能が有効です")
    
    # FFmpeg機能の確認
    try:
        import subprocess
        import tempfile
        import os
        import shutil
        AUDIO_EXPORT_ENABLED = True
        print("音声付き動画エクスポート機能が有効です")
    except ImportError:
        print("音声付き動画エクスポートができません。音声なしで出力します。")
except ImportError:
    print("OpenCVのインポートに失敗しました。動画出力機能は無効になります。")
    print("動画出力を有効にするには、NumPy 1.xとOpenCVをインストールしてください。")

# 定数
WIDTH, HEIGHT = 800, 800
# 動画出力用定数
RECORD_VIDEO = VIDEO_EXPORT_ENABLED  # OpenCVがインポートできた場合のみTrue
MAX_GAME_TIME = 120  # 最大ゲーム時間（秒）
WIN_DISPLAY_TIME = 5  # 勝利後の表示時間（秒）
VIDEO_FPS = 30  # 出力動画のFPS
BOX_SIZE = 700
BLOCK_SIZE = 30
FPS = 60
BACKGROUND_COLOR = (0, 0, 0)
BOX_COLOR = (50, 50, 50)
GOAL_COLOR = (255, 215, 0)  # ゴールは金色
MOVING_WALL_COLOR = (255, 255, 255)  # 迫ってくる壁は白色
WALL_START_TIME = 5  # 5秒後に壁が動き始める
WALL_MOVE_DURATION = 25  # 壁が動く時間（秒）

# ファイルパス定数
# プロジェクトのルートディレクトリを基準とした相対パス
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))  # 現在のファイルのディレクトリ
SOUND_DIR = os.path.join(ROOT_DIR, "assets", "sounds")
BGM_DIR = os.path.join(ROOT_DIR, "assets", "bgm")
VIDEO_DIR = os.path.join(ROOT_DIR, "videos")
BGM_FILE = os.path.join(BGM_DIR, "famipop3.mp3")
COLLISION_SOUND_FILE = os.path.join(SOUND_DIR, "collision.wav")
GOAL_SOUND_FILE = os.path.join(SOUND_DIR, "goal.wav")

# ブロックの色（拡張可能）
BLOCK_COLORS = [
    (255, 0, 0),    # 赤
    (0, 255, 0),    # 緑
    (0, 0, 255),    # 青
    (255, 255, 0),  # 黄
    (255, 0, 255),  # マゼンタ
    (0, 255, 255),  # シアン
    (255, 128, 0),  # オレンジ
    (128, 0, 255),  # 紫
    (255, 128, 128), # ピンク
    (128, 255, 128), # ライトグリーン
    (128, 128, 255), # ライトブルー
    (192, 192, 192), # シルバー
]

# 色の名前（表示用）
COLOR_NAMES = [
    "Red", "Green", "Blue", "Yellow", 
    "Magenta", "Cyan", "Orange", "Purple",
    "Pink", "Light Green", "Light Blue", "Silver"
]

# デフォルト設定
DEFAULT_BLOCK_COUNT = 4  # ブロック数は4個固定
DEFAULT_VIDEO_COUNT = 1  # デフォルトの動画生成数

# グローバル変数
pygame_initialized = False
screen = None
clock = None
collision_sound = None
goal_sound = None

class Block:
    def __init__(self, x, y, color, index):
        self.x = x
        self.y = y
        self.size = BLOCK_SIZE
        self.color = color
        self.index = index
        self.speed = 3  # 基本速度
        # 斜め4方向のみに移動（ランダムな初期方向）
        angle = random.choice([45, 135, 225, 315])
        self.dx = self.speed * math.cos(math.radians(angle))
        self.dy = self.speed * math.sin(math.radians(angle))
        self.reached_goal = False
        self.rect = pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)
    
    def update(self, box_rect, goal_rect, blocks=None, moving_wall_y=None):
        # 前の位置を保存
        old_x, old_y = self.x, self.y
        
        # 位置の更新
        self.x += self.dx
        self.y += self.dy
        
        # 矩形の更新
        self.rect = pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)
        
        # 壁との衝突判定と反射
        collision_occurred = False
        
        # 左の壁
        if self.x - self.size//2 < box_rect.left:
            self.x = box_rect.left + self.size//2
            self.dx = abs(self.dx)  # 右向きに反射
            collision_occurred = True
        
        # 右の壁
        elif self.x + self.size//2 > box_rect.right:
            self.x = box_rect.right - self.size//2
            self.dx = -abs(self.dx)  # 左向きに反射
            collision_occurred = True
        
        # 上の壁（移動壁対応）
        if moving_wall_y is not None:
            if self.y - self.size//2 < moving_wall_y:
                self.y = moving_wall_y + self.size//2
                self.dy = abs(self.dy)  # 下向きに反射
                collision_occurred = True
        elif self.y - self.size//2 < box_rect.top:
            self.y = box_rect.top + self.size//2
            self.dy = abs(self.dy)  # 下向きに反射
            collision_occurred = True
        
        # 下の壁
        if self.y + self.size//2 > box_rect.bottom:
            self.y = box_rect.bottom - self.size//2
            self.dy = -abs(self.dy)  # 上向きに反射
            collision_occurred = True
        
        # 壁との衝突時に音を鳴らす
        global collision_sound
        if collision_occurred and collision_sound:
            collision_sound.play()
        
        # ブロック同士の衝突判定
        if blocks:
            for other in blocks:
                if other is not self and self.rect.colliderect(other.rect):
                    # 衝突が検出された場合、前の位置に戻す
                    self.x, self.y = old_x, old_y
                    self.rect = pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)
                    
                    # 衝突方向を判定して適切に反射
                    dx = self.x - other.x
                    dy = self.y - other.y
                    
                    # 衝突角度に基づいて反射
                    if abs(dx) > abs(dy):
                        # 左右方向の衝突
                        self.dx = math.copysign(abs(self.dx), dx)  # dxの符号を保持
                    else:
                        # 上下方向の衝突
                        self.dy = math.copysign(abs(self.dy), dy)  # dyの符号を保持
                    
                    # 衝突後の新しい位置に更新（少し移動して重ならないようにする）
                    self.x += self.dx * 0.5
                    self.y += self.dy * 0.5
                    self.rect = pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)
                    
                    if collision_sound:
                        collision_sound.play()
                    break
        
        # ゴールとの衝突判定
        global goal_sound
        if self.rect.colliderect(goal_rect) and not self.reached_goal:
            self.reached_goal = True
            if goal_sound:
                goal_sound.play()
            return True
        
        return False
    
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, 
                         (self.x - self.size//2, self.y - self.size//2, self.size, self.size))

def initialize_pygame():
    """Pygameの初期化を行う関数"""
    global pygame_initialized, screen, clock, collision_sound, goal_sound
    
    if not pygame_initialized:
        pygame.init()
        mixer.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("物理演算シミュレーション")
        clock = pygame.time.Clock()
        
        # サウンドの初期化
        if os.path.exists(BGM_FILE):
            mixer.music.load(BGM_FILE)
            mixer.music.set_volume(0.5)
            mixer.music.play(-1)  # -1はループ再生
        else:
            print(f"BGM {BGM_FILE} が見つかりません")
        
        # 効果音の初期化
        collision_sound = pygame.mixer.Sound(COLLISION_SOUND_FILE) if os.path.exists(COLLISION_SOUND_FILE) else None
        goal_sound = pygame.mixer.Sound(GOAL_SOUND_FILE) if os.path.exists(GOAL_SOUND_FILE) else None
        
        pygame_initialized = True

def main(record=RECORD_VIDEO, block_count=DEFAULT_BLOCK_COUNT):
    """メインゲームループ"""
    global screen, clock
    
    # Pygameの初期化
    initialize_pygame()
    
    # OpenCVがインポートできなかった場合は強制的に記録をオフに
    if not VIDEO_EXPORT_ENABLED:
        record = False
    
    # 箱の設定
    margin = (WIDTH - BOX_SIZE) // 2
    box_rect = pygame.Rect(margin, margin, BOX_SIZE, BOX_SIZE)
    
    # 動画出力の設定
    frames = []
    video_filename = None
    
    if record:
        try:
            # 現在時刻をファイル名に含める
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"{VIDEO_DIR}/simulation_{timestamp}.mp4"
            os.makedirs(VIDEO_DIR, exist_ok=True)
        except Exception as e:
            print(f"動画設定エラー: {e}")
            record = False
    
    # ゴールの設定（底部の中央）
    goal_width = 60
    goal_height = 20
    goal_rect = pygame.Rect(WIDTH//2 - goal_width//2, margin + BOX_SIZE - goal_height, goal_width, goal_height)
    
    # ブロック数の調整（1～12個まで）
    block_count = max(1, min(block_count, len(BLOCK_COLORS)))
    
    # ブロックの初期化
    blocks = []
    for i in range(block_count):
        # ブロックの位置をランダムに配置（箱の内側）
        x = random.randint(margin + 50, margin + BOX_SIZE - 50)
        y = random.randint(margin + 50, margin + BOX_SIZE - 50)
        blocks.append(Block(x, y, BLOCK_COLORS[i], i))
    
    # ゲームループ
    winner = None
    running = True
    game_start_time = time.time()
    win_time = None
    
    # 壁の移動用の変数
    start_time = pygame.time.get_ticks()
    wall_started = False
    moving_wall_y = None  # 移動する壁のY座標
    
    while running:
        # 現在時間の取得
        current_time = pygame.time.get_ticks()
        elapsed_seconds = (current_time - start_time) / 1000  # ミリ秒から秒に変換
        
        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # リセット
                    return main()
        
        # 画面クリア
        screen.fill(BACKGROUND_COLOR)
        
        # 移動する壁の処理（5秒後に開始）
        if elapsed_seconds >= WALL_START_TIME and not wall_started:
            wall_started = True
            wall_start_time = current_time
        
        if wall_started:
            wall_elapsed = (current_time - wall_start_time) / 1000  # 壁が動き始めてからの時間
            
            if wall_elapsed <= WALL_MOVE_DURATION:
                # 壁の位置を計算（上から下へ）
                progress = wall_elapsed / WALL_MOVE_DURATION  # 0～1の進行度
                moving_wall_y = margin + (BOX_SIZE * progress)
                
                # 移動する壁の描画
                pygame.draw.line(screen, MOVING_WALL_COLOR, 
                               (margin, moving_wall_y), 
                               (margin + BOX_SIZE, moving_wall_y), 3)
        
        # 通常の壁の描画（移動壁がある場合は上の壁は描画しない）
        if not wall_started or moving_wall_y is None:
            pygame.draw.rect(screen, BOX_COLOR, box_rect, 2)
        else:
            # 左、右、下の壁のみ描画
            pygame.draw.line(screen, BOX_COLOR, (margin, margin), (margin, margin + BOX_SIZE), 2)  # 左
            pygame.draw.line(screen, BOX_COLOR, (margin + BOX_SIZE, margin), (margin + BOX_SIZE, margin + BOX_SIZE), 2)  # 右
            pygame.draw.line(screen, BOX_COLOR, (margin, margin + BOX_SIZE), (margin + BOX_SIZE, margin + BOX_SIZE), 2)  # 下
        
        # ゴールの描画
        pygame.draw.rect(screen, GOAL_COLOR, goal_rect)
        
        # ブロックの更新と描画
        for block in blocks:
            if not winner and block.update(box_rect, goal_rect, blocks, moving_wall_y):
                winner = block.index
            block.draw(screen)
        
        # 勝者表示
        if winner is not None:
            font = pygame.font.SysFont(None, 72)
            win_color = BLOCK_COLORS[winner]
            # 色の名前を取得
            color_name = COLOR_NAMES[winner]
            text = font.render(f"{color_name} Win!", True, win_color)
            text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(text, text_rect)
            
            # リスタート案内
            font_small = pygame.font.SysFont(None, 36)
            restart_text = font_small.render("Press R to restart", True, (200, 200, 200))
            restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
            screen.blit(restart_text, restart_rect)
        
        # 画面更新
        pygame.display.flip()
        
        # 動画フレームのキャプチャ
        if record:
            try:
                frame = pygame.surfarray.array3d(screen)
                frame = frame.transpose([1, 0, 2])  # PyGameの配列をOpenCVの形式に変換
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # RGBからBGRに変換
                frames.append(frame)
            except Exception as e:
                print(f"フレームキャプチャエラー: {e}")
        
        # 時間管理
        current_game_time = time.time() - game_start_time
        
        # 勝者が決まったらwin_timeを記録
        if winner is not None and win_time is None:
            win_time = time.time()
        
        # 終了条件: 勝利後5秒経過 または 2分経過
        if (win_time is not None and time.time() - win_time >= WIN_DISPLAY_TIME) or \
           current_game_time >= MAX_GAME_TIME:
            running = False
        
        clock.tick(FPS)
    
    # 動画の保存
    if record and frames:
        try:
            # OpenCVで無音動画を作成
            temp_video_path = video_filename
            if AUDIO_EXPORT_ENABLED:
                # 一時ファイル名を使用
                temp_dir = tempfile.mkdtemp()
                temp_video_path = os.path.join(temp_dir, "temp_video.mp4")
                
            print(f"動画を保存しています: {temp_video_path}")
            height, width = frames[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video = cv2.VideoWriter(temp_video_path, fourcc, VIDEO_FPS, (width, height))
            
            for frame in frames:
                video.write(frame)
            
            video.release()
            
            # 音声を追加（FFmpegが必要）
            if AUDIO_EXPORT_ENABLED and os.path.exists(BGM_FILE):
                print("FFmpegを使用して音声を追加しています...")
                
                # BGMをループさせて動画の長さに合わせる
                # FFmpeg 2.8.4には-stream_loopオプションがないため、別の方法でループさせる
                movie_duration = len(frames) / VIDEO_FPS
                print(f"動画の長さ: {movie_duration}秒")
                
                # まずMP3をWAVに変換する（古いFFmpegでの互換性のため）
                convert_cmd = [
                    "ffmpeg", "-y",
                    "-i", BGM_FILE,
                    "-c:a", "pcm_s16le",
                    "-ar", "44100",
                    f"{temp_dir}/original_bgm.wav"
                ]
                
                try:
                    subprocess.run(convert_cmd, check=True)
                    print("BGMをWAVに変換しました")
                    
                    # 次にループ処理（古いバージョン対応）
                    loop_cmd = [
                        "ffmpeg", "-y",
                        "-i", f"{temp_dir}/original_bgm.wav",
                        "-filter_complex", f"aloop=loop=-1:size=2147483647",
                        "-t", str(movie_duration),
                        "-c:a", "pcm_s16le",
                        "-ar", "44100",
                        f"{temp_dir}/looped_bgm.wav"
                    ]
                    
                    subprocess.run(loop_cmd, check=True)
                    print("BGMをループして一時ファイルに保存しました")
                except subprocess.CalledProcessError as e:
                    print(f"BGMループ作成エラー: {e.stderr if hasattr(e, 'stderr') else e}")
                
                # 出力設定
                if os.path.exists(f"{temp_dir}/looped_bgm.wav"):
                    # ループしたBGMを使用（古いFFmpegに対応したコマンド）
                    ffmpeg_cmd = [
                        "ffmpeg", "-y",
                        "-i", temp_video_path,
                        "-i", f"{temp_dir}/looped_bgm.wav",
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-strict", "experimental",  # 古いFFmpeg用の設定
                        "-map", "0:v",
                        "-map", "1:a",
                        "-b:a", "192k",  # ビットレートを指定
                        "-ac", "2",      # ステレオ音声
                        video_filename
                    ]
                else:
                    # 変換とループに失敗した場合：直接BGMを使用
                    print("BGMをループできませんでした。オリジナルのBGMを使用します。")
                    ffmpeg_cmd = [
                        "ffmpeg", "-y",
                        "-i", temp_video_path,
                        "-i", BGM_FILE,
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-strict", "experimental",  # 古いFFmpeg用の設定
                        "-map", "0:v",
                        "-map", "1:a",
                        "-b:a", "192k",
                        "-ac", "2",
                        "-shortest",
                        video_filename
                    ]
                
                try:
                    print("FFmpegコマンドを実行中:", " ".join(ffmpeg_cmd))
                    result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
                    print(f"音声付き動画の保存が完了しました: {video_filename}")
                    
                    # 一時ファイルの削除
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                except subprocess.CalledProcessError as e:
                    print(f"FFmpegエラー: {e}")
                    print(f"エラー出力: {e.stderr.decode('utf-8', errors='ignore') if hasattr(e, 'stderr') else '不明'}")
                    print(f"音声なしで動画を保存します: {video_filename}")
                    
                    # より単純なコマンドで再試行
                    try:
                        simple_cmd = [
                            "ffmpeg", "-y",
                            "-i", temp_video_path,
                            "-i", BGM_FILE,
                            "-c:v", "copy",
                            "-c:a", "aac",
                            "-strict", "experimental",
                            video_filename
                        ]
                        print("単純化したコマンドで再試行:", " ".join(simple_cmd))
                        subprocess.run(simple_cmd, check=True)
                        print("単純化したコマンドでの音声付き動画の作成に成功しました")
                    except Exception as e2:
                        print(f"再試行も失敗: {e2}")
                        # 音声付加に失敗した場合は元の動画を使用
                        if temp_video_path != video_filename:
                            shutil.copy(temp_video_path, video_filename)
                    
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
            else:
                print(f"動画の保存が完了しました: {video_filename} (音声なし)")
        except Exception as e:
            print(f"動画保存エラー: {e}")
            video_filename = None
    
    # メインループ終了後は、画面をクリアするだけで、Pygameは終了しない
    screen.fill(BACKGROUND_COLOR)
    pygame.display.flip()
    
    return video_filename

def run_multiple_simulations(count, record=RECORD_VIDEO):
    """複数回シミュレーションを実行し、複数の動画を生成する関数"""
    video_files = []
    
    print(f"合計{count}個の動画を連続して生成します...")
    
    # Pygameの初期化
    initialize_pygame()
    
    for i in range(count):
        print(f"\n=== 動画 {i+1}/{count} の生成を開始 ===")
        video_filename = main(record=record, block_count=DEFAULT_BLOCK_COUNT)
        if video_filename:
            video_files.append(video_filename)
    
    # すべての動画生成が終了したらPygameを終了
    pygame.quit()
    
    print("\n=== 全ての動画生成が完了しました ===")
    if video_files:
        print("生成された動画ファイル:")
        for i, file in enumerate(video_files):
            print(f"{i+1}. {file}")
    
    return video_files

if __name__ == "__main__":
    import argparse
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='物理演算シミュレーション')
    parser.add_argument('-c', '--count', type=int, default=DEFAULT_VIDEO_COUNT,
                        help=f'生成する動画の数（デフォルト: {DEFAULT_VIDEO_COUNT}個）')
    parser.add_argument('--no-video', action='store_true', 
                        help='動画出力を無効にする')
    args = parser.parse_args()
    
    try:
        # 引数に基づいてシミュレーションを実行
        if args.count > 1:
            # 複数の動画を生成
            video_files = run_multiple_simulations(args.count, record=not args.no_video)
        else:
            # 1つの動画を生成
            initialize_pygame()
            video_filename = main(record=not args.no_video, block_count=DEFAULT_BLOCK_COUNT)
            pygame.quit()
            if video_filename:
                print(f"YouTubeにアップロードできる動画が生成されました: {video_filename}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        pygame.quit()
        sys.exit(1)
