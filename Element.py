import html
import re

try:
    from .lib import fusion360utils as futil
except:
    futil = None

def remove_html_tags(html_content):
    if html_content == '':
        return html_content

    # Unescape HTML entities
    unescaped_content = html.unescape(html_content)
    
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', unescaped_content)
    
    return clean_text

# Board game organizer element
class Element:
    def __init__(self, **kwargs):
        return

    def generate_fusion(self):
        return

    def create_path(self, sketch, startPoint, endPoint):
        lines = sketch.sketchCurves.sketchLines
        path = lines.addByTwoPoints(startPoint, endPoint)
        return path

    def add_text_on_label_path(self, sketch, path, text):
        # Assuming 'path' is the SketchLine or SketchCurve created earlier
        textHeight = 0.4  # Or another appropriate value based on the label size
        text_input = sketch.sketchTexts.createInput2(text, textHeight)
        text_input.setAsFitOnPath(path, True)
        text_input.fontName = 'Comic Sans MS'
        sketch_text = sketch.sketchTexts.add(text_input)
        return sketch_text
        
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

    def create_sketch_text(self, sketch):
        has_label = self._label_length and self._label_width and self._label_offset
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

        has_label = self._label_length and self._label_width and self._label_offset 

        if has_label:
            label_x = self._label_offset if self._label_left_right else self._width - self._label_offset - self._label_width
            label_y = self._length - self._label_length
            # Create two subtractive rectangles at the top end within the same sketch
            rect_sub1 = lines.addTwoPointRectangle(
                futil.core.Point3D.create(0, label_y, 0),
                futil.core.Point3D.create(label_x, label_y + self._label_length, 0),
            )

            rect_sub2 = lines.addTwoPointRectangle(
                futil.core.Point3D.create(label_x + self._label_width, label_y, 0),
                futil.core.Point3D.create(self._width, label_y + self._label_length, 0),
            )

        return sketch

    def generate_fusion(self):
        product = futil.app.activeProduct
        design = futil.fusion.Design.cast(product)
        root_comp = design.rootComponent

        has_label = self._label_length and self._label_width and self._label_offset
        sketch = self.create_sketch()

        # Select the profile that includes the main rectangle minus the subtractive rectangles
        # Assuming the desired profile is the first one, adjust if necessary
        if has_label:
            profile = sketch.profiles.item(1)
        else:
            profile = sketch.profiles.item(0)

        extrudes = root_comp.features.extrudeFeatures
        extrude_input = extrudes.createInput(profile, futil.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = futil.core.ValueInput.createByReal(self._height)
        extrude_input.setOneSideExtent(futil.fusion.DistanceExtentDefinition.create(distance), futil.fusion.ExtentDirections.PositiveExtentDirection)
        extrude = extrudes.add(extrude_input)

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
            text_extrude_input = extrudes.createInput(sketch_text, futil.fusion.FeatureOperations.JoinFeatureOperation)
            text_distance = futil.core.ValueInput.createByReal(self._text_height + self._height)  # Assuming _text_height is the extrusion height for the text
            text_extrude_input.setOneSideExtent(futil.fusion.DistanceExtentDefinition.create(text_distance), futil.fusion.ExtentDirections.PositiveExtentDirection)
            text_extrude = extrudes.add(text_extrude_input)

        return