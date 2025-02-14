from moderngl import Program


class VAO:
    def __init__(self, ctx):
        self.ctx = ctx

    def create_vao(self, vbo):
        return self.ctx.vertex_array(Program, [(vbo, '3f', 'in_position')])
