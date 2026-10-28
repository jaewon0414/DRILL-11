from pico2d import load_image, get_time, get_canvas_width, clamp
from pico2d import SDL_KEYDOWN, SDL_KEYUP, SDLK_SPACE, SDLK_LEFT, SDLK_RIGHT, SDLK_a
from transitions import Machine


# 상태 클래스: enter 는 들어갈 때, exit 는 나갈 때 한 번, do 는 머무는 동안 매 프레임, draw 는 그리기
class Idle:
    def __init__(self, boy):
        self.boy = boy
        self.start_time = 0

    def enter(self):
        # IDLE 에 들어올 때마다 5초 타이머를 다시 시작한다.
        self.start_time = get_time()

    def exit(self):
        pass

    def do(self):
        boy = self.boy
        boy.frame = (boy.frame + 1) % 8
        if get_time() - self.start_time > 5:
            boy.time_out()

    def draw(self):
        boy = self.boy
        # animation_sheet.png 의 IDLE 줄: 오른쪽을 볼 때 bottom 300, 왼쪽을 볼 때 bottom 200
        if boy.face_dir == 1:
            boy.image.clip_draw(boy.frame * 100, 300, 100, 100, boy.x, boy.y)
        else:
            boy.image.clip_draw(boy.frame * 100, 200, 100, 100, boy.x, boy.y)


class Sleep:
    def __init__(self, boy):
        self.boy = boy

    def enter(self):
        pass

    def exit(self):
        pass

    def do(self):
        boy = self.boy
        boy.frame = (boy.frame + 1) % 8

    def draw(self):
        boy = self.boy
        # IDLE 그림을 90도 돌려 눕힌다. 눕히면 몸이 떠 보이므로 땅 쪽으로 25 내려서 그린다.
        if boy.face_dir == 1:
            boy.image.clip_composite_draw(boy.frame * 100, 300, 100, 100,
                                          3.141592 / 2, '', boy.x, boy.y - 25, 100, 100)
        else:
            boy.image.clip_composite_draw(boy.frame * 100, 200, 100, 100,
                                          -3.141592 / 2, '', boy.x, boy.y - 25, 100, 100)


class Run:
    def __init__(self, boy):
        self.boy = boy

    def enter(self):
        pass

    def exit(self):
        pass

    def do(self):
        boy = self.boy
        boy.frame = (boy.frame + 1) % 8
        boy.face_dir = boy.dir
        boy.x += boy.dir * 5
        # 그림 한 칸(100x100)의 절반인 50 만큼 안쪽까지만 가면 서 있든 달리든 누워 있든 화면 안에 다 보인다.
        boy.x = clamp(50, boy.x, get_canvas_width() - 50)

    def draw(self):
        boy = self.boy
        # animation_sheet.png 의 RUN 줄: 오른쪽으로 달릴 때 bottom 100, 왼쪽으로 달릴 때 bottom 0
        if boy.face_dir == 1:
            boy.image.clip_draw(boy.frame * 100, 100, 100, 100, boy.x, boy.y)
        else:
            boy.image.clip_draw(boy.frame * 100, 0, 100, 100, boy.x, boy.y)


# 자동 무적 런: 키를 누르지 않아도 계속 달린다.
class AutoRun:
    SPEED = 10  # 프레임당 이동 픽셀. RUN(5)의 두 배
    SCALE = 2   # 그림 확대 배율. 100x100 칸을 200x200 으로 그린다

    def __init__(self, boy):
        self.boy = boy
        # 소년의 dir 은 눌린 방향키로 계산되어 키를 떼면 0 이 되므로, 자동 런은 자기 방향을 따로 가진다.
        self.dir = 1
        self.start_time = 0

    def enter(self):
        # 들어가는 순간 바라보던 방향으로 출발하고, 5초 타이머를 시작한다.
        self.dir = self.boy.face_dir
        self.start_time = get_time()

    def exit(self):
        pass

    def do(self):
        boy = self.boy
        boy.frame = (boy.frame + 1) % 8
        # 바깥쪽으로 가다가 경계에 닿으면 돌아선다. 위치는 고치지 않아서 끝에서 시작해도 순간 이동이 없다.
        # 경계 여백은 커진 그림 칸의 절반이다.
        margin = 50 * AutoRun.SCALE
        left, right = margin, get_canvas_width() - margin
        if (self.dir == 1 and boy.x >= right) or (self.dir == -1 and boy.x <= left):
            self.dir = -self.dir
        boy.face_dir = self.dir
        boy.x += self.dir * AutoRun.SPEED
        if get_time() - self.start_time >= 5:
            boy.time_out()

    def draw(self):
        boy = self.boy
        size = 100 * AutoRun.SCALE
        # 그림은 중심 기준으로 커지므로 발끝(칸 중심 아래 37)이 땅에 남도록 그리는 y 만 올린다.
        y = boy.y + 37 * (AutoRun.SCALE - 1)
        if boy.face_dir == 1:
            boy.image.clip_draw(boy.frame * 100, 100, 100, 100, boy.x, y, size, size)
        else:
            boy.image.clip_draw(boy.frame * 100, 0, 100, 100, boy.x, y, size, size)


