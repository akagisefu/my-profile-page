import pygame
import pymunk
import random
import math
import config
from obstacles import StaticWall, Pin, Flipper, RotatingDisc

class Course:
    """
    マーブルレースのコース管理クラス
    コースの生成、障害物の配置などを担当
    """
    def __init__(self, space):
        """
        コースを初期化
        
        Args:
            space (pymunk.Space): 物理空間
        """
        self.space = space
        self.width = config.COURSE_WIDTH
        self.length = config.COURSE_LENGTH
        self.wall_thickness = config.WALL_THICKNESS
        
        # コース要素を保存するリスト
        self.walls = []
        self.obstacles = []
        self.checkpoints = []
        self.goal = None
        
        # コース生成
        self.generate_course()
    
    def generate_course(self):
        """コース全体を生成"""
        # コースの左右の壁を生成（縦長コース全体）
        self.create_side_walls()
        
        # コースを複数のセクションに分ける
        self.create_section_1(0, self.length * 0.3)                  # 序盤セクション（全体の30%）
        self.create_section_2(self.length * 0.3, self.length * 0.7)  # 中盤セクション（全体の40%）
        self.create_section_3(self.length * 0.7, self.length)        # 終盤セクション（全体の30%）
        
        # ゴールエリアを作成
        self.create_goal(self.length - 200)
    
    def create_side_walls(self):
        """コースの左右の壁を生成 - ギザギザのパターンで蛇行させる"""
        # コースの幅を狭くする
        narrow_width = self.width * 0.6
        
        # 左右の壁を蛇行させるための基準点を作成
        segment_length = 300  # 各セグメントの長さ
        num_segments = int(self.length / segment_length)
        zigzag_amplitude = self.width * 0.15  # ジグザグの振幅
        
        # 左側の壁のベース位置
        left_base_x = (config.WIDTH - narrow_width) / 2
        # 右側の壁のベース位置
        right_base_x = (config.WIDTH + narrow_width) / 2
        
        # 左側の壁をジグザグに配置
        for i in range(num_segments):
            start_y = i * segment_length
            end_y = (i + 1) * segment_length
            
            # ジグザグパターンを作成（左右に蛇行）
            if i % 2 == 0:
                # 左に膨らむ
                mid_x_left = left_base_x - zigzag_amplitude
                mid_x_right = right_base_x - zigzag_amplitude
            else:
                # 右に膨らむ
                mid_x_left = left_base_x + zigzag_amplitude
                mid_x_right = right_base_x + zigzag_amplitude
            
            mid_y = (start_y + end_y) / 2
            
            # 左側の壁の上部セグメント
            left_wall_top = StaticWall(
                (left_base_x, start_y),
                (mid_x_left, mid_y),
                self.wall_thickness // 2,  # 壁を薄く
                self.space
            )
            self.walls.append(left_wall_top)
            
            # 左側の壁の下部セグメント
            left_wall_bottom = StaticWall(
                (mid_x_left, mid_y),
                (left_base_x, end_y),
                self.wall_thickness // 2,
                self.space
            )
            self.walls.append(left_wall_bottom)
            
            # 右側の壁の上部セグメント
            right_wall_top = StaticWall(
                (right_base_x, start_y),
                (mid_x_right, mid_y),
                self.wall_thickness // 2,
                self.space
            )
            self.walls.append(right_wall_top)
            
            # 右側の壁の下部セグメント
            right_wall_bottom = StaticWall(
                (mid_x_right, mid_y),
                (right_base_x, end_y),
                self.wall_thickness // 2,
                self.space
            )
            self.walls.append(right_wall_bottom)
        
        # 始点と終点に短い直線壁を追加（安定性のため）
        # 開始地点
        start_left_wall = StaticWall(
            (left_base_x, 0),
            (left_base_x, 50),
            self.wall_thickness,
            self.space
        )
        self.walls.append(start_left_wall)
        
        start_right_wall = StaticWall(
            (right_base_x, 0),
            (right_base_x, 50),
            self.wall_thickness,
            self.space
        )
        self.walls.append(start_right_wall)
        
        # 終点
        end_left_wall = StaticWall(
            (left_base_x, self.length - 50),
            (left_base_x, self.length),
            self.wall_thickness,
            self.space
        )
        self.walls.append(end_left_wall)
        
        end_right_wall = StaticWall(
            (right_base_x, self.length - 50),
            (right_base_x, self.length),
            self.wall_thickness,
            self.space
        )
        self.walls.append(end_right_wall)
    
    def create_section_1(self, start_y, end_y):
        """
        序盤セクションの生成（比較的シンプルな障害物配置）
        
        Args:
            start_y (float): セクション開始位置（Y座標）
            end_y (float): セクション終了位置（Y座標）
        """
        section_length = end_y - start_y
        
        # 障害物の数を決定
        num_pins = int(section_length / 200)  # 約200pxごとにピン
        num_flippers = 2  # この区間のフリッパー数
        
        # ======== ピンの配置 ========
        # コース幅を8分割してピンを配置 - 5倍に大きくする
        pin_radius = 50  # 元の10から50に拡大
        for i in range(num_pins):
            y_pos = start_y + section_length * (i + 1) / (num_pins + 1)
            
            # 各行で異なるパターンでピンを配置
            if i % 3 == 0:  # パターン1: 交互配置
                for x_div in range(1, 8, 2):
                    x_pos = (config.WIDTH - self.width) / 2 + self.width * x_div / 8
                    pin = Pin((x_pos, y_pos), pin_radius, self.space)
                    self.obstacles.append(pin)
            elif i % 3 == 1:  # パターン2: 三角形配置
                for x_div in [2, 4, 6]:
                    x_pos = (config.WIDTH - self.width) / 2 + self.width * x_div / 8
                    pin = Pin((x_pos, y_pos), pin_radius, self.space)
                    self.obstacles.append(pin)
            else:  # パターン3: 左右寄せ
                for x_div in [1, 2, 6, 7]:
                    x_pos = (config.WIDTH - self.width) / 2 + self.width * x_div / 8
                    pin = Pin((x_pos, y_pos), pin_radius, self.space)
                    self.obstacles.append(pin)
        
        # ======== フリッパーの配置 ========
        for i in range(num_flippers):
            y_pos = start_y + section_length * (i + 1) / (num_flippers + 1)
            
            # 左右のどちらかに配置
            if i % 2 == 0:  # 左側
                x_pos = (config.WIDTH - self.width) / 2 + self.width * 0.25
                flipper = Flipper((x_pos, y_pos), 100, self.space)
            else:  # 右側
                x_pos = (config.WIDTH - self.width) / 2 + self.width * 0.75
                flipper = Flipper((x_pos, y_pos), 100, self.space)
            
            self.obstacles.append(flipper)
    
    def create_section_2(self, start_y, end_y):
        """
        中盤セクションの生成（複雑な障害物と分岐）
        
        Args:
            start_y (float): セクション開始位置（Y座標）
            end_y (float): セクション終了位置（Y座標）
        """
        section_length = end_y - start_y
        
        # 障害物の数を決定
        num_rotating_discs = 3  # 回転円盤の数
        num_pin_clusters = 4    # ピンのクラスター数
        num_flippers = 3        # フリッパー数
        
        # ======== 回転円盤の配置 ========
        # 大きな回転円盤をコース中央に配置
        disc_radius = 120
        for i in range(num_rotating_discs):
            y_pos = start_y + section_length * (i + 1) / (num_rotating_discs + 1)
            
            # 位置を少しずらす（左右に振る）
            if i % 3 == 0:
                x_pos = config.WIDTH / 2 - self.width * 0.1  # 少し左
            elif i % 3 == 1:
                x_pos = config.WIDTH / 2                     # 中央
            else:
                x_pos = config.WIDTH / 2 + self.width * 0.1  # 少し右
            
            disc = RotatingDisc((x_pos, y_pos), disc_radius, self.space)
            self.obstacles.append(disc)
        
        # ======== ピンクラスターの配置 ========
        # 複数のピンをグループ化して配置
        pin_radius = 8
        for i in range(num_pin_clusters):
            cluster_y = start_y + section_length * (i + 1) / (num_pin_clusters + 1)
            
            # クラスタータイプ（パターン）を選択
            cluster_type = i % 3
            
            if cluster_type == 0:
                # 格子状パターン
                for row in range(3):
                    for col in range(5):
                        x_pos = (config.WIDTH - self.width) / 2 + self.width * (col + 1) / 6
                        y_pos = cluster_y - 40 + row * 40  # 縦に3つ並べる
                        pin = Pin((x_pos, y_pos), pin_radius, self.space)
                        self.obstacles.append(pin)
            
            elif cluster_type == 1:
                # 菱形パターン
                for offset in range(5):
                    # 中央を頂点とする菱形
                    x_offset = offset * 15
                    y_offset = abs(offset - 2) * 30
                    
                    x_pos = config.WIDTH / 2 - x_offset
                    y_pos = cluster_y - y_offset
                    pin1 = Pin((x_pos, y_pos), pin_radius, self.space)
                    self.obstacles.append(pin1)
                    
                    if offset != 2:  # 中央のピンを重複させない
                        x_pos = config.WIDTH / 2 + x_offset
                        pin2 = Pin((x_pos, y_pos), pin_radius, self.space)
                        self.obstacles.append(pin2)
            
            else:
                # ジグザグパターン
                zigzag_width = self.width * 0.6
                num_zigzag = 7
                for z in range(num_zigzag):
                    x_pos = (config.WIDTH - zigzag_width) / 2 + zigzag_width * z / (num_zigzag - 1)
                    y_pos = cluster_y + (30 if z % 2 == 0 else -30)
                    pin = Pin((x_pos, y_pos), pin_radius, self.space)
                    self.obstacles.append(pin)
        
        # ======== フリッパーの配置 ========
        # 中央付近で複数のフリッパーを配置
        for i in range(num_flippers):
            y_pos = start_y + section_length * (i + 1) / (num_flippers + 1)
            
            # フリッパーの配置パターン
            if i == 0:
                # 両側に小さなフリッパー
                left_x = (config.WIDTH - self.width) / 2 + self.width * 0.2
                right_x = (config.WIDTH - self.width) / 2 + self.width * 0.8
                
                flipper1 = Flipper((left_x, y_pos), 80, self.space)
                flipper2 = Flipper((right_x, y_pos), 80, self.space)
                self.obstacles.extend([flipper1, flipper2])
            
            elif i == 1:
                # 中央に大きなフリッパー
                center_x = config.WIDTH / 2
                flipper = Flipper((center_x, y_pos), 160, self.space)
                self.obstacles.append(flipper)
            
            else:
                # 交差するフリッパー
                left_x = (config.WIDTH - self.width) / 2 + self.width * 0.3
                right_x = (config.WIDTH - self.width) / 2 + self.width * 0.7
                
                flipper1 = Flipper((left_x, y_pos - 20), 120, self.space)
                flipper2 = Flipper((right_x, y_pos + 20), 120, self.space)
                self.obstacles.extend([flipper1, flipper2])
        
        # ======== 中央の仕切り壁 ========
        # セクションの途中に仕切り壁を作成し、左右に分岐させる
        divider_y = start_y + section_length * 0.6
        divider_length = section_length * 0.2
        
        # 中央の仕切り
        center_x = config.WIDTH / 2
        center_divider = StaticWall(
            (center_x, divider_y),
            (center_x, divider_y + divider_length),
            self.wall_thickness,
            self.space
        )
        self.walls.append(center_divider)
        
        # 左側の誘導壁（少し傾ける）
        left_divider = StaticWall(
            (center_x, divider_y),
            (center_x - self.width * 0.2, divider_y + divider_length * 0.7),
            self.wall_thickness // 2,
            self.space
        )
        self.walls.append(left_divider)
        
        # 右側の誘導壁（少し傾ける）
        right_divider = StaticWall(
            (center_x, divider_y),
            (center_x + self.width * 0.2, divider_y + divider_length * 0.7),
            self.wall_thickness // 2,
            self.space
        )
        self.walls.append(right_divider)
    
    def create_section_3(self, start_y, end_y):
        """
        終盤セクションの生成（狭路や精密配置）
        
        Args:
            start_y (float): セクション開始位置（Y座標）
            end_y (float): セクション終了位置（Y座標）
        """
        section_length = end_y - start_y
        
        # 障害物の数を決定
        num_lanes = 3  # レーン数
        
        # ======== 複数レーンの作成 ========
        # コースを複数のレーンに分ける
        lane_width = self.width / num_lanes
        
        # レーン分けの壁を作成
        for i in range(1, num_lanes):
            lane_x = (config.WIDTH - self.width) / 2 + lane_width * i
            lane_wall = StaticWall(
                (lane_x, start_y),
                (lane_x, start_y + section_length * 0.5),  # レーンの半分まで
                self.wall_thickness // 2,  # 薄い壁
                self.space
            )
            self.walls.append(lane_wall)
        
        # ======== 各レーンに障害物を配置 ========
        for lane in range(num_lanes):
            lane_center_x = (config.WIDTH - self.width) / 2 + lane_width * (lane + 0.5)
            
            # レーンごとに異なる障害物パターン
            if lane == 0:  # 左レーン
                # ピンの階段
                for i in range(10):
                    x_pos = lane_center_x - lane_width * 0.25 + lane_width * 0.5 * (i % 2)
                    y_pos = start_y + section_length * 0.1 + i * section_length * 0.04
                    pin = Pin((x_pos, y_pos), 8, self.space)
                    self.obstacles.append(pin)
                
                # フリッパー
                flipper = Flipper(
                    (lane_center_x, start_y + section_length * 0.7),
                    lane_width * 0.8,
                    self.space
                )
                self.obstacles.append(flipper)
            
            elif lane == 1:  # 中央レーン
                # 回転円盤
                disc = RotatingDisc(
                    (lane_center_x, start_y + section_length * 0.25),
                    lane_width * 0.4,
                    self.space
                )
                self.obstacles.append(disc)
                
                # ジグザグピン
                for i in range(8):
                    x_pos = lane_center_x - lane_width * 0.3 + lane_width * 0.6 * (i % 2)
                    y_pos = start_y + section_length * 0.5 + i * section_length * 0.05
                    pin = Pin((x_pos, y_pos), 8, self.space)
                    self.obstacles.append(pin)
            
            else:  # 右レーン
                # 小さなフリッパー2つ
                flipper1 = Flipper(
                    (lane_center_x - lane_width * 0.25, start_y + section_length * 0.2),
                    lane_width * 0.4,
                    self.space
                )
                flipper2 = Flipper(
                    (lane_center_x + lane_width * 0.25, start_y + section_length * 0.4),
                    lane_width * 0.4,
                    self.space
                )
                self.obstacles.extend([flipper1, flipper2])
                
                # ピンの格子
                for row in range(3):
                    for col in range(2):
                        x_pos = lane_center_x - lane_width * 0.25 + lane_width * 0.5 * col
                        y_pos = start_y + section_length * 0.6 + row * section_length * 0.05
                        pin = Pin((x_pos, y_pos), 8, self.space)
                        self.obstacles.append(pin)
        
        # ======== 収束部分 ========
        # レーンを徐々に一つに収束させる（漏斗状）
        funnel_start_y = start_y + section_length * 0.8
        funnel_end_y = end_y - 100
        
        # 左側の漏斗壁
        left_funnel = StaticWall(
            ((config.WIDTH - self.width) / 2, funnel_start_y),
            (config.WIDTH / 2 - self.width * 0.1, funnel_end_y),
            self.wall_thickness,
            self.space
        )
        self.walls.append(left_funnel)
        
        # 右側の漏斗壁
        right_funnel = StaticWall(
            ((config.WIDTH + self.width) / 2, funnel_start_y),
            (config.WIDTH / 2 + self.width * 0.1, funnel_end_y),
            self.wall_thickness,
            self.space
        )
        self.walls.append(right_funnel)
    
    def create_goal(self, y_position):
        """
        ゴールエリアを作成
        
        Args:
            y_position (float): ゴールのY座標
        """
        # ゴールラインの位置（コース下部）
        goal_width = self.width * 0.3
        goal_center_x = config.WIDTH / 2
        
        # ゴールの左右の壁
        left_goal_x = goal_center_x - goal_width / 2
        right_goal_x = goal_center_x + goal_width / 2
        
        # ゴールエリアの作成（センサーのみ、視覚的な要素は描画時に追加）
        goal_height = 20
        
        # ゴールセンサーのボディ（静的）
        goal_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        
        # ゴールセンサーの形状（長方形）
        goal_shape = pymunk.Segment(
            goal_body,
            (left_goal_x, y_position),
            (right_goal_x, y_position),
            goal_height
        )
        goal_shape.collision_type = config.COLLISION_TYPES["goal"]
        goal_shape.sensor = True  # センサーとして機能（物理的に衝突しない）
        
        # 物理空間に追加
        self.space.add(goal_body, goal_shape)
        
        # ゴール情報の保存
        self.goal = {
            "position": (goal_center_x, y_position),
            "width": goal_width,
            "body": goal_body,
            "shape": goal_shape
        }
    
    def draw(self, screen, camera_y=0):
        """
        コースを描画
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            camera_y (int): カメラのY位置オフセット
        """
        # 壁の描画
        for wall in self.walls:
            wall.draw(screen, camera_y)
        
        # 障害物の描画
        for obstacle in self.obstacles:
            obstacle.draw(screen, camera_y)
        
        # ゴールエリアの描画
        if self.goal:
            goal_pos = (self.goal["position"][0], self.goal["position"][1] - camera_y)
            goal_width = self.goal["width"]
            
            # 画面内にある場合のみ描画
            if 0 <= goal_pos[1] <= config.HEIGHT:
                # ゴールライン
                pygame.draw.line(
                    screen,
                    (255, 215, 0),  # 金色
                    (goal_pos[0] - goal_width / 2, goal_pos[1]),
                    (goal_pos[0] + goal_width / 2, goal_pos[1]),
                    5
                )
                
                # "GOAL" テキスト
                font = pygame.font.SysFont("Arial", 36)
                text_surface = font.render("GOAL", True, (255, 215, 0))
                text_rect = text_surface.get_rect(center=(goal_pos[0], goal_pos[1] - 30))
                screen.blit(text_surface, text_rect)
    
    def update(self, dt):
        """
        コース内の動的要素を更新
        
        Args:
            dt (float): 時間の経過（秒）
        """
        # 動的な障害物を更新
        for obstacle in self.obstacles:
            obstacle.update(dt)
