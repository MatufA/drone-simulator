import pygame
from math import cos, sin, radians
from datetime import timedelta
from DroneState import DroneState


class Drone:
    MAX_SPEED = 3  # meter / sec
    MAX_YAW_SPEED = 180  # deg/sec  (aka  1.0 PI)
    MAX_FLIGHT_TIME = 60 * 5  # 5 Minute
    DT = 1.0 / 50  # ms ==> 50Hz

    def __init__(self, start_x, start_y, color, bounds_color, lidars):
        """

        :param start_x:
        :param start_y:
        :param color:
        :param bounds_color:
        :param lidars:
        """
        self.state = DroneState
        self.yaw = 0
        self.mode = self.state.GROUND
        self.speed = 0
        self.time_in_air = Drone.MAX_FLIGHT_TIME
        self.error_case = 0
        self.score = 0
        self.radius = 3
        self.x_position = start_x
        self.y_position = start_y
        self.lidars = lidars

        self.color = color
        self.bounds_color = bounds_color

    def rotate(self, maze, direction, game_display):
        """rotate the drone.

        :param game_display:
        :param direction:
        :param maze:
        :return:
        """

        self.yaw += direction * self.speed
        if self.yaw >= 360:
            self.yaw = self.yaw % 360
        elif self.yaw < 0:
            self.yaw = 360 + self.yaw

        for lidar in self.lidars:
            lidar.add_angle(direction * self.speed)
            lidar.draw(maze=maze, game_display=game_display)
        self.check_bounds(maze=maze, game_display=game_display)

    def get_position(self):
        """get drone coordinates.

        :return: a coordinates of the drone.
        :rtype: tuple. (x_position, y_position)
        """
        return round(self.x_position), round(self.y_position)

    def check_bounds(self, maze, game_display):
        """check if the drone get to bounds.

        :param game_display: a screen object.
        :param maze: a background maze.
        :return: true if we reach the bounds (or wall).
        :rtype: boolean
        """
        for lidar in self.lidars:
            # check sensor.
            lidar_info = lidar.check_bounds(maze=maze)
            # if sensor find a bounds.
            if type(lidar_info) is tuple:
                # draw a bounds.
                self.draw_bounds(game_display=game_display, coordination=lidar_info)

        if maze.get_at((int(self.x_position), int(self.y_position))) == self.bounds_color:
            self.error_case += 1
        return False

    def draw(self, game_display):
        """draw drone over the screen.

        :param game_display: a pygame surface (screen).
        """
        pygame.draw.circle(game_display, self.color, self.get_position(), self.radius)

    def draw_bounds(self, game_display, coordination):
        """
        draw a bounds by the drone observation.
        :param coordination: a drone bounds observation, tuple.
        :param game_display: a main screen.
        :return:
        """
        pygame.draw.circle(game_display, self.bounds_color, coordination, 3)

    def change_lidars_positions(self, maze, game_display):
        """change lidars positions according to drone movements.

        change lidars positions and draw.
        :param game_display: a pygame surface (screen).
        :param maze: a background maze.
        """
        for lidar in self.lidars:
            lidar.move(coordinate=self.get_position())
            lidar.draw(maze=maze, game_display=game_display)

    def calc_x(self):
        """calculate the x end point of the drone.

        :return: the end points.
        :rtype: int
        """
        return cos(radians(self.yaw)) * self.radius

    def calc_y(self):
        """calculate the y end point of the drone.

        :return: the end points.
        :rtype: int
        """
        return sin(radians(self.yaw)) * self.radius

    def move(self, game_display, maze):
        """move the drone and the lidars.

        :param game_display: a pygame surface (screen).
        :param maze: a background maze.
        """
        self.x_position += self.speed * self.calc_x()
        self.y_position += self.speed * self.calc_y()
        # update odometer position.
        self.change_lidars_positions(maze=maze, game_display=game_display)
        self.is_crashed(maze=maze)

    def forward(self, acc=1.):
        """
        speed up the drone forward.
        """
        n_speed = self.speed + 0.2 * acc
        self.speed = n_speed if n_speed < 2 else 2

    def backward(self, acc=1.):
        """
        speed up the drone forward.
        """
        n_speed = self.speed - 0.2 * acc
        self.speed = n_speed if n_speed > 0 else 0.2

    def handle_keys(self, maze, game_display, key):
        """handle keys, move a drone by the pressed key.

        :return: true if the drone moves, otherwise false.
        :rtype: bool
        """
        if self.state == DroneState.LAND:
            self.state = DroneState.TAKE_OFF
        self.time_in_air -= 1 / 25 if self.time_in_air > 0 else self.time_in_air
        if self.time_in_air == 0:
            self.state = DroneState.LAND
            return False
        self.check_bounds(maze=maze, game_display=game_display)
        # if left key pressed, go left.
        if key[pygame.K_LEFT]:
            self.rotate(maze=maze, direction=-1, game_display=game_display)
            return True
        # if right key pressed, go right.
        if key[pygame.K_RIGHT]:
            self.rotate(maze=maze, direction=1, game_display=game_display)
            return True
        # if up key pressed,up go left
        if key[pygame.K_UP]:
            # update y position
            self.forward()
            self.move(maze=maze, game_display=game_display)
            return True
        # if down key pressed, go down.
        if key[pygame.K_DOWN]:
            self.backward()
            self.move(maze=maze, game_display=game_display)
            return True
        return False

    def is_crashed(self, maze):
        """if drone has crashed to wall.

        :param maze: a background maze.
        :return: true is a drone crashed to a wall.
        :rtype: bool
        """
        if maze.get_at(self.get_position()) == self.bounds_color:
            self.error_case += 1
            return True
        return False

    def get_info_dict(self):
        """get all drone info.

        :return: an info.
        :rtype: dict
        """
        return {
            'yaw': self.yaw,
            'speed': self.speed,
            'left': self.lidars[2],
            'right': self.lidars[1],
            'head': self.lidars[0],
            'crash': self.error_case,
            'score': self.score,
            'battery': str(timedelta(seconds=self.time_in_air)).split('.')[0]
        }
