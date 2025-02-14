import numpy as np

class Ground:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.program = app.load_program(vertex_shader='shaders/default.vert', fragment_shader='shaders/default.frag')
        self.vbo, self.vao = self.create_ground()

    def create_ground(self):
        vertices = np.array([
            -10, 0, -10, 0, 1, 0,
            10, 0, -10, 0, 1, 0,
            10, 0, 10, 0, 1, 0,
            -10, 0, 10, 0, 1, 0
        ], dtype='f4')

        indices = np.array([0, 1, 2, 2, 3, 0], dtype='i4')

        vbo = self.ctx.buffer(vertices)
        ebo = self.ctx.buffer(indices)
        vao = self.ctx.vertex_array(self.program, [(vbo, '3f 3f', 'in_position', 'in_normal')], ebo)
        return vbo, vao

    def render(self):
        self.vao.render()