class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.image = load_image('animation_sheet.png')

        # 방향키가 눌려 있는지 기억해 두고, 달릴 방향(dir)을 계산한다. 오른쪽 1, 왼쪽 -1, 멈춤 0.
        self.left_pressed = False
        self.right_pressed = False
        self.dir = 0

        # 상태 이름 -> 그 상태를 맡는 상태 객체
        self.state_objects = {
            'IDLE': Idle(self),
            'SLEEP': Sleep(self),
            'RUN': Run(self),
            'AUTO_RUN': AutoRun(self),
        }

        # IDLE --(5초 경과: time_out)--> SLEEP
        # SLEEP --(SPACE 누름: space_down)--> IDLE
        # IDLE, SLEEP, AUTO_RUN --(방향키 누름: dir_down)--> RUN
        # RUN --(방향키 모두 뗌: dir_up)--> IDLE
        # IDLE --(a 키 누름: a_down)--> AUTO_RUN
        # AUTO_RUN --(5초 경과: time_out)--> IDLE
        # 상태가 바뀔 때마다 Machine 이 나가는 상태 객체의 exit 와 들어가는 상태 객체의 enter 를 불러 준다.
        # ignore_invalid_triggers: IDLE 에서 SPACE 처럼 현재 상태에 없는 이벤트는 무시한다.
        self.machine = Machine(
            model=self,
            states=[{'name': name, 'on_enter': obj.enter, 'on_exit': obj.exit}
                    for name, obj in self.state_objects.items()],
            transitions=[
                {'trigger': 'time_out', 'source': 'IDLE', 'dest': 'SLEEP'},
                {'trigger': 'space_down', 'source': 'SLEEP', 'dest': 'IDLE'},
                {'trigger': 'dir_down', 'source': ['IDLE', 'SLEEP', 'AUTO_RUN'], 'dest': 'RUN'},
                {'trigger': 'dir_up', 'source': 'RUN', 'dest': 'IDLE'},
                {'trigger': 'a_down', 'source': 'IDLE', 'dest': 'AUTO_RUN'},
                {'trigger': 'time_out', 'source': 'AUTO_RUN', 'dest': 'IDLE'},
            ],
            initial='IDLE',
            auto_transitions=False,
            ignore_invalid_triggers=True,
        )

        # 처음 시작 상태로 놓일 때는 Machine 이 enter 를 부르지 않으므로 직접 부른다.
        self.state_objects['IDLE'].enter()

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
            self.space_down()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_a:
            self.a_down()
        elif event.type in (SDL_KEYDOWN, SDL_KEYUP) and event.key in (SDLK_LEFT, SDLK_RIGHT):
            pressed = event.type == SDL_KEYDOWN
            if event.key == SDLK_LEFT:
                self.left_pressed = pressed
            else:
                self.right_pressed = pressed
            self.dir = int(self.right_pressed) - int(self.left_pressed)

            # 왼쪽/오른쪽 모두 같은 이벤트로 처리한다. 방향은 self.dir 이 들고 있다.
            if self.dir != 0:
                self.dir_down()
            else:
                self.dir_up()

    def update(self):
        self.state_objects[self.state].do()

    def draw(self):
        self.state_objects[self.state].draw()
