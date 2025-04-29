import pygame
import pymunk
import math
import random
import config

class Obstacle:
    """
    障害物の基本クラス
    すべての障害物はこのクラスを継承する
    """
    def __init__(self, position, space):
        self.position = position
        self.space = space
        self.body = None
        self.shape = None
        self.color = config.WHITE
        
    def draw(self, screen, camera_y=0):
        """
        障害物を描画（サブクラスでオーバーライド）
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            camera_y (int): カメラのY位置オフセット
        """
        pass
    
    def update(self, dt):
        """
        障害物の状態を更新（動く障害物用）
        
        Args:
            dt (float): 時間の経過（秒）
        """
        pass
    
    def remove_from_space(self):
        """物理空間から障害物を削除"""
        if self.body and self.shape:
            self.space.remove(self.body, self.shape)


class StaticWall(Obstacle):
    """静的な壁（レースコースの壁）"""
    def __init__(self, p1, p2, thickness, space):
        """
        静的な壁を初期化
        
        Args:
            p1 (tuple): 開始点の座標 (x, y)
            p2 (tuple): 終了点の座標 (x, y)
            thickness (int): 壁の厚さ
            space (pymunk.Space): 物理空間
        """
        super().__init__(((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2), space)
        
        self.p1 = p1
        self.p2 = p2
        self.thickness = thickness
        self.color = (150, 150, 150)  # グレー
        
        # 静的ボディの作成
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        
        # セグメント形状の作成（線分） - 壁の厚さを2倍にして当たり判定を大きく
        self.shape = pymunk.Segment(self.body, p1, p2, thickness * 2)
        self.shape.elasticity = 0.7
        self.shape.friction = 0.5
        self.shape.collision_type = config.COLLISION_TYPES["wall"]
        
        # 物理空間に追加
        space.add(self.body, self.shape)
        
    def draw(self, screen, camera_y=0):
        """
        壁を描画
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            camera_y (int): カメラのY位置オフセット
        """
        # カメラオフセットを適用
        p1 = (self.p1[0], self.p1[1] - camera_y)
        p2 = (self.p2[0], self.p2[1] - camera_y)
        
        # 画面内にある場合（簡易チェック）
        if (p1[1] <= config.HEIGHT and p2[1] >= 0) or \
           (p2[1] <= config.HEIGHT and p1[1] >= 0):
            pygame.draw.line(screen, self.color, p1, p2, self.thickness)


class Pin(Obstacle):
    """
    ピン（マーブルの方向を変える小さな円形の障害物）
    """
    def __init__(self, position, radius, space):
        """
        ピンを初期化
        
        Args:
            position (tuple): 位置 (x, y)
            radius (int): 半径
            space (pymunk.Space): 物理空間
        """
        super().__init__(position, space)
        
        self.radius = radius
        self.color = (220, 220, 220)  # 明るいグレー
        
        # 静的ボディの作成
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.body.position = position
        
        # 円形の形状
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = 0.8
        self.shape.friction = 0.3
        self.shape.collision_type = config.COLLISION_TYPES["obstacle"]
        
        # 物理空間に追加
        space.add(self.body, self.shape)
        
    def draw(self, screen, camera_y=0):
        """
        ピンを描画
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            camera_y (int): カメラのY位置オフセット
        """
        # カメラオフセットを適用
        draw_pos = (int(self.position[0]), int(self.position[1] - camera_y))
        
        # 画面内にある場合のみ描画
        if -self.radius <= draw_pos[1] <= config.HEIGHT + self.radius:
            pygame.draw.circle(screen, self.color, draw_pos, self.radius)
            # ハイライト（3D効果）
            highlight_pos = (draw_pos[0] - self.radius // 3, draw_pos[1] - self.radius // 3)
            highlight_radius = self.radius // 4
            pygame.draw.circle(screen, (255, 255, 255), highlight_pos, highlight_radius)


class Flipper(Obstacle):
    """
    フリッパー（一定間隔で回転する障害物）
    """
    def __init__(self, position, length, space):
        """
        フリッパーを初期化
        
        Args:
            position (tuple): 回転軸の位置 (x, y)
            length (int): フリッパーの長さ
            space (pymunk.Space): 物理空間
        """
        super().__init__(position, space)
        
        self.length = length
        self.width = 10  # フリッパーの幅
        self.color = (200, 100, 100)  # 赤っぽい色
        
        # 回転速度と方向
        self.angular_velocity = random.uniform(1.0, 2.5)  # ランダムな速度
        if random.random() < 0.5:
            self.angular_velocity *= -1  # ランダムな方向
        
        # 回転角度（ラジアン）
        self.angle = 0
        
        # 物理ボディの作成（キネマティック：位置は手動で制御するが衝突は検出）
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = position
        
        # ボックス形状の作成
        self.shape = pymunk.Segment(
            self.body, 
            (0, 0),  # 中心点からの相対位置（開始点）
            (length, 0),  # 中心点からの相対位置（終了点）
            self.width
        )
        self.shape.elasticity = 0.8
        self.shape.friction = 0.3
        self.shape.collision_type = config.COLLISION_TYPES["obstacle"]
        
        # 物理空間に追加
        space.add(self.body, self.shape)
    
    def update(self, dt):
        """
        フリッパーの状態を更新（回転）
        
        Args:
            dt (float): 時間の経過（秒）
        """
        # 角度を更新
        self.angle += self.angular_velocity * dt
        
        # ボディの回転角度を設定
        self.body.angle = self.angle
    
    def draw(self, screen, camera_y=0):
        """
        フリッパーを描画
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            camera_y (int): カメラのY位置オフセット
        """
        # カメラオフセットを適用した中心位置
        center_pos = (int(self.position[0]), int(self.position[1] - camera_y))
        
        # 現在の角度に基づいて端点の位置を計算
        end_x = center_pos[0] + self.length * math.cos(self.angle)
        end_y = center_pos[1] + self.length * math.sin(self.angle)
        
        # 画面内にある場合のみ描画（簡易チェック）
        if (0 <= center_pos[1] <= config.HEIGHT or 
            0 <= end_y <= config.HEIGHT):
            # フリッパー本体（線分）
            pygame.draw.line(screen, self.color, center_pos, (end_x, end_y), self.width)
            # 回転軸（小さな円）
            pygame.draw.circle(screen, (150, 150, 150), center_pos, self.width//2)


class RotatingDisc(Obstacle):
    """
    回転円盤（マーブルを乗せて回転させる円盤）
    """
    def __init__(self, position, radius, space):
        """
        回転円盤を初期化
        
        Args:
            position (tuple): 円盤の中心位置 (x, y)
            radius (int): 円盤の半径
            space (pymunk.Space): 物理空間
        """
        super().__init__(position, space)
        
        self.radius = radius
        self.color = (100, 150, 200)  # 青っぽい色
        
        # 回転速度（ラジアン/秒）
        self.angular_velocity = random.uniform(0.5, 2.0)
        if random.random() < 0.5:
            self.angular_velocity *= -1  # ランダムな方向
        
        # 回転角度（ラジアン）
        self.angle = 0
        
        # 物理ボディの作成（キネマティック）
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = position
        
        # 円形の形状
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = 0.4
        self.shape.friction = 0.9  # 高めの摩擦でマーブルが滑らないように
        self.shape.collision_type = config.COLLISION_TYPES["obstacle"]
        
        # 物理空間に追加
        space.add(self.body, self.shape)
        
        # パターン表示用の属性
        self.pattern_angle = 0  # パターンの回転角度
    
    def update(self, dt):
        """
        回転円盤の状態を更新
        
        Args:
            dt (float): 時間の経過（秒）
        """
        # 回転角度を更新
        self.angle += self.angular_velocity * dt
        self.pattern_angle = self.angle  # パターン表示用
        
        # ボディの角速度を設定（速度ベクトルではなく角速度）
        self.body.angular_velocity = self.angular_velocity
    
    def draw(self, screen, camera_y=0):
        """
        回転円盤を描画
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            camera_y (int): カメラのY位置オフセット
        """
        # カメラオフセットを適用
        draw_pos = (int(self.position[0]), int(self.position[1] - camera_y))
        
        # 画面内にある場合のみ描画
        if -self.radius <= draw_pos[1] <= config.HEIGHT + self.radius:
            # 円盤の本体
            pygame.draw.circle(screen, self.color, draw_pos, self.radius)
            
            # 円盤の回転を表すパターン（線）
            for i in range(4):
                angle = self.pattern_angle + i * (math.pi / 2)
                line_start_x = draw_pos[0] + (self.radius * 0.3) * math.cos(angle)
                line_start_y = draw_pos[1] + (self.radius * 0.3) * math.sin(angle)
                line_end_x = draw_pos[0] + (self.radius * 0.9) * math.cos(angle)
                line_end_y = draw_pos[1] + (self.radius * 0.9) * math.sin(angle)
                
                pygame.draw.line(
                    screen, 
                    (50, 50, 150), 
                    (line_start_x, line_start_y), 
                    (line_end_x, line_end_y), 
                    3
                )
            
            # 中心点（小さな円）
            pygame.draw.circle(screen, (50, 50, 150), draw_pos, self.radius * 0.2)
