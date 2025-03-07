import numpy as np

class Ground:
    def __init__(self, ctx, program):
        self.ctx = ctx
        self.program = program
        self.vbo, self.vao = self.create_ground()

    def create_ground(self):
        vertices = np.array([
            -10, 0, -10, 0, 1, 0,
            10, 0, -10, 0, 1, 0,
            10, 0, 10, 0, 1, 0,
            -10, 0, 10, 0, 1, 0
        ], dtype='f4')

        indices = np.array([
            0, 1, 2, 2, 3, 0
        ], dtype='i4')

        vbo = self.ctx.buffer(vertices)
        ebo = self.ctx.buffer(indices)
        vao = self.ctx.vertex_array(self.program, [(vbo, '3f 3f', 'in_position', 'in_normal')], ebo)
        return vbo, vao

    def render(self):
        self.vao.render()

class LetterA:
    def __init__(self, ctx, program):
        self.ctx = ctx
        self.program = program
        self.vbo, self.vao = self.create_letter_a()

    def create_letter_a(self):
        vertices = np.array([
            # Replace this with the actual letter 'A' vertex data
            -0.5, 0.0, 0.0,
            0.5, 0.0, 0.0,
            0.0, 1.0, 0.0,
        ], dtype='f4')

        vbo = self.ctx.buffer(vertices)
        vao = self.ctx.vertex_array(
            self.program,
            [(vbo, '3f', 'in_position')],
        )
        return vbo, vao

    def render(self):
        self.vao.render()
