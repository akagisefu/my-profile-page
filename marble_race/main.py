import pygame
import pymunk
import sys
import os
import time
import random
import math

# プロジェクト内のモジュールをインポート
import sys
import os

# 現在のディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# モジュールをインポート
import config
from marble import Marble
from course import Course
from renderer import Renderer
from exporter import VideoExporter, AudioManager

class MarbleRace:
    """
    マーブルレースのメインクラス
    シミュレーション全体を管理
    """
    def __init__(self):
        """ゲームの初期化"""
        # Pygameの初期化
        pygame.init()
        
        # 画面の設定
        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        pygame.display.set_caption(config.TITLE)
        
        # クロック（フレームレート制御）
        self.clock = pygame.time.Clock()
        
        # 物理エンジン（空間）の設定
        self.space = pymunk.Space()
        self.space.gravity = config.GRAVITY
        self.space.damping = config.DAMPING
        
        # 衝突ハンドラの設定
        self.setup_collision_handlers()
        
        # コースの作成
        self.course = Course(self.space)
        
        # マーブル（ビー玉）のリスト
        self.marbles = []
        
        # レース状態
        self.race_state = config.STATE_READY
        self.race_time = 0  # レース時間
        
        # カメラの位置（Y座標のみ）
        self.camera_y = 0
        
        # レンダラーの作成
        self.renderer = Renderer()
        
        # ビデオ出力の設定
        self.video_exporter = None
        if config.RECORD_VIDEO:
            self.video_exporter = VideoExporter()
        
        # 音声マネージャー
        self.audio_manager = AudioManager()
        
        # イントロステージ（0: タイトル画面, 1: マーブル紹介）
        self.intro_stage = 0
        
        # カウントダウン
        self.countdown_value = 3
        self.countdown_timer = 0
        self.is_countdown = False
        
        # 実行フラグ
        self.running = True
        
        # ビデオ出力ディレクトリの作成
        if config.RECORD_VIDEO:
            os.makedirs(os.path.join("marble_race", config.VIDEO_DIR), exist_ok=True)
    
    def setup_collision_handlers(self):
        """衝突ハンドラを設定"""
        # マーブルとゴールの衝突検出
        goal_handler = self.space.add_collision_handler(
            config.COLLISION_TYPES["marble"],
            config.COLLISION_TYPES["goal"]
        )
        goal_handler.begin = self.handle_goal_collision
        
        # マーブル同士の衝突
        marble_handler = self.space.add_collision_handler(
            config.COLLISION_TYPES["marble"],
            config.COLLISION_TYPES["marble"]
        )
        marble_handler.post_solve = self.handle_marble_collision
    
    def handle_goal_collision(self, arbiter, space, data):
        """
        マーブルがゴールに到達した時の処理
        
        Args:
            arbiter: 衝突情報
            space: 物理空間
            data: 追加データ
            
        Returns:
            bool: 通常の物理衝突を処理するかどうか
        """
        # 衝突した形状からマーブルを特定
        shapes = arbiter.shapes
        marble_shape = shapes[0]
        
        # マーブルオブジェクトを取得
        if hasattr(marble_shape, 'marble'):
            marble = marble_shape.marble
            
            # まだゴールしていない場合のみ処理
            if not marble.finished:
                marble.mark_finished(self.race_time)
                print(f"{marble.color_name} marble reached the goal! Time: {self.race_time:.2f}s")
                
                # ゴール効果音
                self.audio_manager.play_sound("goal")
                
                # すべてのマーブルがゴールしたかチェック
                all_finished = all(m.finished for m in self.marbles)
                if all_finished:
                    self.race_state = config.STATE_FINISHED
                    print("Race finished!")
        
        # ゴールは物理的には衝突しない（センサー）
        return False
    
    def handle_marble_collision(self, arbiter, space, data):
        """
        マーブル同士が衝突した時の処理
        
        Args:
            arbiter: 衝突情報
            space: 物理空間
            data: 追加データ
        """
        # 衝突の強さに基づいて効果音の再生を判断
        if arbiter.total_impulse.length > 10:
            # 衝突効果音（音量を衝突の強さに応じて調整）
            volume = min(1.0, arbiter.total_impulse.length / 100)
            if random.random() < 0.1:  # 衝突音が多すぎないように調整
                self.audio_manager.play_sound("collision")
    
    def create_marbles(self):
        """マーブルを作成"""
        if len(self.marbles) > 0:
            # すでに作成済みの場合は何もしない
            return
        
        # 4種類のマーブルを作成
        for i in range(4):
            position = config.START_POSITIONS[i]
            marble = Marble(position, i, self.space)
            self.marbles.append(marble)
    
    def reset_game(self):
        """ゲームをリセットする"""
        # 既存のマーブルを削除
        for marble in self.marbles:
            marble.remove_from_space(self.space)
        self.marbles = []
        
        # 新しいマーブルを作成
        self.create_marbles()
        
        # レース状態をリセット
        self.race_state = config.STATE_READY
        self.race_time = 0
        
        # カメラ位置をリセット
        self.camera_y = 0
    
    def start_race(self):
        """レースを開始する"""
        # カウントダウンを開始
        self.is_countdown = True
        self.countdown_value = 3
        self.countdown_timer = time.time()
        
        # BGM開始
        self.audio_manager.play_music()
    
    def update_countdown(self):
        """カウントダウンを更新"""
        current_time = time.time()
        elapsed = current_time - self.countdown_timer
        
        # 1秒ごとにカウントダウン
        if elapsed >= 1.0:
            self.countdown_value -= 1
            self.countdown_timer = current_time
            
            # カウント音再生
            self.audio_manager.play_sound("count")
            
            # カウントダウンが0になったらレース開始
            if self.countdown_value <= 0:
                self.is_countdown = False
                self.race_state = config.STATE_RUNNING
                
                # スタート音
                self.audio_manager.play_sound("start")
    
    def update(self, dt):
        """
        ゲーム状態を更新
        
        Args:
            dt (float): 経過時間（秒）
        """
        # レース中のみ時間を更新
        if self.race_state == config.STATE_RUNNING:
            self.race_time += dt
        
        # カウントダウン中の処理
        if self.is_countdown:
            self.update_countdown()
            
            # カウントダウン中は物理演算を適用せず、初期位置を維持
            for i, marble in enumerate(self.marbles):
                # 初期位置に固定
                marble.body.position = config.START_POSITIONS[i]
                marble.body.velocity = (0, 0)
        else:
            # レース中のみ物理演算を更新
            self.space.step(dt)
            
            # マーブルの状態を更新
            for marble in self.marbles:
                marble.update()
            
            # 障害物など動的要素の更新
            self.course.update(dt)
        
        # カメラの位置を更新
        self.update_camera()
    
    def update_camera(self):
        """カメラの位置を更新（先頭のマーブルを追従）"""
        if not self.marbles:
            return
        
        # レース中のマーブル（まだゴールしていないマーブル）
        active_marbles = [m for m in self.marbles if not m.finished]
        
        # アクティブなマーブルがない場合は全マーブルを対象にする
        target_marbles = active_marbles if active_marbles else self.marbles
        
        # 最も遠くまで進んだマーブルを見つける（Y座標が最大のもの）
        leading_marble = max(target_marbles, key=lambda m: m.get_position_y())
        
        # カメラのターゲット位置（マーブルの位置 - オフセット）
        target_y = leading_marble.get_position_y() - config.CAMERA_OFFSET_Y
        
        # コースの始点より上にはカメラを移動させない
        target_y = max(0, target_y)
        
        # コースの終点を超えてカメラを動かさない
        target_y = min(target_y, config.COURSE_LENGTH - config.HEIGHT)
        
        # スムーズに追従するための補間
        self.camera_y += (target_y - self.camera_y) * config.CAMERA_SMOOTH
    
    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            # 終了イベント
            if event.type == pygame.QUIT:
                self.running = False
            
            # キー入力
            elif event.type == pygame.KEYDOWN:
                # エスケープキーで終了
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                # スペースキーでゲーム状態切り替え
                elif event.key == pygame.K_SPACE:
                    if self.intro_stage == 0:
                        # タイトル画面からマーブル紹介へ
                        self.intro_stage = 1
                        self.create_marbles()
                    elif self.intro_stage == 1:
                        # マーブル紹介からレース開始
                        self.intro_stage = None
                        self.start_race()
                    elif self.race_state == config.STATE_FINISHED:
                        # レース終了状態からリセット
                        self.reset_game()
                        self.intro_stage = 0
                
                # Rキーでリセット
                elif event.key == pygame.K_r:
                    self.reset_game()
                    self.intro_stage = 0
    
    def render(self):
        """描画処理"""
        # イントロ画面
        if self.intro_stage is not None:
            self.renderer.draw_intro(self.screen, self.marbles, self.intro_stage)
            return
        
        # 通常のゲーム画面
        # まず画面を完全に黒でクリア（残像防止）
        self.screen.fill((0, 0, 0))
        
        # 背景描画
        self.renderer.draw_background(self.screen, self.camera_y)
        
        # コース描画
        self.renderer.draw_course(self.screen, self.course, self.camera_y)
        
        # マーブル描画
        self.renderer.draw_marbles(self.screen, self.marbles, self.camera_y)
        
        # UI描画
        self.renderer.draw_ui(
            self.screen, 
            self.marbles, 
            self.race_time, 
            self.camera_y, 
            self.race_state
        )
        
        # カウントダウン表示
        if self.is_countdown:
            self.renderer.draw_countdown(self.screen, self.countdown_value)
    
    def run(self):
        """ゲームのメインループ"""
        try:
            # ゲームループ
            while self.running:
                # デルタタイム計算（秒単位）
                dt = self.clock.tick(config.FPS) / 1000.0
                
                # イベント処理
                self.handle_events()
                
                # 状態更新
                self.update(dt)
                
                # 描画
                self.render()
                pygame.display.flip()
                
                # ビデオ録画
                if self.video_exporter and self.video_exporter.enabled:
                    self.video_exporter.capture_frame(self.screen)
        except Exception as e:
            print(f"エラーが発生しました: {e}")
        finally:
            # クリーンアップ
            self.cleanup()
    
    def cleanup(self):
        """リソースの解放など終了処理"""
        print("終了処理を実行中...")
        
        # ビデオ出力の終了処理
        if self.video_exporter and self.video_exporter.enabled:
            self.video_exporter.finalize()
        
        # 音楽を停止
        self.audio_manager.stop_music()
        
        # Pygameを終了
        pygame.quit()
        
        print("終了処理完了。")

# メイン実行部分
if __name__ == "__main__":
    # マーブルレースのインスタンスを作成
    game = MarbleRace()
    
    # ゲーム実行
    game.run()
    
    # プログラム終了
    sys.exit()
