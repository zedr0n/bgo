from .Element import Element
from .utils import futil

class Tray(Element):
    def __init__(self, **kwargs):
        #super().__init__(**kwargs)
        self._height = kwargs['Height'] 
        self._width = kwargs['Width'] 
        self._length = kwargs['Length']  
        self._wall_thickness = kwargs.get('WallThickness', 0.02)
        self._base_thickness = kwargs.get("BaseThickness", 0.02)
        self._cutout_ratio = kwargs.get("CutoutRatio", 0.0)

    def create_cutout(self, body, normal_vector):
        product = futil.app.activeProduct
        design = futil.fusion.Design.cast(product)
        root_comp = design.rootComponent
        
        if self._cutout_ratio == 0:
            return

        radius = normal_vector.length * self._cutout_ratio
        normal_vector.normalize()

        faces = self.find_faces_by_normal_and_position(body, normal_vector)        
        for face in faces:
            face = futil.fusion.BRepFace.cast(face)
            sketches = root_comp.sketches
            sketch = sketches.add(face)

            mid_point = face.centroid            
            center_point = futil.core.Point3D.create(mid_point.x, mid_point.y, self._height)
            center_point = sketch.modelToSketchSpace(center_point)
            sketch_point = sketch.sketchPoints.add(center_point)

            circles = sketch.sketchCurves.sketchCircles
            circle = circles.addByCenterRadius(sketch_point, radius)
            
            profile = sketch.profiles.item(0)
            self.extrude(root_comp, profile, -self._base_thickness, futil.fusion.FeatureOperations.CutFeatureOperation)


    def generate_fusion(self):
        product = futil.app.activeProduct
        design = futil.fusion.Design.cast(product)
        root_comp = design.rootComponent

        sketch = self.create_sketch()        
        outer_profile = sketch.profiles.item(1)
        inner_profile = sketch.profiles.item(0)

        base_body = self.extrude(root_comp, outer_profile, self._base_thickness)
        wall_body = self.extrude(root_comp, inner_profile, self._height, futil.fusion.FeatureOperations.JoinFeatureOperation)

        # modify tray with cutout
        self.create_cutout(base_body, futil.core.Vector3D.create(0, self._width, 0))
        self.create_cutout(base_body, futil.core.Vector3D.create(self._length, 0, 0))

    def create_sketch(self):
        #return super().create_sketch()
        product = futil.app.activeProduct
        design = futil.fusion.Design.cast(product)
        root_comp = design.rootComponent

        # create a new sketch on XY plane
        sketches = root_comp.sketches
        xy_plane = root_comp.xYConstructionPlane
        sketch = sketches.add(xy_plane)

        # create 2d rectangle
        lines = sketch.sketchCurves.sketchLines
        rect = lines.addTwoPointRectangle(
            futil.core.Point3D.create(0,0,0),
            futil.core.Point3D.create(self._width,self._length,0),                                              
        )

        rect_sub_walls = lines.addTwoPointRectangle(
            futil.core.Point3D.create(self._wall_thickness, self._wall_thickness, 0),
            futil.core.Point3D.create(self._width - self._wall_thickness,self._length - self._wall_thickness, 0)
        )

        return sketch
        