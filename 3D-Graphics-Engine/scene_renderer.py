class SceneRenderer:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.mesh = app.mesh
        self.scene = app.scene

        # Prepare depth texture for shadow mapping
        self.depth_texture = self.mesh.texture.textures['depth_texture']
        self.depth_fbo = self.ctx.framebuffer(depth_attachment=self.depth_texture)

    def render_shadow(self):
        """Render shadows by capturing depth information."""
        self.depth_fbo.clear()
        self.depth_fbo.use()
        for obj in self.scene.objects:
            if hasattr(obj, 'render_shadow'):
                obj.render_shadow()

    def main_render(self):
        """Perform the main render pass with all objects and the skybox."""
        self.app.ctx.screen.use()
        self.ctx.clear(color=(0.08, 0.16, 0.18), depth=True)  # Clear screen
        for obj in self.scene.objects:
            if hasattr(obj, 'render'):
                obj.render()
        self.scene.skybox.render()  # Render the skybox last

    def render(self):
        """Render the scene: shadows first, then the main render pass."""
        self.scene.update()  # Update animations or transformations
        self.render_shadow()  # Pass 1: Render shadows
        self.main_render()    # Pass 2: Render scene with lighting and textures

    def destroy(self):
        """Release resources used by the renderer."""
        self.depth_fbo.release()
