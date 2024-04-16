from .utils import futil

# Board game organizer element
class Element:
    def __init__(self, **kwargs):
        return

    def generate_fusion(self):
        return
    
    def create_sketch(self):
        return None    

    def create_path(self, sketch, start_point, end_point):
        lines = sketch.sketchCurves.sketchLines
        path = lines.addByTwoPoints(start_point, end_point)
        return path
    
    def extrude(self, root_comp, object, height, operation = futil.fusion.FeatureOperations.NewBodyFeatureOperation):
        extrudes = root_comp.features.extrudeFeatures
        extrude_input = extrudes.createInput(object, operation)
        distance = futil.core.ValueInput.createByReal(height)
        extrude_input.setOneSideExtent(futil.fusion.DistanceExtentDefinition.create(distance), futil.fusion.ExtentDirections.PositiveExtentDirection)
        extrude = extrudes.add(extrude_input)

        if extrude.bodies.count > 0:
            return extrude.bodies.item(0)  # Return the first body created by this extrusion
        return None        
    
    def find_faces_by_normal_and_position(self,component, normal_vector, position_criteria = lambda x : True):
        faces = []
        for face in component.faces:
            geometry = face.geometry
            if hasattr(geometry, 'normal'):
                normal = geometry.normal
                if normal.isEqualTo(normal_vector) and position_criteria(face):
                    faces.append(face)
        return faces
    
    # Example criteria function to find the bottom face
    def is_bottom_face(self, face):
        # Assuming Z is up, check if the center point Z value is minimal
        return face.centroid.z < 0.01  # adjust tolerance as needed    
    
    def is_side_face(self, face):
        return face.centroid.z > 0.01