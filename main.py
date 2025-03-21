import pygame
import sys
import random
import math
import os
import time
from pygame import mixer

# 動画出力機能（オプション）
VIDEO_EXPORT_ENABLED = False
try:
    import cv2
    import numpy as np
    from datetime import datetime
    VIDEO_EXPORT_ENABLED = True
    print("動画エクスポート機能が有効です")
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

# Pygameの初期化
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("物理演算シミュレーション")
clock = pygame.time.Clock()

# 音楽の初期化
mixer.init()
if os.path.exists("physics_simulation/bgm.wav"):
    mixer.music.load("physics_simulation/bgm.wav")
    mixer.music.set_volume(0.5)
    mixer.music.play(-1)  # -1はループ再生

# サウンドエフェクト
collision_sound = pygame.mixer.Sound("physics_simulation/collision.wav") if os.path.exists("physics_simulation/collision.wav") else None
goal_sound = pygame.mixer.Sound("physics_simulation/goal.wav") if os.path.exists("physics_simulation/goal.wav") else None

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
        if self.rect.colliderect(goal_rect) and not self.reached_goal:
            self.reached_goal = True
            if goal_sound:
                goal_sound.play()
            return True
        
        return False
    
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, 
                         (self.x - self.size//2, self.y - self.size//2, self.size, self.size))

def main(record=RECORD_VIDEO, block_count=DEFAULT_BLOCK_COUNT):
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
            video_filename = f"physics_simulation/simulation_{timestamp}.mp4"
            os.makedirs("physics_simulation", exist_ok=True)
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
        frame_start_time = time.time()
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
            print(f"動画を保存しています: {video_filename}")
            height, width = frames[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video = cv2.VideoWriter(video_filename, fourcc, VIDEO_FPS, (width, height))
            
            for frame in frames:
                video.write(frame)
            
            video.release()
            print(f"動画の保存が完了しました: {video_filename}")
        except Exception as e:
            print(f"動画保存エラー: {e}")
            video_filename = None
    
    pygame.quit()
    
    if record and frames:
        return video_filename
    
    sys.exit()

def run_multiple_simulations(count, record=RECORD_VIDEO):
    """複数回シミュレーションを実行し、複数の動画を生成する関数"""
    video_files = []
    
    print(f"合計{count}個の動画を連続して生成します...")
    
    for i in range(count):
        print(f"\n=== 動画 {i+1}/{count} の生成を開始 ===")
        video_filename = main(record=record, block_count=DEFAULT_BLOCK_COUNT)
        if video_filename:
            video_files.append(video_filename)
    
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
    
    # 引数に基づいてシミュレーションを実行
    if args.count > 1:
        # 複数の動画を生成
        video_files = run_multiple_simulations(args.count, record=not args.no_video)
    else:
        # 1つの動画を生成
        video_filename = main(record=not args.no_video, block_count=DEFAULT_BLOCK_COUNT)
        if video_filename:
            print(f"YouTubeにアップロードできる動画が生成されました: {video_filename}")
