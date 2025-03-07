from skybox import SkyBox
from vbo import Ground, LetterA

class Scene:
    def __init__(self, app):
        self.app = app
        self.objects = []
        self.skybox = SkyBox(app)

        # Initialize ground and letter
        self.ground = Ground(app.ctx, app.shader_programs['default'])
        self.letter_a = LetterA(app.ctx, app.shader_programs['default'])

    def render(self):
        self.skybox.render()
        self.ground.render()
        self.letter_a.render()

    def resize(self, width, height):
        self.skybox.resize(width, height)
