from .Element import Element
from .utils import futil, remove_html_tags

class Divider(Element):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._height = kwargs['Height'] 
        self._width = kwargs['Width'] 
        self._length = kwargs['Length']
        self._label_length = kwargs.get('LabelLength', 0)
        self._label_width = kwargs.get('LabelWidth', 0)
        self._label_offset = kwargs.get('LabelOffset', 0)
        self._label_left_right = kwargs.get('LabelLeftRight', True)
        self._label_fillet = kwargs.get('LabelFillet',0)
        self._text_height = kwargs.get('TextHeight', 0.06)
        self._label_text = kwargs.get('LabelText', '')
        self._label_text = remove_html_tags(self._label_text)
        if self._label_width > 0 and self._label_length > 0 and self._label_offset == 0:
            self._label_offset = 0.001

    def add_text_on_label_path(self, sketch, path, text, text_height = 0.4, font_family = 'Comic Sans MS'):
        # Assuming 'path' is the SketchLine or SketchCurve created earlier
        text_input = sketch.sketchTexts.createInput2(text, text_height)
        text_input.setAsFitOnPath(path, True)
        text_input.fontName = font_family
        sketch_text = sketch.sketchTexts.add(text_input)
        return sketch_text

    def create_sketch_text(self, sketch):
        has_label = self._label_length and self._label_width
        sketch_text = None
        if has_label and self._label_text != '':
            label_x = self._label_offset if self._label_left_right else self._width - self._label_offset - self._label_width
            label_y = self._length - self._label_length

            start_point = futil.core.Point3D.create(label_x + self._label_fillet / 3, label_y + self._label_length / 10, 0)
            end_point = futil.core.Point3D.create(label_x + self._label_width - self._label_fillet / 3, label_y + self._label_length / 10, 0)
            sketch_text = self.add_text_on_label_path(sketch, self.create_path(sketch, start_point, end_point), self._label_text)
        return sketch_text

    def create_sketch(self):
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

        has_label = self._label_length and self._label_width

        if has_label:
            label_x = self._label_offset if self._label_left_right else self._width - self._label_offset - self._label_width
            label_y = self._length - self._label_length
            if label_x > 0:
                # Create two subtractive rectangles at the top end within the same sketch
                rect_sub1 = lines.addTwoPointRectangle(
                    futil.core.Point3D.create(0, label_y, 0),
                    futil.core.Point3D.create(label_x, label_y + self._label_length, 0),
                )

            if self._width - self._label_width - label_x > 0:
                rect_sub2 = lines.addTwoPointRectangle(
                    futil.core.Point3D.create(label_x + self._label_width, label_y, 0),
                    futil.core.Point3D.create(self._width, label_y + self._label_length, 0),
                )

        return sketch

    def generate_fusion(self):
        product = futil.app.activeProduct
        design = futil.fusion.Design.cast(product)
        root_comp = design.rootComponent

        has_label = self._label_length and self._label_width
        sketch = self.create_sketch()

        # Select the profile that includes the main rectangle minus the subtractive rectangles
        # Assuming the desired profile is the first one, adjust if necessary
        if has_label:
            profile = sketch.profiles.item(1)
        else:
            profile = sketch.profiles.item(0)

        extrude = self.extrude(root_comp, profile, self._height)

        fillets = root_comp.features.filletFeatures
        fillet_input = fillets.createInput()
        edges_to_be_filleted = futil.core.ObjectCollection.create()

        # Iterate through the edges of the extruded body to find the top edges
        # Note: The logic to identify 'top edges' needs to be defined based on your model's specifics
        for edge in extrude.bodies.item(0).edges:
            is_top_edge = False  # Placeholder for your logic to determine if an edge is a 'top edge'                

            # Assuming 'edge' is an edge from the extruded body
            start_point = edge.startVertex.geometry
            end_point = edge.endVertex.geometry

            # Convert points to vectors
            start_vector = futil.core.Vector3D.create(start_point.x, start_point.y, start_point.z)
            end_vector = futil.core.Vector3D.create(end_point.x, end_point.y, end_point.z)

            vector = start_vector.copy()
            vector.scaleBy(-1.0)
            vector.add(end_vector)

            if vector.z == self._height and start_point.y == self._length:
                is_top_edge = True
            
            if is_top_edge:
                edges_to_be_filleted.add(edge)

        # If there are edges to fillet, add the fillet feature
        if self._label_fillet > 0 and edges_to_be_filleted.count > 0:
            fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(edges_to_be_filleted, futil.core.ValueInput.createByReal(self._label_fillet), True)
            fillet_feature = root_comp.features.filletFeatures.add(fillet_input)
        
        sketch_text = self.create_sketch_text(sketch)
        if sketch_text is not None:
            if self._text_height < 0:
                self.extrude(root_comp, sketch_text, self._height, futil.fusion.FeatureOperations.CutFeatureOperation)
                sketch_text = self.create_sketch_text(sketch)
            self.extrude(root_comp, sketch_text, self._text_height + self._height, futil.fusion.FeatureOperations.JoinFeatureOperation)
            
        return