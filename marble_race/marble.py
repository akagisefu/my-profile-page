import pygame
import pymunk
import math
import config

class Marble:
    """
    マーブル（ビー玉）クラス
    物理演算と描画を処理
    """
    def __init__(self, position, color_index, space):
        """
        マーブルを初期化
        
        Args:
            position (tuple): 初期位置 (x, y)
            color_index (int): 色のインデックス（0-3）
            space (pymunk.Space): 物理空間
        """
        self.color = config.MARBLE_COLORS[color_index]
        self.color_name = ["Red", "Blue", "Green", "Yellow"][color_index]
        self.color_index = color_index
        self.radius = config.MARBLE_RADIUS
        self.mass = config.MARBLE_MASS
        
        # 物理ボディの作成（動的）
        moment = pymunk.moment_for_circle(self.mass, 0, self.radius)
        self.body = pymunk.Body(self.mass, moment)
        self.body.position = position
        
        # 形状の作成（円）
        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.elasticity = config.MARBLE_ELASTICITY
        self.shape.friction = config.MARBLE_FRICTION
        self.shape.collision_type = config.COLLISION_TYPES["marble"]
        
        # データ属性
        self.shape.marble = self  # 形状からマーブルを参照できるようにする
        
        # 物理空間に追加
        space.add(self.body, self.shape)
        
        # レース関連の属性
        self.finished = False
        self.finish_time = None
        self.position = 0  # レースでの順位
        self.checkpoints = []  # 通過したチェックポイント
        
        # 表示用の属性
        self.trail = []  # 軌跡
        self.trail_max_length = 10  # 軌跡の最大長（短くして目立たなくする）
        self.trail_update_rate = 4  # フレームごとの軌跡更新レート（増やして軌跡を間引く）
        self.frame_counter = 0

    def update(self):
        """Update the marble state"""
        # 速度の最大値を制限
        max_velocity = 1200  # 最大速度を設定
        
        # 現在の速度のベクトル長さを取得
        velocity_length = self.body.velocity.length
        
        # 最大速度を超えている場合は調整
        if velocity_length > max_velocity:
            # 速度ベクトルを正規化して、最大速度を掛ける
            normalized_velocity = self.body.velocity.normalized()
            self.body.velocity = normalized_velocity * max_velocity
    
    def draw(self, screen, camera_y=0):
        """
        Draw the marble
        
        Args:
            screen (pygame.Surface): Surface to draw on
            camera_y (int): Camera Y position offset
        """
        # No trail drawing - trails are disabled
        
        # マーブル本体の描画
        draw_pos = (int(self.body.position.x), int(self.body.position.y - camera_y))
        
        # 画面内にある場合のみ描画
        if -self.radius <= draw_pos[1] <= config.HEIGHT + self.radius:
            # マーブルの本体
            pygame.draw.circle(screen, self.color, draw_pos, self.radius)
            
            # マーブルの光沢効果（左上に小さな白い円）
            highlight_radius = self.radius // 3
            highlight_offset = self.radius // 2
            highlight_pos = (draw_pos[0] - highlight_offset, draw_pos[1] - highlight_offset)
            pygame.draw.circle(screen, (255, 255, 255, 180), highlight_pos, highlight_radius)
    
    def get_position_y(self):
        """Y座標を取得（カメラ追従用）"""
        return self.body.position.y
    
    def is_visible(self, camera_y):
        """
        マーブルが画面内に表示されているかチェック
        
        Args:
            camera_y (int): カメラのY位置
        
        Returns:
            bool: 画面内に表示されていればTrue
        """
        y = self.body.position.y - camera_y
        return -self.radius <= y <= config.HEIGHT + self.radius
    
    def mark_finished(self, time):
        """
        マーブルがゴールしたことをマーク
        
        Args:
            time (float): ゴール時間
        """
        self.finished = True
        self.finish_time = time
    
    def add_checkpoint(self, checkpoint_id):
        """
        チェックポイントを追加
        
        Args:
            checkpoint_id (int): チェックポイントID
        """
        if checkpoint_id not in self.checkpoints:
            self.checkpoints.append(checkpoint_id)
    
    def remove_from_space(self, space):
        """
        物理空間からマーブルを削除
        
        Args:
            space (pymunk.Space): 物理空間
        """
        space.remove(self.body, self.shape)
